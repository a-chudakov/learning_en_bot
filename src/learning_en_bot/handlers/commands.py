"""
Обработчики команд бота (/start, /help)
"""

from aiogram import types
from loguru import logger
from src.learning_en_bot.buttons.keyboards import get_main_menu


async def cmd_start(message: types.Message) -> None:
    """Обработчик команды /start"""
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Я твой помощник для изучения английского!\n\n"
        f"Выбери действие ниже 👇",
        reply_markup=get_main_menu()
    )


async def cmd_help(message: types.Message) -> None:
    """Обработчик команды /help"""
    logger.info(f"User {message.from_user.id} asked for help")
    await message.answer(
        "❓ <b>СПРАВКА ПО БОТУ</b>\n\n"
        "<b>Как добавить слово:</b>\n"
        "Отправь: <code>слово - перевод - транскрипция</code>\n"
        "Примеры:\n"
        "• <code>cat - кот - [kæt]</code>\n"
        "• <code>hello - привет</code> (транскрипция опциональна)\n"
        "• <code>cat - кот - [kæt] #животные</code> (с темой)\n\n"
        "<b>Автоматические напоминания:</b>\n"
        "Бот отправляет 5 случайных слов в установленное время.\n"
        "Нажми ⚙️ Настройки чтобы настроить время!\n\n"
        "<b>Тренировка:</b>\n"
        "Используй 🎯 Тренировка для интерактивного изучения слов!",
        parse_mode="HTML"
    )
