import asyncio
import json
import logging
import os
from typing import Callable, TypedDict, Union
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

from database import add_user, get_user_stats
from game_logic import (
    CaesarQuestion,
    PlayerState,
    WordGameQuestion,
    generate_word_game_question,
    generate_caesar_decrypt_question,
    generate_caesar_question,
)

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація бота з API токеном
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class GameStates(StatesGroup):
    choose = State()
    in_game = State()
    playing_level = State()


class LevelConfig(TypedDict):
    generator: Callable[[], Union[CaesarQuestion, WordGameQuestion]]
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
        "next_level_callback": "start_easy_caesar",
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
    "word_game_easy": {
        "generator": lambda: generate_word_game_question("easy"),
        "question_template": (
            "*Вгадай слово*\n"
            "{question_text}\n"
            "Оберіть правильний варіант:"
        ),
        "callback_prefix": "word_game_answer_",
        "next_level_callback": "start_easy_word_game",
        "points": 10,
    },
    "word_game_medium": {
        "generator": lambda: generate_word_game_question("medium"),
        "question_template": (
            "*Вгадай слово*\n"
            "{question_text}\n"
            "Оберіть правильний варіант:"
        ),
        "callback_prefix": "word_game_answer_",
        "next_level_callback": "start_medium_word_game",
        "points": 20,
    },
    "word_game_hard": {
        "generator": lambda: generate_word_game_question("hard"),
        "question_template": (
            "*Вгадай слово*\n"
            "{question_text}\n"
            "Оберіть правильний варіант:"
        ),
        "callback_prefix": "word_game_answer_",
        "next_level_callback": "start_hard_word_game",
        "points": 30,
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
            [
                InlineKeyboardButton(
                    text=option,
                    callback_data=f"{answer_prefix}{idx}",
                )
            ]
            for idx, option in enumerate(question_data["options"])
        ]
    )

    await target_message.answer(
        question_text,
        reply_markup=inline_kb,
        parse_mode="Markdown",
    )


# Обробник команди /start
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or ""

    if not get_user_stats(user_id):
        add_user(user_id, username)

    data = await state.get_data()
    player_state = data.get("player_state")
    if isinstance(player_state, PlayerState):
        player_state.reset_state()
    else:
        player_state = PlayerState()
    await state.update_data(player_state=player_state)
    await state.set_state(GameStates.choose)

    web_app_url = f"https://rachel345.github.io/telegram-mini-app-game/index.html?user_id={user_id}"
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити Mini App",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ],
            [
                InlineKeyboardButton(text="Легкий", callback_data="start_easy_word_game"),
                InlineKeyboardButton(text="Середній", callback_data="start_medium_word_game"),
                InlineKeyboardButton(text="Складний", callback_data="start_hard_word_game"),
            ],
        ]
    )

    await message.answer(
        f"Вітаю, {username}! (user_id: {user_id})\n"
        "Оберіть рівень гри або відкрийте Mini App:",
        reply_markup=inline_kb,
    )

@dp.callback_query(F.data == "start_easy_caesar")
async def process_start_easy_caesar(callback: CallbackQuery, state: FSMContext):
    logger.info("callback_data=%s, state=%s", callback.data, await state.get_state())
    await callback.answer()
    await start_game_level("caesar_easy", callback.message, state)
    await callback.message.delete()


@dp.callback_query(F.data == "start_easy_caesar_decrypt")
async def process_start_easy_caesar_decrypt(callback: CallbackQuery, state: FSMContext):
    logger.info("callback_data=%s, state=%s", callback.data, await state.get_state())
    await callback.answer()
    await start_game_level("caesar_decrypt_easy", callback.message, state)
    await callback.message.delete()


@dp.callback_query(F.data == "start_easy_word_game")
async def process_start_easy_word_game(callback: CallbackQuery, state: FSMContext):
    logger.info("callback_data=%s, state=%s", callback.data, await state.get_state())
    await callback.answer()
    await start_game_level("word_game_easy", callback.message, state)
    await callback.message.delete()


@dp.callback_query(F.data == "start_medium_word_game")
async def process_start_medium_word_game(callback: CallbackQuery, state: FSMContext):
    logger.info("callback_data=%s, state=%s", callback.data, await state.get_state())
    await callback.answer()
    await start_game_level("word_game_medium", callback.message, state)
    await callback.message.delete()


@dp.callback_query(F.data == "start_hard_word_game")
async def process_start_hard_word_game(callback: CallbackQuery, state: FSMContext):
    logger.info("callback_data=%s, state=%s", callback.data, await state.get_state())
    await callback.answer()
    await start_game_level("word_game_hard", callback.message, state)
    await callback.message.delete()


