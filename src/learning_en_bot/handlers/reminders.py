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
        """Показать меню напоминаний"""
        logger.info(f"User {message.from_user.id} clicked 'Reminders'")
        stats = self.db.get_reminder_stats(message.from_user.id)
        
        if stats["total_words"] == 0:
            await message.answer(
                "🔔 <b>НАПОМИНАНИЯ</b>\n\n"
                "❌ Пока нет добавленных слов.",
                parse_mode="HTML"
            )
            return
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🌅 Утренние")],
                [KeyboardButton(text="🌙 Вечерние")],
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="⬅️ Назад")],
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            f"🔔 <b>НАПОМИНАНИЯ</b>\n\n"
            f"📝 Слов добавлено: {stats['total_words']}\n"
            f"✨ Никогда не повторённых: {stats['never_reviewed']}\n\n"
            f"Выбери период:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
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
