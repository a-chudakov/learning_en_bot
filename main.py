import asyncio
import logging
from typing import Optional
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand
from src.config import get_config
from src.learning_en_bot.buttons.keyboards import get_main_menu
from src.learning_en_bot.handlers import register_all_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

async def cmd_start(message: types.Message) -> None:
    greeting = (
        "👋 Привет! Я твой помощник для изучения английского!\n\n"
        "Я помогу тебе учить новые слова и выражения.\n"
        "Отправляй мне:\n"
        "📝 Слова (в формате: слово - перевод)\n"
        "📸 Фотографии с примерами\n\n"
        "И я буду отправлять их для повторения!\n\n"
        "Выбери действие ниже 👇"
    )
    
    await message.answer(greeting, reply_markup=get_main_menu())
    logger.info(f"User {message.from_user.id} started the bot")


async def cmd_help(message: types.Message) -> None:
    help_text = (
        "📚 <b>СПРАВКА ПО БОТУ</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Эта справка\n"
        "/stats - Показать статистику\n"
        "/history - История добавленных слов\n\n"
        "<b>Как добавить слово:</b>\n"
        "Отправь текст в формате: <code>слово - перевод</code>\n"
        "Пример: <code>cat - кот</code>\n\n"
        "<b>Как использовать кнопки:</b>\n"
        "Нажми на кнопку и следуй инструкциям\n"
        "Бот подскажет что дальше"
    )

    await message.answer(help_text, parse_mode="HTML")
    logger.info(f"User {message.from_user.id} requested help")


async def cmd_stats(message: types.Message) -> None:
    stats_text = (
        "📊 <b>Твоя статистика</b>\n\n"
        "📝 Слов добавлено: 0\n"
        "🔄 Повторений: 0\n"
        "🎯 Уровень: новичок\n\n"
        "Добавляй слова чтобы улучшить статистику!"
    )
    
    await message.answer(stats_text, parse_mode="HTML")
    logger.info(f"User {message.from_user.id} requested stats")

def register_handlers() -> None:
    assert dp is not None, "Dispatcher not initialized"
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_stats, Command("stats"))
    register_all_handlers(dp)

async def main() -> None:
    global bot, dp
    config = get_config()
    logger.info("✅ Configuration loaded successfully")
    logger.info(f"Bot username: {config.bot_username}")
    logger.info(f"Database path: {config.database_path}")
    bot = Bot(token=config.telegram_token)
    logger.info("✅ Bot initialized")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logger.info("✅ Dispatcher initialized")
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="history", description="История слов"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Bot commands set")
    register_handlers()
    logger.info("✅ Handlers registered")
    try:
        logger.info("🤖 Bot started. Polling mode activated...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⏸️ Bot interrupted by user")
    finally:
        await bot.session.close()
        logger.info("✅ Bot session closed")

if __name__ == "__main__":    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✋ Bot stopped by user (Ctrl+C)")
