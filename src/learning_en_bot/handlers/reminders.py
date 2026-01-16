"""
Обработчики для напоминаний
"""

from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loguru import logger
from src.learning_en_bot.reminders import ReminderSystem
from src.learning_en_bot.buttons.keyboards import get_main_menu


class RemindersHandler:
    """Обработчики для напоминаний"""
    
    def __init__(self, reminder_system: ReminderSystem, db):
        self.reminder_system = reminder_system
        self.db = db
    
    async def button_reminders(self, message: types.Message) -> None:
        """Показать 5 случайных слов для повторения"""
        logger.info(f"User {message.from_user.id} clicked 'Reminders'")
        user_id = message.from_user.id
        
        # Получаем 5 случайных слов
        words = self.db.get_random_words(user_id, limit=5)
        
        if not words:
            await message.answer(
                "🔔 <b>НАПОМИНАНИЯ</b>\n\n"
                "❌ Пока нет добавленных слов.",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
            return
        
        # Форматируем слова
        words_lines = []
        for i, (en, ru, trans, topic) in enumerate(words, 1):
            trans_part = f" [{trans}]" if trans else ""
            topic_part = f" (#{topic})" if topic else ""
            words_lines.append(f"<code>{i}.</code> <b>{en}</b>{trans_part} - {ru}{topic_part}")
        
        words_text = "\n".join(words_lines)
        
        message_text = (
            f"🔔 <b>НАПОМИНАНИЯ</b>\n\n"
            f"Пора повторить слова! 📚\n\n"
            f"{words_text}\n\n"
            f"Хочешь ещё? Нажми 🔔 Напоминания снова!"
        )
        
        await message.answer(message_text, parse_mode="HTML", reply_markup=get_main_menu())
    
    async def button_morning_reminders(self, message: types.Message) -> None:
        """Показать утренние напоминания"""
        logger.info(f"User {message.from_user.id} selected morning reminders")
        message_text, keyboard = self.reminder_system.get_morning_reminder_message(message.from_user.id)
        await message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
    
    async def button_evening_reminders(self, message: types.Message) -> None:
        """Показать вечерние напоминания"""
        logger.info(f"User {message.from_user.id} selected evening reminders")
        message_text, keyboard = self.reminder_system.get_evening_reminder_message(message.from_user.id)
        await message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
    
    async def button_stats(self, message: types.Message) -> None:
        """Показать статистику"""
        logger.info(f"User {message.from_user.id} clicked stats")
        text = self.reminder_system.get_stats_message(message.from_user.id)
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())
