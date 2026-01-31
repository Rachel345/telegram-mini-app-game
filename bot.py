import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
)
from aiogram.filters import CommandStart

from database import add_user, get_user_stats

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Визначення станів FSM
class Form(StatesGroup):
    waiting_for_name = State()

# Ініціалізація бота з API токеном
API_TOKEN = '8290033163:AAH11alj0hWFsRkycOZ1hA5vybom0JH44dA'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Обробник команди /start
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or ""

    if not get_user_stats(user_id):
        add_user(user_id, username)

    web_app_url = f"https://your_mini_app_url.com?user_id={user_id}"
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


# Обробник для отримання імені користувача
@dp.message(Form.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    user_name = message.text.strip()
    # Збереження імені в стані
    await state.update_data(name=user_name)
    
    # Створення інлайн-кнопки "Давай"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Давай", callback_data="start_game")]
    ])
    
    # Відправка підтвердження з інлайн-кнопкою
    await message.answer(
        f"Приємно познайомитись! {user_name}, давай пограємо?",
        reply_markup=inline_kb
    )
    
    # Очищення стану FSM
    await state.clear()


# Обробник натискання на інлайн-кнопку "Давай"
@dp.callback_query(F.data == "start_game")
async def process_start_game(callback: CallbackQuery):
    # Відповідь на callback запит (щоб прибрати індикатор завантаження)
    await callback.answer()
    
    # Видалення попереднього повідомлення з інлайн-кнопкою
    await callback.message.delete()
    
    # Створення Reply-клавіатури з рівнями складності
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="легкий"),
                KeyboardButton(text="середній"),
                KeyboardButton(text="складний")
            ],
            [
                KeyboardButton(text="навчання грі"),
                KeyboardButton(text="цікава інформація про криптографію")
            ]
        ],
        resize_keyboard=True
    )
    
    # Відправка нового повідомлення з Reply-клавіатурою
    await callback.message.answer(
        "Я хочу тобі запропонувати три рівня складності. Обери будь-який з них, будь ласка.",
        reply_markup=reply_kb
    )


# Обробники для кнопок складності
@dp.message(F.text.in_(["легкий", "середній", "складний"]))
async def process_difficulty(message: Message):
    difficulty = message.text
    await message.answer(f"Ти обрав(ла) {difficulty}.")


# Обробник для кнопки "навчання грі"
@dp.message(F.text == "навчання грі")
async def process_training(message: Message):
    await message.answer("Починаємо навчання грі!")


# Обробник для кнопки "цікава інформація про криптографію"
@dp.message(F.text == "цікава інформація про криптографію")
async def process_cryptography_info(message: Message):
    await message.answer("Зараз розповім тобі цікаву інформацію про криптографію.")


# Функція для запуску бота
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
