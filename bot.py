import asyncio
import json
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
# ДОДАНО: KeyboardButton та ReplyKeyboardMarkup
from aiogram.types import (
    Message, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    WebAppInfo, 
    KeyboardButton, 
    ReplyKeyboardMarkup
)
from database import add_user, get_user_stats, update_user_stats

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- СЕРВЕРНА ЧАСТИНА (API ДЛЯ ГРИ) ---
# (Залишаємо без змін, як у тебе в коді)
async def handle_update_stars(request):
    if request.method == 'OPTIONS':
        return web.Response(headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, ngrok-skip-browser-warning',
        })
    try:
        data = await request.json()
        user_id = data.get("user_id")
        stars_to_add = data.get("stars")
        if user_id and stars_to_add is not None:
            update_user_stats(user_id, stars_to_add)
            logger.info(f"✅ Додано {stars_to_add} зірок користувачу {user_id}")
            return web.json_response({"status": "ok"}, headers={'Access-Control-Allow-Origin': '*'})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, headers={'Access-Control-Allow-Origin': '*'})

async def handle_get_stars(request):
    if request.method == 'OPTIONS':
        return web.Response(headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, ngrok-skip-browser-warning'})
    try:
        user_id = int(request.query.get("user_id", 0))
        stats = get_user_stats(user_id)
        stars = stats.get('stars', 0) if stats else 0
        return web.json_response({"stars": stars}, headers={'Access-Control-Allow-Origin': '*', 'ngrok-skip-browser-warning': 'true'})
    except Exception as e:
        return web.json_response({"stars": 0}, headers={'Access-Control-Allow-Origin': '*'})

app = web.Application()
app.router.add_route('*', '/update_stars', handle_update_stars)
app.router.add_route('*', '/get_stars', handle_get_stars)

# --- ЛОГІКА БОТА ---

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or "Агент"
    
    stats = get_user_stats(user_id)
    if not stats:
        add_user(user_id, username)
        stars = 0
    else:
        stars = stats.get('stars', 0)

    # ТВОЄ ПОСИЛАННЯ ТУТ
    web_app_url = f"https://rachel345.github.io/telegram-mini-app-game/index.html?user_id={user_id}&stars={stars}"

    # СТВОРЕННЯ REPLY-КЛАВІАТУРИ (НИЖНЯ ПАНЕЛЬ)
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 ЗАПУСТИТИ ТРЕНАЖЕР", web_app=WebAppInfo(url=web_app_url))],
            [KeyboardButton(text="🆘 ПІДТРИМКА")]
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Оберіть дію в меню 👇"
    )

    welcome_text = "Вітаю у Крипто-тренажері! 🕵️‍♂️ Обирай дію в меню 👇"

    await message.answer(welcome_text, reply_markup=main_menu)

# ОБРОБНИК ДЛЯ КНОПКИ ПІДТРИМКА
@dp.message(F.text == "🆘 ПІДТРИМКА")
async def support_handler(message: Message):
    await message.answer(
        "Маєте питання? Напишіть розробнику: https://t.me/ra4elll",
        disable_web_page_preview=True
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🆘 **Допомога та підтримка**\n\n"
        "Вітаю у Крипто-тренажері! Ось як тут усе працює:\n\n"
        "• Тисни /start, щоб отримати посилання на гру.\n"
        "• У грі обирай рівень складності та розгадуй шифри.\n"
        "• Теорію можна знайти у розділі **КРИПТО-АКАДЕМІЯ**.\n\n"
        "Якщо гра не відкривається або ти знайшов баг — пиши розробнику!"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Написати розробнику", url="https://t.me/ra4elll")]
    ])
    await message.answer(help_text, reply_markup=markup, parse_mode="Markdown")

@dp.message(F.photo | F.video | F.voice | F.audio | F.document | F.sticker)
async def block_media(message: Message):
    await message.answer(
        "Вибачте, я приймаю тільки текстові відповіді для розшифрування. "
        "Скористайтеся клавіатурою або введіть текст."
    )

async def main():
    bot_task = asyncio.create_task(dp.start_polling(bot))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    logger.info("🚀 БОТ ТА API ЗАПУЩЕНІ (Порт 8080)")
    await site.start()
    await bot_task

if __name__ == "__main__":
    asyncio.run(main())
