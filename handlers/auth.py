import asyncio
from io import BytesIO
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile
from states import AuthStates
from vk_client import request_code, submit_code, login_with_password, create_vk_session
from database import save_token, log_auth
from keyboards import main_menu_keyboard, auth_method_keyboard
from utils import download_captcha


router = Router()

# ---- Начало авторизации - выбор метода ----
@router.callback_query(lambda c: c.data == "auth_start")
async def start_auth(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите способ авторизации:",
        reply_markup=auth_method_keyboard()
    )
    await state.set_state(AuthStates.waiting_method)
    await callback.answer()

@router.callback_query(lambda c: c.data == "method_code")
async def auth_method_code(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите номер телефона в международном формате, например:\n`+79001234567`",
        parse_mode="Markdown"
    )
    await state.update_data(method="code")
    await state.set_state(AuthStates.waiting_phone)
    await callback.answer()

@router.callback_query(lambda c: c.data == "method_password")
async def auth_method_password(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите номер телефона в международном формате:\n`+79001234567`\n\n"
        "Следующим сообщением отправьте ПАРОЛЬ (он не сохраняется).",
        parse_mode="Markdown"
    )
    await state.update_data(method="password")
    await state.set_state(AuthStates.waiting_phone)
    await callback.answer()

# ---- Ввод номера (общий для обоих методов) ----
@router.message(AuthStates.waiting_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not (phone.startswith('+') and phone[1:].isdigit()):
        await message.answer("Неверный формат. Пример: `+79001234567`", parse_mode="Markdown")
        return

    data = await state.get_data()
    method = data.get("method")
    await state.update_data(phone=phone)

    if method == "code":
        # Запрос SMS-кода
        await message.answer("Запрашиваю код...")
        success, vk, result, _ = await asyncio.to_thread(request_code, phone)
        if not success:
            if isinstance(result, dict) and "sid" in result:
                img_bytes = await download_captcha(result["img_url"])
                if img_bytes:
                    await message.answer_photo(InputFile(BytesIO(img_bytes), filename="captcha.jpg"),
                                               caption="🔐 Введите текст капчи:")
                    await state.update_data(captcha_sid=result["sid"], vk_session=vk)
                    await state.set_state(AuthStates.waiting_captcha)
                    log_auth(message.from_user.id, phone, "captcha_requested")
                else:
                    await message.answer("Не удалось загрузить капчу. /start")
                    await state.clear()
            else:
                await message.answer(f"Ошибка: {result}. /start")
                await state.clear()
            return
        await state.update_data(vk_session=vk)
        await state.set_state(AuthStates.waiting_code)
        await message.answer("Код подтверждения отправлен. Введите его:")
        log_auth(message.from_user.id, phone, "code_sent")

    elif method == "password":
        await message.answer("Теперь введите пароль от страницы ВКонтакте (не будет сохранён):")
        await state.set_state(AuthStates.waiting_password)

# ---- Ввод пароля ----
@router.message(AuthStates.waiting_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    phone = data.get("phone")

    await message.answer("Выполняю вход...")
    success, token, error = await asyncio.to_thread(login_with_password, phone, password)

    if success:
        save_token(message.from_user.id, token)
        await message.answer(
            f"✅ Успех!\n\nВаш access token:\n`{token}`\n\n"
            "Токен сохранён.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        log_auth(message.from_user.id, phone, "password_success")
        await state.clear()
    else:
        if error.startswith("captcha_needed:"):
            parts = error.split(":", 2)
            if len(parts) >= 3:
                captcha_sid = parts[1]
                captcha_img = parts[2]
                img_bytes = await download_captcha(captcha_img)
                if img_bytes:
                    await message.answer_photo(InputFile(BytesIO(img_bytes), filename="captcha.jpg"),
                                               caption="🔐 Требуется капча. Введите текст с картинки:")
                    await state.update_data(captcha_sid=captcha_sid, password=password)
                    await state.set_state(AuthStates.waiting_captcha)
                else:
                    await message.answer("Не удалось загрузить капчу. /start")
                    await state.clear()
            else:
                await message.answer(f"Ошибка капчи: {error}. /start")
                await state.clear()
        else:
            await message.answer(f"❌ Ошибка входа: {error}\nПопробуйте /start")
            await state.clear()

# ---- Ввод SMS-кода (для метода code) ----
@router.message(AuthStates.waiting_code)
async def process_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    if not code.isdigit():
        await message.answer("Код только из цифр. Попробуйте ещё.")
        return

    data = await state.get_data()
    vk = data.get("vk_session")
    if not vk:
        await message.answer("Сессия утеряна. /start")
        await state.clear()
        return

    await message.answer("Проверяю код...")
    success, token, error = await asyncio.to_thread(submit_code, vk, code)

    if success:
        save_token(message.from_user.id, token)
        await message.answer(
            f"✅ Успех!\n\nВаш access token:\n`{token}`\n\n"
            "Токен сохранён.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        log_auth(message.from_user.id, data.get("phone"), "code_success")
        await state.clear()
    else:
        if isinstance(error, dict) and "sid" in error:
            img_bytes = await download_captcha(error["img_url"])
            if img_bytes:
                await message.answer_photo(InputFile(BytesIO(img_bytes), filename="captcha.jpg"),
                                           caption="🔐 Требуется капча. Введите текст:")
                await state.update_data(captcha_sid=error["sid"], vk_session=vk, phone=data.get("phone"))
                await state.set_state(AuthStates.waiting_captcha)
            else:
                await message.answer("Не удалось загрузить капчу. /start")
                await state.clear()
        else:
            await message.answer(f"❌ {error}\nПовторите ввод кода или /start")

# ---- Обработка капчи (общая для всех методов) ----
@router.message(AuthStates.waiting_captcha)
async def process_captcha(message: types.Message, state: FSMContext):
    captcha_key = message.text.strip()
    data = await state.get_data()
    phone = data.get("phone")
    vk = data.get("vk_session")
    captcha_sid = data.get("captcha_sid")
    password = data.get("password")  # для метода password

    if not phone:
        await message.answer("Ошибка данных. /start")
        await state.clear()
        return

    # Определяем, какой метод использовался
    if password:
        # вход по паролю
        success, token, error = await asyncio.to_thread(login_with_password, phone, password, captcha_sid, captcha_key)
        if success:
            save_token(message.from_user.id, token)
            await message.answer(f"✅ Успех!\nТокен: `{token}`", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            log_auth(message.from_user.id, phone, "password_success_with_captcha")
            await state.clear()
        else:
            await message.answer(f"❌ Ошибка: {error}. /start")
            await state.clear()
    elif vk:
        # вход по коду
        await message.answer("Повторяю вход с капчей...")

        def retry_with_captcha():
            new_vk = create_vk_session(phone)
            try:
                new_vk.auth(captcha_sid=captcha_sid, captcha_key=captcha_key)
                return "need_code", new_vk
            except Exception as e:
                if hasattr(e, 'captcha_sid'):
                    return "captcha_again", None
                if hasattr(e, 'need_validation') and e.need_validation:
                    return "need_code", new_vk
                error_str = str(e).lower()
                if "validation" in error_str or "code" in error_str:
                    return "need_code", new_vk
                return f"error: {e}", None

        result, new_vk = await asyncio.to_thread(retry_with_captcha)
        if result == "need_code":
            await state.update_data(vk_session=new_vk, captcha_sid=None)
            await state.set_state(AuthStates.waiting_code)
            await message.answer("Капча принята. Код отправлен повторно. Введите код:")
            log_auth(message.from_user.id, phone, "captcha_solved")
        elif result == "captcha_again":
            await message.answer("❌ Неверный текст капчи. Попробуйте ещё раз:")
        elif result.startswith("error"):
            await message.answer(f"Ошибка: {result}. /start")
            await state.clear()
        else:
            await message.answer("Неожиданный ответ VK. /start")
            await state.clear()
    else:
        await message.answer("Непонятная ситуация. /start")
        await state.clear()