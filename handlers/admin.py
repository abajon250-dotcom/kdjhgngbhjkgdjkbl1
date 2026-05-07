import sqlite3
from aiogram import Router, types
from config import ADMIN_ID, DB_NAME   # DB_NAME добавлен
from database import get_all_users, get_token, revoke_token
from keyboards import admin_panel_keyboard, user_list_keyboard, user_actions_keyboard


router = Router()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

@router.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    await callback.message.edit_text("🛠 Админ-панель:", reply_markup=admin_panel_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    users = get_all_users()
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM auth_logs")
        logs_count = cur.fetchone()[0]
    text = f"📊 Статистика\n👥 Пользователей: {len(users)}\n📝 Логов: {logs_count}"
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    users = get_all_users()
    if not users:
        await callback.message.edit_text("Нет пользователей.", reply_markup=admin_panel_keyboard())
        await callback.answer()
        return
    await callback.message.edit_text("👥 Список пользователей:", reply_markup=user_list_keyboard(users, 0))
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("users_page_"))
async def users_page(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    page = int(callback.data.split("_")[-1])
    users = get_all_users()
    await callback.message.edit_reply_markup(reply_markup=user_list_keyboard(users, page))
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("user_"))
async def user_detail(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(f"👤 Пользователь ID: `{user_id}`", reply_markup=user_actions_keyboard(user_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("view_token_"))
async def view_token_admin(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    token = get_token(user_id)
    await callback.message.answer(f"Токен {user_id}:\n`{token}`" if token else "Токен отсутствует", parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("del_user_"))
async def delete_user_admin(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    revoke_token(user_id)
    await callback.message.answer(f"Пользователь {user_id} удалён.")
    users = get_all_users()
    if users:
        await callback.message.edit_text("Список обновлён:", reply_markup=user_list_keyboard(users, 0))
    else:
        await callback.message.edit_text("Пользователей нет.", reply_markup=admin_panel_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    from keyboards import main_menu_keyboard
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()