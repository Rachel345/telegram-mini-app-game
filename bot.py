import asyncio
import json
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from database import add_user, get_user_stats, update_user_stats

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- СЕРВЕРНА ЧАСТИНА (API ДЛЯ ГРИ) ---

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
    # ВИПРАВЛЕНО: Додано обробку OPTIONS для цього маршруту
    if request.method == 'OPTIONS':
        return web.Response(headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, ngrok-skip-browser-warning',
        })

    try:
        user_id = int(request.query.get("user_id", 0))
        stats = get_user_stats(user_id)
        stars = stats.get('stars', 0) if stats else 0
        return web.json_response({"stars": stars}, headers={
            'Access-Control-Allow-Origin': '*',
            'ngrok-skip-browser-warning': 'true'
        })
    except Exception as e:
        return web.json_response({"stars": 0}, headers={'Access-Control-Allow-Origin': '*'})

app = web.Application()
# Дозволяємо всі методи для обох шляхів
app.router.add_route('*', '/update_stars', handle_update_stars)
app.router.add_route('*', '/get_stars', handle_get_stars)

# --- ЛОГІКА БОТА ---

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or "Кріптограф"

    # Перевіряємо/додаємо користувача
    stats = get_user_stats(user_id)
    if not stats:
        add_user(user_id, username)
        stars = 0
    else:
        stars = stats.get('stars', 0)

    # Посилання на вашу гру (GitHub Pages)
    web_app_url = f"https://rachel345.github.io/telegram-mini-app-game/index.html?user_id={user_id}&stars={stars}"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 ЗАПУСТИТИ ТРЕНАЖЕР", web_app=WebAppInfo(url=web_app_url))]
    ])

    await message.answer(
        f"Вітаю, {username}!\nВаш поточний баланс: {stars} ⭐\n\nГотові до дешифрування?",
        reply_markup=markup
    )

async def main():
    # Запуск бота
    bot_task = asyncio.create_task(dp.start_polling(bot))
    
    # Запуск сервера на порту 8080
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    
    logger.info("🚀 БОТ ТА API ЗАПУЩЕНІ (Порт 8080)")
    await site.start()
    await bot_task

if __name__ == "__main__":
    asyncio.run(main())
