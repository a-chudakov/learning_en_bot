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
        
        "<b>➕ Добавление слов и фраз:</b>\n"
        "Формат: <code>слово/фраза - перевод</code>\n\n"
        "Примеры:\n"
        "• <code>cat - кот - [kæt]</code>\n"
        "• <code>a black cat - чёрная кошка</code>\n"
        "• <code>break a leg - удачи! #idioms</code>\n\n"
        
        "<b>✏️ Редактирование:</b>\n"
        "Нажми «✏️ Редактировать» → введи слово для поиска → выбери из результатов.\n\n"
        
        "<b>📖 Мои слова:</b>\n"
        "Просмотр всех слов списком (по 50 на страницу).\n\n"
        
        "<b>🎯 Тренировка:</b>\n"
        "• Умная (SRS) — слова для повторения\n"
        "• Случайные — любой набор\n"
        "• Сложные — самые трудные\n"
        "• Новые — недавно добавленные\n\n"
        
        "<b>🔔 Напоминания:</b>\n"
        "Показывает 5 случайных слов.\n\n"
        
        "<b>📊 Статистика:</b>\n"
        "Твой прогресс в изучении.",
        parse_mode="HTML"
    )
