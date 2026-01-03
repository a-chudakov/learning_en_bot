"""
ГЛАВНЫЙ ФАЙЛ БОТА (Entry Point) с настройкой времени
"""

import asyncio
import sys
from loguru import logger

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from src.config import get_config
from src.learning_en_bot.buttons.keyboards import get_main_menu
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.reminders import ReminderSystem
from src.learning_en_bot.scheduler import ReminderScheduler
from src.learning_en_bot.settings import SettingsManager
from src.learning_en_bot.fsm_states import ReminderStates
from src.learning_en_bot.handlers import register_all_handlers

# Настройка loguru
logger.remove()  # Удаляем стандартный handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

db: WordDatabase = None
reminder_system: ReminderSystem = None
scheduler: ReminderScheduler = None
settings_manager: SettingsManager = None


# ==================================================
# КОМАНДЫ
# ==================================================

async def cmd_start(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Я твой помощник для изучения английского!\n\n"
        f"Выбери действие ниже 👇",
        reply_markup=get_main_menu()
    )


async def cmd_help(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} asked for help")
    await message.answer(
        "❓ <b>СПРАВКА ПО БОТУ</b>\n\n"
        "<b>Как добавить слово:</b>\n"
        "Отправь: <code>слово - перевод - транскрипция</code>\n"
        "Примеры:\n"
        "• <code>cat - кот - [kæt]</code>\n"
        "• <code>hello - привет</code> (транскрипция опциональна)\n"
        "• <code>cat - кот - [kæt] #животные</code> (с темой)\n\n"
        "<b>Автоматические напоминания:</b>\n"
        "Бот отправляет 5 случайных слов в установленное время.\n"
        "Нажми ⚙️ Настройки чтобы настроить время!",
        parse_mode="HTML"
    )


# ==================================================
# ГЛАВНОЕ МЕНЮ
# ==================================================

async def button_add_word(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} clicked 'Add word'")
    await message.answer(
        "📝 Отправь слово в формате:\n"
        "<code>слово - перевод - транскрипция</code>\n\n"
        "Примеры:\n"
        "<code>cat - кот - [kæt]</code>\n"
        "<code>hello - привет</code> (транскрипция опциональна)\n\n"
        "Можно добавить тему через #:\n"
        "<code>cat - кот - [kæt] #животные</code>",
        parse_mode="HTML"
    )


async def button_my_words(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} clicked 'My words'")
    words = db.get_user_words(message.from_user.id)
    
    if not words:
        await message.answer(
            "📖 <b>Твои слова:</b>\n\nПока нет добавленных слов.",
            parse_mode="HTML"
        )
    else:
        words_lines = []
        for en, ru, trans, topic in words:
            trans_part = f" [{trans}]" if trans else ""
            topic_part = f" (#{topic})" if topic else ""
            words_lines.append(f"<b>{en}</b>{trans_part} - {ru}{topic_part}")
        
        words_text = "\n".join(words_lines)
        await message.answer(
            f"📖 <b>Твои слова ({len(words)}):</b>\n\n{words_text}",
            parse_mode="HTML"
        )


async def button_reminders(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} clicked 'Reminders'")
    stats = db.get_reminder_stats(message.from_user.id)
    
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


async def button_morning_reminders(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} selected morning reminders")
    message_text, keyboard = reminder_system.get_morning_reminder_message(message.from_user.id)
    await message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)


async def button_evening_reminders(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} selected evening reminders")
    message_text, keyboard = reminder_system.get_evening_reminder_message(message.from_user.id)
    await message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)


async def button_stats(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} clicked stats")
    text = reminder_system.get_stats_message(message.from_user.id)
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())


async def button_help(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} clicked 'Help'")
    await cmd_help(message)


# ==================================================
# ОБРАБОТКА CALLBACK (Ответы на слова)
# ==================================================

async def handle_correct_answer(callback: types.CallbackQuery) -> None:
    """Обработка правильного ответа"""
    data = callback.data.split("_")
    word = data[1]
    user_id = int(data[2])
    
    db.mark_word_reviewed(user_id, word, correct=True)
    
    await callback.answer("✅ Правильно! Отлично! 🎉", show_alert=True)
    await callback.message.edit_text(
        f"✅ <b>Отлично!</b>\n\n"
        f"Слово <code>{word}</code> отмечено как выученное!",
        parse_mode="HTML"
    )


async def handle_wrong_answer(callback: types.CallbackQuery) -> None:
    """Обработка неправильного ответа"""
    data = callback.data.split("_")
    word = data[1]
    user_id = int(data[2])
    
    # Получаем перевод с транскрипцией
    words = db.get_user_words(user_id)
    translation = None
    transcription = None
    for w_en, w_ru, w_trans, _ in words:
        if w_en == word:
            translation = w_ru
            transcription = w_trans
            break
    
    db.mark_word_reviewed(user_id, word, correct=False)
    
    if translation:
        trans_part = f" [{transcription}]" if transcription else ""
        await callback.answer(f"Правильный ответ: {translation}", show_alert=True)
        await callback.message.edit_text(
            f"❌ <b>Неправильно!</b>\n\n"
            f"<b>{word}</b>{trans_part} = <code>{translation}</code>\n\n"
            f"Это слово нужно повторить! 📚",
            parse_mode="HTML"
        )
    else:
        await callback.answer("Слово удалено из списка", show_alert=True)


