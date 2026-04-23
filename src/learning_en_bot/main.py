"""
ГЛАВНЫЙ ФАЙЛ БОТА (Entry Point)
"""

import asyncio
import sys
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand

from src.config import get_config
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.reminders import ReminderSystem
from src.learning_en_bot.scheduler import ReminderScheduler
from src.learning_en_bot.settings import SettingsManager
from src.learning_en_bot.services.srs_service import SRSService
from src.learning_en_bot.services.quiz_service import QuizService
from src.learning_en_bot.handlers import (
    commands,
    words,
    quiz,
    reminders,
    settings,
    callbacks
)
from src.learning_en_bot.handlers import register_all_handlers
from src.learning_en_bot.middlewares.auth import AuthMiddleware

# Настройка loguru
logger.remove()  # Удаляем стандартный handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)


async def set_commands(bot: Bot) -> None:
    """Установить команды бота"""
    commands_list = [
        BotCommand(command="start", description="Начало"),
        BotCommand(command="help", description="Справка"),
    ]
    await bot.set_my_commands(commands_list)


async def main() -> None:
    """Главная функция запуска бота"""
    logger.info("🤖 Starting bot...")
    
    try:
        # Загружаем конфигурацию
        config = get_config()
        logger.info(f"✅ Config loaded: {config.bot_username}")

        # Инициализируем базу данных
        db = WordDatabase(config.database_path)
        logger.info("✅ Database initialized")
        
        # Инициализируем сервисы
        reminder_system = ReminderSystem(db)
        settings_manager = SettingsManager(db, config.timezone)
        srs_service = SRSService(db)
        quiz_service = QuizService(db, srs_service)
        logger.info("✅ Services initialized")
        
        # Инициализируем бота и диспетчер
        bot = Bot(token=config.telegram_token)
        storage = MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        
        # Добавляем middleware для приватного доступа
        if config.allowed_user_id:
            dispatcher.message.middleware(AuthMiddleware())
            dispatcher.callback_query.middleware(AuthMiddleware())
            logger.info(f"🔒 Private bot mode enabled for user {config.allowed_user_id}")
        
        # Устанавливаем команды
        await set_commands(bot)
        logger.info("✅ Bot commands set")
        
        # Инициализируем планировщик напоминаний
        scheduler = ReminderScheduler(bot, db, reminder_system, config.timezone)
        scheduler.start()
        logger.info("✅ Scheduler started")
        
        # Инициализируем handlers
        words_handler = words.WordsHandler(db)
        quiz_handler = quiz.QuizHandler(quiz_service)
        reminders_handler = reminders.RemindersHandler(reminder_system, db)
        settings_handler = settings.SettingsHandler(settings_manager, db, config.timezone)
        callbacks_handler = callbacks.CallbacksHandler(db)
        
        # Регистрируем все handlers
        register_all_handlers(
            dispatcher,
            words_handler,
            quiz_handler,
            reminders_handler,
            settings_handler,
            callbacks_handler
        )
        logger.info("✅ Handlers registered")

        # Запускаем бота
        logger.info("🤖 Bot started. Polling...")
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types()
        )
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🤖 LEARNING ENGLISH BOT")
    logger.info("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopped")
    except Exception as e:
        logger.error(f"❌ FATAL: {e}", exc_info=True)
        sys.exit(1)
