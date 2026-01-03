"""
Планировщик автоматических напоминаний
Отправляет напоминания каждому пользователю в его индивидуальное время
"""

from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from loguru import logger


class ReminderScheduler:
    """Планировщик напоминаний с поддержкой индивидуальных настроек"""
    
    def __init__(self, bot: Bot, db, reminder_system):
        self.bot = bot
        self.db = db
        self.reminder_system = reminder_system
        self.scheduler = AsyncIOScheduler()
        self.sent_today = {}  # {(user_id, 'morning'/'evening'): date} - для отслеживания отправленных сегодня
    
    def _parse_time(self, time_str: str) -> tuple[int, int]:
        """Парсинг времени из строки HH:MM"""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError("Invalid time format")
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Time out of range")
            return hour, minute
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid time format '{time_str}', using default 09:00: {e}")
            return 9, 0
    
    async def send_morning_reminder(self, user_id: int) -> None:
        """Отправить утреннее напоминание"""
        try:
            # Проверяем включены ли напоминания
            settings = self.db.get_user_settings(user_id)
            if not settings["reminders_enabled"]:
                return
            
            # Проверяем, не отправляли ли уже сегодня
            today = datetime.now().date()
            key = (user_id, 'morning')
            if self.sent_today.get(key) == today:
                return
            
            # Получаем утреннее сообщение
            text, _ = self.reminder_system.get_morning_reminder_message(user_id)
            
            if text and "❌ Нет слов" not in text:
                await self.bot.send_message(user_id, text, parse_mode="HTML")
                self.sent_today[key] = today
                logger.info(f"✅ Morning reminder sent to user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error sending morning reminder to {user_id}: {e}")
    
    async def send_evening_reminder(self, user_id: int) -> None:
        """Отправить вечернее напоминание"""
        try:
            # Проверяем включены ли напоминания
            settings = self.db.get_user_settings(user_id)
            if not settings["reminders_enabled"]:
                return
            
            # Проверяем, не отправляли ли уже сегодня
            today = datetime.now().date()
            key = (user_id, 'evening')
            if self.sent_today.get(key) == today:
                return
            
            # Получаем вечернее сообщение
            text, _ = self.reminder_system.get_evening_reminder_message(user_id)
            
            if text and "❌ Нет слов" not in text:
                await self.bot.send_message(user_id, text, parse_mode="HTML")
                self.sent_today[key] = today
                logger.info(f"✅ Evening reminder sent to user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error sending evening reminder to {user_id}: {e}")
    
    def start(self) -> None:
        """
        Запустить планировщик с проверкой каждую минуту
        Отправляет напоминания пользователям в их индивидуальное время
        """
        try:
            # Запускаем проверку каждую минуту
            self.scheduler.add_job(
                func=self._check_and_send_reminders,
                trigger=CronTrigger(minute="*"),  # Каждую минуту
                id="reminder_checker",
                name="Reminder Checker",
                replace_existing=True
            )
            
            # Запускаем планировщик
            self.scheduler.start()
            logger.info("🚀 Reminder scheduler started (individual user times)")
        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")
    
    async def _check_and_send_reminders(self) -> None:
        """Проверить и отправить напоминания пользователям в их время"""
        try:
            now = datetime.now()
            current_time = now.time().replace(second=0, microsecond=0)
            today = now.date()
            
            # Получаем всех пользователей с их настройками
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Получаем пользователей из user_settings
            cursor.execute("""
                SELECT user_id, morning_time, evening_time, reminders_enabled
                FROM user_settings
                WHERE reminders_enabled = 1
            """)
            users = cursor.fetchall()
            conn.close()
            
            for user_id, morning_time_str, evening_time_str, _ in users:
                try:
                    # Парсим время
                    morning_hour, morning_minute = self._parse_time(morning_time_str)
                    evening_hour, evening_minute = self._parse_time(evening_time_str)
                    
                    morning_time = time(morning_hour, morning_minute)
                    evening_time = time(evening_hour, evening_minute)
                    
                    # Проверяем утреннее время
                    if current_time == morning_time:
                        key = (user_id, 'morning')
                        if self.sent_today.get(key) != today:
                            await self.send_morning_reminder(user_id)
                    
                    # Проверяем вечернее время
                    if current_time == evening_time:
                        key = (user_id, 'evening')
                        if self.sent_today.get(key) != today:
                            await self.send_evening_reminder(user_id)
                            
                except Exception as e:
                    logger.error(f"❌ Error processing user {user_id}: {e}")
            
            # Очищаем старые записи (старше 1 дня)
            keys_to_remove = [
                key for key, date in self.sent_today.items()
                if date < today
            ]
            for key in keys_to_remove:
                del self.sent_today[key]
                
        except Exception as e:
            logger.error(f"❌ Error in reminder checker: {e}")
    
    def stop(self) -> None:
        """Остановить планировщик"""
        try:
            self.scheduler.shutdown()
            logger.info("⛔ Reminder scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
