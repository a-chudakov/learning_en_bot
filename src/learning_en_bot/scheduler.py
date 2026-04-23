"""
Планировщик автоматических напоминаний
Отправляет напоминания каждому пользователю в его индивидуальное время
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from loguru import logger


class ReminderScheduler:
    """Планировщик напоминаний с поддержкой индивидуальных настроек"""

    def __init__(self, bot: Bot, db, reminder_system, timezone: str = "UTC"):
        self.bot = bot
        self.db = db
        self.reminder_system = reminder_system
        self.tz = ZoneInfo(timezone)
        self.scheduler = AsyncIOScheduler(timezone=timezone)
    
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
    
    async def send_morning_reminder(self, user_id: int, today_date: str) -> None:
        """Отправить утреннее напоминание"""
        try:
            settings = self.db.get_user_settings(user_id)
            if not settings["reminders_enabled"]:
                return

            if self.db.was_reminder_sent_today(user_id, "morning", today_date):
                return

            text, _ = self.reminder_system.get_morning_reminder_message(user_id)

            if text and "❌ Нет слов" not in text:
                await self.bot.send_message(user_id, text, parse_mode="HTML")
                self.db.mark_reminder_sent(user_id, "morning")
                logger.info(f"✅ Morning reminder sent to user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error sending morning reminder to {user_id}: {e}")

    async def send_evening_reminder(self, user_id: int, today_date: str) -> None:
        """Отправить вечернее напоминание"""
        try:
            settings = self.db.get_user_settings(user_id)
            if not settings["reminders_enabled"]:
                return

            if self.db.was_reminder_sent_today(user_id, "evening", today_date):
                return

            text, _ = self.reminder_system.get_evening_reminder_message(user_id)

            if text and "❌ Нет слов" not in text:
                await self.bot.send_message(user_id, text, parse_mode="HTML")
                self.db.mark_reminder_sent(user_id, "evening")
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
            now = datetime.now(self.tz)
            current_time = now.time().replace(second=0, microsecond=0)
            today_date = now.strftime("%Y-%m-%d")

            users = self.db.get_users_for_reminders()

            for user_id, morning_time_str, evening_time_str in users:
                try:
                    morning_hour, morning_minute = self._parse_time(morning_time_str)
                    evening_hour, evening_minute = self._parse_time(evening_time_str)

                    if current_time == time(morning_hour, morning_minute):
                        await self.send_morning_reminder(user_id, today_date)

                    if current_time == time(evening_hour, evening_minute):
                        await self.send_evening_reminder(user_id, today_date)

                except Exception as e:
                    logger.error(f"❌ Error processing user {user_id}: {e}")

        except Exception as e:
            logger.error(f"❌ Error in reminder checker: {e}")
    
    def stop(self) -> None:
        """Остановить планировщик"""
        try:
            self.scheduler.shutdown()
            logger.info("⛔ Reminder scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
