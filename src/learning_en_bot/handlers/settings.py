"""
Обработчики для настроек
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger
from src.learning_en_bot.settings import SettingsManager
from src.learning_en_bot.fsm_states import ReminderStates
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.buttons.keyboards import get_main_menu


class SettingsHandler:
    """Обработчики для настроек"""

    def __init__(self, settings_manager: SettingsManager, db: WordDatabase, timezone: str = "UTC"):
        self.settings_manager = settings_manager
        self.db = db
        self.tz_label = datetime.now(ZoneInfo(timezone)).strftime("%Z")
    
    async def button_settings(self, message: types.Message) -> None:
        """Показать меню настроек"""
        logger.info(f"User {message.from_user.id} clicked 'Settings'")
        settings_text = self.settings_manager.get_settings_message(message.from_user.id)
        keyboard = self.settings_manager.get_settings_keyboard()
        
        await message.answer(settings_text, parse_mode="HTML", reply_markup=keyboard)
    
    async def change_morning_time(self, message: types.Message, state: FSMContext) -> None:
        """Запрос ввода утреннего времени"""
        logger.info(f"User {message.from_user.id} clicked 'Change morning time'")
        await state.set_state(ReminderStates.waiting_for_morning_time)
        
        keyboard = self.settings_manager.get_time_selection_keyboard()
        await message.answer(
            "🌅 <b>УСТАНОВИТЬ УТРЕННЕЕ ВРЕМЯ</b>\n\n"
            "Выбери предложенное время или напиши своё:\n"
            "Формат: <code>HH:MM</code>\n"
            "Пример: <code>09:00</code>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def handle_morning_time(self, message: types.Message, state: FSMContext) -> None:
        """Обработка ввода утреннего времени"""
        time_str = message.text.strip()
        
        # Если нажал "Назад"
        if time_str == "⬅️ Назад":
            await state.clear()
            await self.button_settings(message)
            return
        
        if not self.settings_manager.validate_time(time_str):
            await message.answer(
                "❌ Неправильный формат!\n"
                "Используй: <code>HH:MM</code>\n"
                "Пример: <code>09:00</code>",
                parse_mode="HTML"
            )
            return
        
        success = self.db.update_user_settings(message.from_user.id, morning_time=time_str)
        await state.clear()
        
        if success:
            await message.answer(
                f"✅ <b>Утреннее время установлено!</b>\n\n"
                f"⏰ Время: <code>{time_str} {self.tz_label}</code>\n\n"
                f"Бот будет присылать напоминания в это время 📲",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                "❌ <b>Ошибка при сохранении настроек!</b>\n\n"
                "Попробуй ещё раз или обратись в поддержку.",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
    
    async def change_evening_time(self, message: types.Message, state: FSMContext) -> None:
        """Запрос ввода вечернего времени"""
        logger.info(f"User {message.from_user.id} clicked 'Change evening time'")
        await state.set_state(ReminderStates.waiting_for_evening_time)
        
        keyboard = self.settings_manager.get_time_selection_keyboard()
        await message.answer(
            "🌙 <b>УСТАНОВИТЬ ВЕЧЕРНЕЕ ВРЕМЯ</b>\n\n"
            "Выбери предложенное время или напиши своё:\n"
            "Формат: <code>HH:MM</code>\n"
            "Пример: <code>20:00</code>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def handle_evening_time(self, message: types.Message, state: FSMContext) -> None:
        """Обработка ввода вечернего времени"""
        time_str = message.text.strip()
        
        # Если нажал "Назад"
        if time_str == "⬅️ Назад":
            await state.clear()
            await self.button_settings(message)
            return
        
        if not self.settings_manager.validate_time(time_str):
            await message.answer(
                "❌ Неправильный формат!\n"
                "Используй: <code>HH:MM</code>\n"
                "Пример: <code>20:00</code>",
                parse_mode="HTML"
            )
            return
        
        success = self.db.update_user_settings(message.from_user.id, evening_time=time_str)
        await state.clear()
        
        if success:
            await message.answer(
                f"✅ <b>Вечернее время установлено!</b>\n\n"
                f"⏰ Время: <code>{time_str} {self.tz_label}</code>\n\n"
                f"Бот будет присылать напоминания в это время 📲",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                "❌ <b>Ошибка при сохранении настроек!</b>\n\n"
                "Попробуй ещё раз или обратись в поддержку.",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
    
    async def toggle_reminders(self, message: types.Message) -> None:
        """Включить/отключить напоминания"""
        logger.info(f"User {message.from_user.id} clicked 'Toggle reminders'")
        settings = self.db.get_user_settings(message.from_user.id)
        new_status = not settings["reminders_enabled"]
        
        self.db.update_user_settings(message.from_user.id, reminders_enabled=new_status)
        status_text = "✅ Включены" if new_status else "❌ Отключены"
        
        await message.answer(
            f"🔔 Напоминания {status_text}",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
    
    async def go_back(self, message: types.Message, state: FSMContext) -> None:
        """Вернуться в главное меню"""
        logger.info(f"User {message.from_user.id} went back")
        await state.clear()
        await message.answer(
            "⬅️ Главное меню",
            reply_markup=get_main_menu()
        )
