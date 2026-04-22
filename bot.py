import asyncio
import json
import logging
import os
import random
from typing import Callable, TypedDict
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
# Додаємо імпорт для сервера
from aiohttp import web

# Імпортуємо функції бази даних
from database import add_user, get_user_stats, update_user_stats
from game_logic import (
    CaesarQuestion,
    PlayerState,
    generate_caesar_decrypt_question,
    generate_caesar_question,
    generate_caesar_shift_guess_question,
)

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

# --- БЛОК СЕРВЕРА ---

async def handle_update_stars(request):
    """Обробляє запити від фронтенду для збереження зірочок"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        stars = data.get("stars")

        if user_id is None or stars is None:
            return web.json_response({"status": "error", "message": "Incomplete data"}, status=400)

        update_user_stats(user_id, stars)
        logger.info(f"Updated stars for user {user_id}: {stars}")
        
        return web.json_response({"status": "ok", "new_stars": stars})
    except Exception as e:
        logger.error(f"Error updating stars: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

app = web.Application()
app.router.add_post('/update_stars', handle_update_stars)

async def on_prepare(request, response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

app.on_response_prepare.append(on_prepare)

# --- КІНЕЦЬ БЛОКУ СЕРВЕРА ---

class GameStates(StatesGroup):
    choose = State()
    in_game = State()
    playing_level = State()

class LevelConfig(TypedDict):
    generator: Callable[[], CaesarQuestion]
    question_template: str
    callback_prefix: str
    next_level_callback: str
    points: int

LEVEL_CONFIGS: dict[str, LevelConfig] = {
    "caesar_easy": {
        "generator": lambda: generate_caesar_question("easy"),
        "question_template": (
            "*Зашифруй слово шифром Цезаря*\n"
            "Слово: `{original_word}`\n"
            "Сдвиг: `{shift}`\n"
            "Оберіть правильний зашифрований варіант:"
        ),
        "callback_prefix": "caesar_answer_",
        "next_level_callback": "start_easy_caesar_mixed",
        "points": 10,
    },
    "caesar_easy_shift": {
        "generator": lambda: generate_caesar_shift_guess_question("easy"),
        "question_template": (
            "*Легкий рівень 2*\n"
            "Зашифроване слово: `{ciphertext}`\n"
            "Початкове слово: `{original_word}`\n\n"
            "Оберіть правильний варіант ключа для слова `{original_word}`:"
        ),
        "callback_prefix": "caesar_answer_",
        "next_level_callback": "start_easy_caesar_mixed",
        "points": 10,
    },
    "caesar_decrypt_easy": {
        "generator": lambda: generate_caesar_decrypt_question("easy"),
        "question_template": (
            "*Розшифруй слово шифром Цезаря*\n"
            "Зашифроване слово: `{original_word}`\n"
            "Сдвиг: `{shift}`\n"
            "Оберіть правильний розшифрований варіант:"
        ),
        "callback_prefix": "caesar_answer_",
        "next_level_callback": "start_easy_caesar_decrypt",
        "points": 10,
    },
}

async def start_game_level(level_type: str, target_message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    player_state = data.get("player_state")
    if not isinstance(player_state, PlayerState):
        player_state = PlayerState()

    player_state.current_level_type = level_type
    config = LEVEL_CONFIGS.get(level_type)
    if not config:
        await target_message.answer("Цей рівень поки не підтримується.")
        return
        
    question_data = config["generator"]()
    question_text = config["question_template"].format(**question_data)
    answer_prefix = config["callback_prefix"]

    player_state.current_question_data = question_data
    await state.update_data(
        player_state=player_state,
        current_question_options=question_data["options"],
    )
    await state.set_state(GameStates.playing_level)

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f"{answer_prefix}{idx}")]
            for idx, option in enumerate(question_data["options"])
        ]
    )

    await target_message.answer(question_text, reply_markup=inline_kb, parse_mode="Markdown")

EASY_MIXED_LEVELS = ("caesar_easy", "caesar_easy_shift")

async def start_random_easy_level(target_message: Message, state: FSMContext) -> None:
    await start_game_level(random.choice(EASY_MIXED_LEVELS), target_message, state)

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or ""

    stats = get_user_stats(user_id)
    if not stats:
        add_user(user_id, username)
        stars = 0
    else:
        # Отримуємо зірочки зі словника, який повертає оновлений database.py
        stars = stats.get('stars', 0)

    data = await state.get_data()
    player_state = data.get("player_state")
    if isinstance(player_state, PlayerState):
        player_state.reset_state()
    else:
        player_state = PlayerState()
    
    await state.update_data(player_state=player_state)
    await state.set_state(GameStates.choose)

    # Версія v=4 для оновлення кешу в Telegram
    web_app_url = f"https://rachel345.github.io/telegram-mini-app-game/index.html?user_id={user_id}&stars={stars}&v=4"
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Відкрити Mini App", web_app=WebAppInfo(url=web_app_url))]
        ]
    )

    await message.answer(
        f"Вітаю, {username}! (user_id: {user_id})\nВаші зірочки: {stars} ⭐",
        reply_markup=inline_kb,
    )

@dp.callback_query(F.data.in_({"start_easy_caesar", "start_easy_caesar_mixed"}))
async def process_start_easy_caesar_mixed(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await start_random_easy_level(callback.message, state)
    await callback.message.delete()

@dp.callback_query(F.data == "start_easy_caesar_decrypt")
async def process_start_easy_caesar_decrypt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await start_game_level("caesar_decrypt_easy", callback.message, state)
    await callback.message.delete()

@dp.callback_query(GameStates.playing_level, F.data.startswith("caesar_answer_"))
async def process_caesar_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    index_str = callback.data.replace("caesar_answer_", "", 1)
    answer_index = int(index_str)

    data = await state.get_data()
    player_state = data.get("player_state")
    options = data.get("current_question_options") or []
    
    user_answer = options[answer_index]
    q_data = player_state.current_question_data

    is_correct = user_answer == q_data.get("encrypted_word_correct") or \
                 (q_data.get("answer_mode") == "shift" and int(user_answer.split(":")[1].strip()) == q_data["shift"])

    if is_correct:
        player_state.add_score(10)
        await callback.message.answer("✅ Правильно!")
    else:
        player_state.decrease_life()
        await callback.message.answer(f"❌ Неправильно.")

    await state.update_data(player_state=player_state)
    
    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Наступне питання", callback_data="start_easy_caesar_mixed")
    ]])
    await callback.message.answer("Далі?", reply_markup=next_kb)

@dp.message(F.web_app_data)
async def process_web_app_data(message: Message, state: FSMContext):
    payload = json.loads(message.web_app_data.data)
    action = payload.get("action")
    if action == "start_level":
        await start_random_easy_level(message, state)

async def main():
    loop = asyncio.get_event_loop()
    bot_task = loop.create_task(dp.start_polling(bot))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    
    logging.info("Сервер запущено на порту 8080")
    await site.start()
    await bot_task

if __name__ == "__main__":   
    asyncio.run(main())        