@dp.callback_query(GameStates.playing_level, F.data.startswith("caesar_answer_"))
async def process_caesar_answer(callback: CallbackQuery, state: FSMContext):
    logger.info("callback_data=%s, state=%s", callback.data, await state.get_state())
    await callback.answer()
    index_str = callback.data.replace("caesar_answer_", "", 1)
    try:
        answer_index = int(index_str)
    except ValueError:
        await callback.message.answer("Некоректна відповідь. Спробуйте ще раз.")
        return

    data = await state.get_data()
    player_state = data.get("player_state")
    options = data.get("current_question_options") or []
    if not isinstance(player_state, PlayerState) or not player_state.current_question_data:
        await callback.message.answer("Сесія втрачена. Почніть знову командою /start.")
        await state.clear()
        return
    if answer_index < 0 or answer_index >= len(options):
        await callback.message.answer("Некоректна відповідь. Спробуйте ще раз.")
        return

    user_answer = options[answer_index]

    correct = player_state.current_question_data["encrypted_word_correct"]
    if user_answer == correct:
        points = LEVEL_CONFIGS.get(
            player_state.current_level_type, LEVEL_CONFIGS["caesar_easy"]
        )["points"]
        player_state.add_score(points)
        player_state.add_coins(1)
        await callback.message.answer(f"✅ Правильно! +{points} очок, +1 монета.")
    else:
        player_state.decrease_life()
        await callback.message.answer(
            f"❌ Неправильно. Правильна відповідь: `{correct}`",
            parse_mode="Markdown",
        )

    await state.update_data(player_state=player_state)
    await callback.message.edit_reply_markup(reply_markup=None)

    if player_state.is_game_over():
        restart_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Повторити гру",
                        callback_data="restart_game",
                    )
                ]
            ]
        )
        await callback.message.answer(
            "Гру завершено. Життя закінчились.\n"
            "Натисніть кнопку, щоб почати знову.",
            reply_markup=restart_kb,
        )
        return

    next_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Наступне питання",
                    callback_data=LEVEL_CONFIGS.get(
                        player_state.current_level_type, LEVEL_CONFIGS["caesar_easy"]
                    )["next_level_callback"],
                )
            ]
        ]
    )
    await callback.message.answer(
        "Готові до наступного питання?",
        reply_markup=next_kb,
    )


@dp.callback_query(GameStates.playing_level, F.data.startswith("word_game_answer_"))
async def process_word_game_answer(callback: CallbackQuery, state: FSMContext):
    logger.info("callback_data=%s, state=%s", callback.data, await state.get_state())
    await callback.answer()
    index_str = callback.data.replace("word_game_answer_", "", 1)
    try:
        answer_index = int(index_str)
    except ValueError:
        await callback.message.answer("Некоректна відповідь. Спробуйте ще раз.")
        return

    data = await state.get_data()
    player_state = data.get("player_state")
    options = data.get("current_question_options") or []
    if not isinstance(player_state, PlayerState) or not player_state.current_question_data:
        await callback.message.answer("Сесія втрачена. Почніть знову командою /start.")
        await state.clear()
        return
    if answer_index < 0 or answer_index >= len(options):
        await callback.message.answer("Некоректна відповідь. Спробуйте ще раз.")
        return

    user_answer = options[answer_index]
    correct = player_state.current_question_data["correct_answer"]
    if user_answer == correct:
        points = LEVEL_CONFIGS.get(
            player_state.current_level_type, LEVEL_CONFIGS["word_game_easy"]
        )["points"]
        player_state.add_score(points)
        player_state.add_coins(1)
        await callback.message.answer(f"✅ Правильно! +{points} очок, +1 монета.")
    else:
        player_state.decrease_life()
        await callback.message.answer(
            f"❌ Неправильно. Правильна відповідь: `{correct}`",
            parse_mode="Markdown",
        )

    await state.update_data(player_state=player_state)
    await callback.message.edit_reply_markup(reply_markup=None)

    if player_state.is_game_over():
        restart_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Повторити гру",
                        callback_data="restart_game",
                    )
                ]
            ]
        )
        await callback.message.answer(
            "Гру завершено. Життя закінчились.\n"
            "Натисніть кнопку, щоб почати знову.",
            reply_markup=restart_kb,
        )
        return

    next_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Наступне питання",
                    callback_data=LEVEL_CONFIGS.get(
                        player_state.current_level_type, LEVEL_CONFIGS["word_game_easy"]
                    )["next_level_callback"],
                )
            ]
        ]
    )
    await callback.message.answer(
        "Готові до наступного питання?",
        reply_markup=next_kb,
    )


@dp.message(F.web_app_data)
async def process_web_app_data(message: Message, state: FSMContext):
    try:
        payload = json.loads(message.web_app_data.data)
    except json.JSONDecodeError:
        logger.warning("Некоректні JSON дані з Mini App: %s", message.web_app_data.data)
        await message.answer("Некоректні дані з Mini App.")
        return

    current_state = await state.get_state()
    logger.info("web_app_data: %s, state=%s", payload, current_state)

    action = payload.get("action")
    level = payload.get("level")
    if action == "start_level" and level == "easy_caesar":
        await start_game_level("caesar_easy", message, state)
        return
    if action == "start_level" and level == "easy_caesar_decrypt":
        await start_game_level("caesar_decrypt_easy", message, state)
        return
    if action == "start_level" and level == "easy_word_game":
        await start_game_level("word_game_easy", message, state)
        return
    if action == "start_level" and level == "medium_word_game":
        await start_game_level("word_game_medium", message, state)
        return
    if action == "start_level" and level == "hard_word_game":
        await start_game_level("word_game_hard", message, state)
        return

    await message.answer("Отримані дані з Mini App не підтримуються.")


@dp.callback_query(F.data == "restart_game")
async def process_restart_game(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    player_state = data.get("player_state")
    if isinstance(player_state, PlayerState):
        player_state.reset_state()
        await state.update_data(player_state=player_state)
    await state.clear()
    await cmd_start(callback.message, state)
    await callback.message.delete()


# Функція для запуску бота
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
