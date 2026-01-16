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
        
        "<b>📝 Добавление слов:</b>\n"
        "Отправь: <code>слово - перевод</code>\n"
        "Примеры:\n"
        "• <code>cat - кот</code>\n"
        "• <code>hello - привет - həˈləʊ</code>\n"
        "• <code>dog - собака #животные</code>\n\n"
        
        "<b>🎯 Тренировка:</b>\n"
        "Выбери режим тренировки и отвечай на вопросы с вариантами ответа.\n"
        "• Умная тренировка - слова для повторения\n"
        "• Случайные слова - любой набор\n"
        "• Сложные слова - самые трудные\n"
        "• Новые слова - недавно добавленные\n\n"
        
        "<b>🔔 Напоминания:</b>\n"
        "Показывает 5 случайных слов для повторения.\n\n"
        
        "<b>⚙️ Настройки:</b>\n"
        "Настрой время автоматических напоминаний (опционально).\n\n"
        
        "<b>📊 Статистика:</b>\n"
        "Смотри свой прогресс в изучении слов.",
        parse_mode="HTML"
    )