async def handle_show_answer(callback: types.CallbackQuery) -> None:
    """Показать ответ"""
    data = callback.data.split("_")
    word = data[1]
    user_id = int(data[2]) if len(data) > 2 else None
    
    # Получаем полную информацию о слове
    if user_id:
        words = db.get_user_words(user_id)
        for w_en, w_ru, w_trans, w_topic in words:
            if w_en == word:
                trans_part = f" [{w_trans}]" if w_trans else ""
                topic_part = f" (#{w_topic})" if w_topic else ""
                await callback.answer("Вот ответ! 👇", show_alert=False)
                await callback.message.edit_text(
                    f"👁️ <b>ОТВЕТ:</b>\n\n"
                    f"<b>{word}</b>{trans_part} = <code>{w_ru}</code>{topic_part}",
                    parse_mode="HTML"
                )
                return
    
    # Fallback для старого формата
    translation = "_".join(data[2:]) if len(data) > 2 else "?"
    await callback.answer("Вот ответ! 👇", show_alert=False)
    await callback.message.edit_text(
        f"👁️ <b>ОТВЕТ:</b>\n\n"
        f"<code>{word}</code> = <code>{translation}</code>",
        parse_mode="HTML"
    )


# ==================================================
# НАСТРОЙКИ
# ==================================================

async def button_settings(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} clicked 'Settings'")
    settings_text = settings_manager.get_settings_message(message.from_user.id)
    keyboard = settings_manager.get_settings_keyboard()
    
    await message.answer(settings_text, parse_mode="HTML", reply_markup=keyboard)


