from typing import List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Авторизация VK", callback_data="auth_start")],
        [InlineKeyboardButton(text="📋 Мой токен", callback_data="get_my_token")],
        [InlineKeyboardButton(text="🗑 Удалить токен", callback_data="revoke_my_token")],
        [InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")]
    ])

def auth_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 По номеру + SMS-код", callback_data="method_code")],
        [InlineKeyboardButton(text="🔐 По номеру + пароль", callback_data="method_password")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])

def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])

def user_list_keyboard(users: List[Tuple[int, str]], page: int = 0) -> InlineKeyboardMarkup:
    from math import ceil
    per_page = 5
    pages = ceil(len(users) / per_page)
    start = page * per_page
    end = start + per_page
    kb = []
    for user_id, token in users[start:end]:
        short_token = token[:10] + "..." if len(token) > 10 else token
        kb.append([InlineKeyboardButton(text=f"👤 {user_id} ({short_token})", callback_data=f"user_{user_id}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀ Назад", callback_data=f"users_page_{page-1}"))
    if page < pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶", callback_data=f"users_page_{page+1}"))
    if nav_buttons:
        kb.append(nav_buttons)
    kb.append([InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def user_actions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Посмотреть токен", callback_data=f"view_token_{user_id}")],
        [InlineKeyboardButton(text="❌ Удалить пользователя", callback_data=f"del_user_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_users")]
    ])