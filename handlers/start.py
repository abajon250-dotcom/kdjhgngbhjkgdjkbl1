from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_menu_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать!\n\n"
        "Я помогу получить access_token ВКонтакте по номеру телефона.\n"
        "Используйте кнопки ниже.",
        reply_markup=main_menu_keyboard()
    )