async def change_morning_time(message: types.Message, state: FSMContext) -> None:
    """Запрос ввода утреннего времени"""
    logger.info(f"User {message.from_user.id} clicked 'Change morning time'")
    await state.set_state(ReminderStates.waiting_for_morning_time)
    
    keyboard = settings_manager.get_time_selection_keyboard()
    await message.answer(
        "🌅 <b>УСТАНОВИТЬ УТРЕННЕЕ ВРЕМЯ</b>\n\n"
        "Выбери предложенное время или напиши своё:\n"
        "Формат: <code>HH:MM</code>\n"
        "Пример: <code>09:00</code>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_morning_time(message: types.Message, state: FSMContext) -> None:
    """Обработка ввода утреннего времени"""
    time_str = message.text.strip()
    
    # Если нажал "Назад"
    if time_str == "⬅️ Назад":
        await state.clear()
        await button_settings(message)
        return
    
    if not settings_manager.validate_time(time_str):
        await message.answer(
            "❌ Неправильный формат!\n"
            "Используй: <code>HH:MM</code>\n"
            "Пример: <code>09:00</code>",
            parse_mode="HTML"
        )
        return
    
    success = db.update_user_settings(message.from_user.id, morning_time=time_str)
    await state.clear()
    
    if success:
        await message.answer(
            f"✅ <b>Утреннее время установлено!</b>\n\n"
            f"⏰ Время: <code>{time_str} MSK</code>\n\n"
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


async def change_evening_time(message: types.Message, state: FSMContext) -> None:
    """Запрос ввода вечернего времени"""
    logger.info(f"User {message.from_user.id} clicked 'Change evening time'")
    await state.set_state(ReminderStates.waiting_for_evening_time)
    
    keyboard = settings_manager.get_time_selection_keyboard()
    await message.answer(
        "🌙 <b>УСТАНОВИТЬ ВЕЧЕРНЕЕ ВРЕМЯ</b>\n\n"
        "Выбери предложенное время или напиши своё:\n"
        "Формат: <code>HH:MM</code>\n"
        "Пример: <code>20:00</code>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_evening_time(message: types.Message, state: FSMContext) -> None:
    """Обработка ввода вечернего времени"""
    time_str = message.text.strip()
    
    # Если нажал "Назад"
    if time_str == "⬅️ Назад":
        await state.clear()
        await button_settings(message)
        return
    
    if not settings_manager.validate_time(time_str):
        await message.answer(
            "❌ Неправильный формат!\n"
            "Используй: <code>HH:MM</code>\n"
            "Пример: <code>20:00</code>",
            parse_mode="HTML"
        )
        return
    
    success = db.update_user_settings(message.from_user.id, evening_time=time_str)
    await state.clear()
    
    if success:
        await message.answer(
            f"✅ <b>Вечернее время установлено!</b>\n\n"
            f"⏰ Время: <code>{time_str} MSK</code>\n\n"
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


async def toggle_reminders(message: types.Message) -> None:
    """Включить/отключить напоминания"""
    logger.info(f"User {message.from_user.id} clicked 'Toggle reminders'")
    settings = db.get_user_settings(message.from_user.id)
    new_status = not settings["reminders_enabled"]
    
    db.update_user_settings(message.from_user.id, reminders_enabled=new_status)
    status_text = "✅ Включены" if new_status else "❌ Отключены"
    
    await message.answer(
        f"🔔 Напоминания {status_text}",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


async def go_back(message: types.Message, state: FSMContext) -> None:
    """Вернуться в главное меню"""
    logger.info(f"User {message.from_user.id} went back")
    await state.clear()
    await message.answer(
        "⬅️ Главное меню",
        reply_markup=get_main_menu()
    )


# ==================================================
# ДОБАВЛЕНИЕ СЛОВ
# ==================================================

async def handle_text(message: types.Message) -> None:
    logger.info(f"User {message.from_user.id} sent: {message.text}")
    
    # Проверка формата
    if " - " not in message.text:
        await message.answer(
            "❌ Неправильный формат!\n\n"
            "Отправь: <code>слово - перевод - транскрипция</code>\n"
            "Пример: <code>cat - кот - [kæt]</code>",
            parse_mode="HTML"
        )
        return
    
    # Парсим строку: слово - перевод - транскрипция #тема
    text = message.text.strip()
    
    # Извлекаем тему (если есть)
    topic = None
    if " #" in text:
        parts_with_topic = text.split(" #", 1)
        text = parts_with_topic[0].strip()
        topic = parts_with_topic[1].strip() if len(parts_with_topic) > 1 else None
    
    # Разбиваем на части
    parts = text.split(" - ", 2)
    word = parts[0].strip()
    translation = parts[1].strip() if len(parts) > 1 else ""
    transcription = parts[2].strip() if len(parts) > 2 else None
    
    # Базовая валидация
    if not word or not translation:
        await message.answer(
            "❌ Слово и перевод обязательны!",
            parse_mode="HTML"
        )
        return
    
    success = db.add_word(message.from_user.id, word, translation, transcription, topic)
    
    if success:
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" (#{topic})" if topic else ""
        await message.answer(
            f"✅ <b>Слово добавлено!</b>\n\n"
            f"📝 <b>{word}</b>{trans_part} - {translation}{topic_part}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⚠️ <b>Слово уже есть!</b>\n\n"
            f"📝 <code>{word}</code>",
            parse_mode="HTML"
        )


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начало"),
        BotCommand(command="help", description="Справка"),
    ]
    await bot.set_my_commands(commands)


# ==================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ==================================================

async def main() -> None:
    global db, reminder_system, scheduler, settings_manager
    
    logger.info("🤖 Starting bot...")
    
    try:
        config = get_config()
        logger.info(f"✅ Config loaded: {config.bot_username}")

        db = WordDatabase(config.database_path)
        reminder_system = ReminderSystem(db)
        settings_manager = SettingsManager(db)
        
        bot = Bot(token=config.telegram_token)
        storage = MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        
        await set_commands(bot)

        scheduler = ReminderScheduler(bot, db, reminder_system)
        scheduler.start()
        logger.info("✅ Scheduler started")

        # Регистрируем команды
        dispatcher.message.register(cmd_start, Command("start"))
        dispatcher.message.register(cmd_help, Command("help"))
        
        # Главное меню
        dispatcher.message.register(button_add_word, lambda msg: msg.text == "➕ Добавить слово")
        dispatcher.message.register(button_my_words, lambda msg: msg.text == "📖 Мои слова")
        dispatcher.message.register(button_reminders, lambda msg: msg.text == "🔔 Напоминания")
        dispatcher.message.register(button_settings, lambda msg: msg.text == "⚙️ Настройки")
        dispatcher.message.register(button_help, lambda msg: msg.text == "❓ Помощь")
        
        # Напоминания
        dispatcher.message.register(button_morning_reminders, lambda msg: msg.text == "🌅 Утренние")
        dispatcher.message.register(button_evening_reminders, lambda msg: msg.text == "🌙 Вечерние")
        dispatcher.message.register(button_stats, lambda msg: msg.text == "📊 Статистика")
        
        # Настройки
        dispatcher.message.register(
            change_morning_time, 
            lambda msg: msg.text == "🌅 Установить утреннее время"
        )
        dispatcher.message.register(
            change_evening_time,
            lambda msg: msg.text == "🌙 Установить вечернее время"
        )
        dispatcher.message.register(toggle_reminders, lambda msg: msg.text == "🔔 Вкл/Выкл напоминания")
        dispatcher.message.register(go_back, lambda msg: msg.text == "⬅️ Назад")
        
        # FSM обработчики
        dispatcher.message.register(
            handle_morning_time,
            ReminderStates.waiting_for_morning_time
        )
        dispatcher.message.register(
            handle_evening_time,
            ReminderStates.waiting_for_evening_time
        )
        
        # Callback обработчики (Inline кнопки)
        dispatcher.callback_query.register(handle_correct_answer, F.data.startswith("correct_"))
        dispatcher.callback_query.register(handle_wrong_answer, F.data.startswith("wrong_"))
        dispatcher.callback_query.register(handle_show_answer, F.data.startswith("show_"))
        
        # Добавление слов (в конце, как fallback)
        dispatcher.message.register(handle_text)
        
        register_all_handlers(dispatcher)
        logger.info("✅ Handlers registered")

        logger.info("🤖 Bot started. Polling...")
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
        
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
