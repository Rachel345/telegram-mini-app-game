import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart

from database import add_user, get_user_stats

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота з API токеном
API_TOKEN = '8290033163:AAH11alj0hWFsRkycOZ1hA5vybom0JH44dA'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Обробник команди /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or ""

    if not get_user_stats(user_id):
        add_user(user_id, username)

    web_app_url = f"https://rachel345.github.io/telegram-mini-app-game/index.html?user_id={user_id}"
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити Mini App",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ]
        ]
    )

    await message.answer(
        "Вітаю! Натисни кнопку нижче, щоб відкрити Telegram Mini App.",
        reply_markup=inline_kb,
    )


# Функція для запуску бота
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
