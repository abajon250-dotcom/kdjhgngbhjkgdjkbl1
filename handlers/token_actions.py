from aiogram import Router, types
from database import get_token, revoke_token

router = Router()

@router.callback_query(lambda c: c.data == "get_my_token")
async def get_my_token(callback: types.CallbackQuery):
    token = get_token(callback.from_user.id)
    if token:
        await callback.message.answer(f"Ваш токен:\n`{token}`", parse_mode="Markdown")
    else:
        await callback.message.answer("У вас нет токена. Нажмите «Авторизация VK».")
    await callback.answer()

@router.callback_query(lambda c: c.data == "revoke_my_token")
async def revoke_my_token(callback: types.CallbackQuery):
    revoke_token(callback.from_user.id)
    await callback.message.answer("Ваш токен удалён.")
    await callback.answer()