from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить"),
                KeyboardButton(text="✏️ Редактировать"),
            ],
            [
                KeyboardButton(text="📖 Мои слова"),
                KeyboardButton(text="🎯 Тренировка"),
            ],
            [
                KeyboardButton(text="🔔 Напоминания"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard
