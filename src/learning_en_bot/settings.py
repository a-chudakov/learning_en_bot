"""
Менеджер настроек пользователя
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loguru import logger


class SettingsManager:
    """Управление настройками пользователя"""

    def __init__(self, db, timezone: str = "UTC"):
        self.db = db
        self.tz_label = datetime.now(ZoneInfo(timezone)).strftime("%Z")

    def get_settings_message(self, user_id: int) -> str:
        """Получить сообщение с текущими настройками"""
        settings = self.db.get_user_settings(user_id)

        status = "✅ Включены" if settings["reminders_enabled"] else "❌ Отключены"

        return (
            f"⚙️ <b>НАСТРОЙКИ НАПОМИНАНИЙ</b>\n\n"
            f"🌅 Утреннее время: <code>{settings['morning_time']} {self.tz_label}</code>\n"
            f"🌙 Вечернее время: <code>{settings['evening_time']} {self.tz_label}</code>\n"
            f"🔔 Статус: {status}\n\n"
            f"Выбери что изменить:"
        )
    
    def get_settings_keyboard(self) -> ReplyKeyboardMarkup:
        """Клавиатура настроек"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🌅 Установить утреннее время")],
                [KeyboardButton(text="🌙 Установить вечернее время")],
                [KeyboardButton(text="🔔 Вкл/Выкл напоминания")],
                [KeyboardButton(text="⬅️ Назад")],
            ],
            resize_keyboard=True
        )
    
    def get_time_selection_keyboard(self) -> ReplyKeyboardMarkup:
        """Клавиатура для выбора времени (быстрые варианты)"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="06:00"), KeyboardButton(text="07:00"), KeyboardButton(text="08:00")],
                [KeyboardButton(text="09:00"), KeyboardButton(text="10:00"), KeyboardButton(text="11:00")],
                [KeyboardButton(text="18:00"), KeyboardButton(text="19:00"), KeyboardButton(text="20:00")],
                [KeyboardButton(text="21:00"), KeyboardButton(text="22:00"), KeyboardButton(text="23:00")],
                [KeyboardButton(text="Своё время")],
                [KeyboardButton(text="⬅️ Назад")],
            ],
            resize_keyboard=True
        )
    
    def validate_time(self, time_str: str) -> bool:
        """Проверить формат времени HH:MM"""
        try:
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                return False
            
            hours = int(parts[0])
            minutes = int(parts[1])
            
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except ValueError:
            return False
