import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from aiohttp import web
from database import add_user, get_user_stats, update_user_stats

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація бота
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- БЛОК API СЕРВЕРА (ДЛЯ MINI APP) ---

async def handle_update_stars(request):
    """Отримує зірки від гри та зберігає в БД"""
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

        if user_id is None or stars_to_add is None:
            return web.json_response({"status": "error"}, status=400)

        update_user_stats(user_id, stars_to_add)
        logger.info(f"✅ Додано {stars_to_add} зірок користувачу {user_id}")
        
        return web.json_response({"status": "ok"}, headers={'Access-Control-Allow-Origin': '*'})
    except Exception as e:
        logger.error(f"❌ Помилка API: {e}")
        return web.json_response({"status": "error"}, status=500)

async def handle_get_stars(request):
    """Повертає баланс зірок для Mini App"""
    try:
        user_id = int(request.query.get("user_id"))
        stats = get_user_stats(user_id)
        stars = stats.get('stars', 0) if stats else 0
        return web.json_response({"stars": stars}, headers={'Access-Control-Allow-Origin': '*'})
    except:
        return web.json_response({"stars": 0}, headers={'Access-Control-Allow-Origin': '*'})

# Налаштування веб-додатка aiohttp
app = web.Application()
app.router.add_post('/update_stars', handle_update_stars)
app.router.add_get('/get_stars', handle_get_stars)
app.router.add_options('/update_stars', handle_update_stars)

# --- ЛОГІКА ТЕЛЕГРАМ БОТА ---

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or "Гравець"

    # Реєстрація користувача, якщо його немає
    stats = get_user_stats(user_id)
    if not stats:
        add_user(user_id, username)
        stars = 0
    else:
        stars = stats.get('stars', 0)

    # URL вашого Mini App на GitHub Pages
    web_app_url = f"https://rachel345.github.io/telegram-mini-app-game/index.html?user_id={user_id}&stars={stars}&v={os.urandom(4).hex()}"
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 ЗАПУСТИТИ КРІПТО-КОНСОЛЬ", web_app=WebAppInfo(url=web_app_url))]
        ]
    )

    await message.answer(
        f"📟 **ВІТАЮ В СИСТЕМІ, {username.upper()}**\n\n"
        f"Твій поточний рівень доступу: **{stars} ⭐**\n"
        "Натисни кнопку нижче, щоб увійти в термінал.",
        reply_markup=inline_kb,
        parse_mode="Markdown"
    )

async def main():
    # Запуск бота
    bot_task = asyncio.create_task(dp.start_polling(bot))
    
    # Запуск API сервера
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    print("🚀 БОТ ТА API ЗАПУЩЕНІ (Порт 8080)")
    await bot_task

if __name__ == "__main__":
    asyncio.run(main())
