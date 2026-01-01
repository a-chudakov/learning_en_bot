import asyncio
import logging
import sys
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand

from src.config import get_config
from src.learning_en_bot.buttons.keyboards import get_main_menu
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.handlers import register_all_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Глобальная переменная для БД
db: WordDatabase = None

async def cmd_start(message: types.Message) -> None:
    """Обработчик команды /start"""
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Я твой помощник для изучения английского!\n\n"
        f"Я помогу тебе учить новые слова и выражения.\n"
        f"Выбери действие ниже 👇",
        reply_markup=get_main_menu()
    )


async def cmd_help(message: types.Message) -> None:
    """Обработчик команды /help"""
    logger.info(f"User {message.from_user.id} asked for help")
    await message.answer(
        "❓ <b>СПРАВКА ПО БОТУ</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Эта справка\n"
        "/stats - Показать статистику\n\n"
        "<b>Как добавить слово:</b>\n"
        "Отправь текст в формате: <code>слово - перевод</code>\n"
        "Пример: <code>cat - кот</code>\n\n"
        "<b>Как использовать кнопки:</b>\n"
        "Нажми на кнопку и следуй инструкциям",
        parse_mode="HTML"
    )


async def button_add_word(message: types.Message) -> None:
    """Обработчик кнопки 'Добавить слово'"""
    logger.info(f"User {message.from_user.id} clicked 'Add word'")
    await message.answer(
        "📝 Отправь мне слово в формате:\n"
        "<code>слово - перевод</code>\n\n"
        "Пример: <code>cat - кот</code>",
        parse_mode="HTML"
    )


async def button_add_photo(message: types.Message) -> None:
    """Обработчик кнопки 'Добавить фото'"""
    logger.info(f"User {message.from_user.id} clicked 'Add photo'")
    await message.answer(
        "📸 Отправь мне фотографию с примером использования слова.\n"
        "Я сохраню её для повторения!"
    )


async def button_my_words(message: types.Message) -> None:
    """Обработчик кнопки 'Мои слова'"""
    logger.info(f"User {message.from_user.id} clicked 'My words'")
    
    words = db.get_user_words(message.from_user.id)
    word_count = len(words)
    
    if word_count == 0:
        await message.answer(
            "📖 <b>Твои слова:</b>\n\n"
            "Пока нет добавленных слов.\n"
            "Нажми '➕ Добавить слово' чтобы начать!",
            parse_mode="HTML"
        )
    else:
        words_text = "\n".join([f"<code>{en}</code> - <code>{ru}</code>" for en, ru in words])
        await message.answer(
            f"📖 <b>Твои слова ({word_count}):</b>\n\n{words_text}",
            parse_mode="HTML"
        )


async def button_reminders(message: types.Message) -> None:
    """Обработчик кнопки 'Напоминания'"""
    logger.info(f"User {message.from_user.id} clicked 'Reminders'")
    await message.answer(
        "🔔 <b>Напоминания</b>\n\n"
        "Уведомления отключены.\n"
        "Добавь слова чтобы включить напоминания!",
        parse_mode="HTML"
    )


async def button_stats(message: types.Message) -> None:
    """Обработчик кнопки 'Статистика'"""
    logger.info(f"User {message.from_user.id} clicked 'Stats'")
    word_count = db.get_user_word_count(message.from_user.id)
    
    await message.answer(
        f"📊 <b>Твоя статистика</b>\n\n"
        f"📝 Слов добавлено: {word_count}\n"
        f"🔄 Повторений: 0\n"
        f"🎯 Уровень: новичок\n\n"
        f"Добавляй слова чтобы улучшить статистику!",
        parse_mode="HTML"
    )


async def button_help(message: types.Message) -> None:
    """Обработчик кнопки 'Помощь'"""
    logger.info(f"User {message.from_user.id} clicked 'Help'")
    await cmd_help(message)


async def handle_text(message: types.Message) -> None:
    """Обработчик обычных текстовых сообщений (добавление слов)"""
    logger.info(f"User {message.from_user.id} sent: {message.text}")
    
    if " - " in message.text:
        parts = message.text.split(" - ", 1)
        word = parts[0].strip()
        translation = parts[1].strip()
        
        success = db.add_word(message.from_user.id, word, translation)
        
        if success:
            await message.answer(
                f"✅ <b>Слово добавлено!</b>\n\n"
                f"📝 <code>{word}</code> - <code>{translation}</code>\n\n"
                f"Это слово сохранено для повторения!",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"⚠️ <b>Слово уже есть в списке!</b>\n\n"
                f"📝 <code>{word}</code> - <code>{translation}</code>",
                parse_mode="HTML"
            )
    else:
        await message.answer(
            "❌ Неправильный формат!\n\n"
            "Отправь в формате: <code>слово - перевод</code>\n"
            "Пример: <code>cat - кот</code>",
            parse_mode="HTML"
        )


async def set_commands(bot: Bot) -> None:
    """Установить меню команд"""
    commands = [
        BotCommand(command="start", description="Начало работы"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="stats", description="Статистика"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Bot commands set")

async def main() -> None:
    """Главная функция бота"""
    
    global db
    
    logger.info("🤖 Starting bot initialization...")
    
    try:
        # Загружаем конфиг
        logger.info("Loading configuration...")
        config = get_config()
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"Bot username: {config.bot_username}")
        logger.info(f"Database path: {config.database_path}")

        # Инициализируем БД
        logger.info("Initializing database...")
        db = WordDatabase(config.database_path)
        logger.info("✅ Database initialized")

        # Инициализируем бота
        logger.info("Creating Bot instance...")
        bot = Bot(token=config.telegram_token)
        logger.info("✅ Bot initialized")

        # Инициализируем диспетчер
        logger.info("Creating Dispatcher...")
        storage = MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        logger.info("✅ Dispatcher initialized")

        # Устанавливаем команды
        await set_commands(bot)

        # Регистрируем обработчики команд
        logger.info("Registering handlers...")
        dispatcher.message.register(cmd_start, Command("start"))
        dispatcher.message.register(cmd_help, Command("help"))
        
        # Регистрируем обработчики кнопок
        dispatcher.message.register(button_add_word, lambda msg: msg.text == "➕ Добавить слово")
        dispatcher.message.register(button_add_photo, lambda msg: msg.text == "📸 Добавить фото")
        dispatcher.message.register(button_my_words, lambda msg: msg.text == "📖 Мои слова")
        dispatcher.message.register(button_reminders, lambda msg: msg.text == "🔔 Напоминания")
        dispatcher.message.register(button_stats, lambda msg: msg.text == "📊 Статистика")
        dispatcher.message.register(button_help, lambda msg: msg.text == "❓ Помощь")
        
        # Обработчик для текстовых сообщений
        dispatcher.message.register(handle_text)
        
        # Регистрируем остальные обработчики
        register_all_handlers(dispatcher)
        logger.info("✅ Handlers registered")

        # Запускаем бота
        logger.info("🤖 Bot started. Polling mode activated...")
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Error in main: {type(e).__name__}: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🤖 LEARNING ENGLISH BOT - STARTING")
    logger.info("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)
