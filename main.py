import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import start, auth, token_actions, admin

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем все роутеры
    dp.include_router(start.router)
    dp.include_router(auth.router)
    dp.include_router(token_actions.router)
    dp.include_router(admin.router)

    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())