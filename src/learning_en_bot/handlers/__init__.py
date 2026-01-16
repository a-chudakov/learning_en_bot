"""
Регистрация всех обработчиков
"""

from aiogram import Dispatcher
from aiogram.filters.command import Command
from aiogram.filters import F
from aiogram.fsm.context import FSMContext

from src.learning_en_bot.handlers import commands, words, quiz, reminders, settings, callbacks
from src.learning_en_bot.fsm_states import ReminderStates


def register_all_handlers(
    dp: Dispatcher,
    words_handler: words.WordsHandler,
    quiz_handler: quiz.QuizHandler,
    reminders_handler: reminders.RemindersHandler,
    settings_handler: settings.SettingsHandler,
    callbacks_handler: callbacks.CallbacksHandler
) -> None:
    """
    Зарегистрировать все обработчики в диспетчере
    
    Args:
        dp: Диспетчер aiogram
        words_handler: Обработчик для работы со словами
        quiz_handler: Обработчик для викторины
        reminders_handler: Обработчик для напоминаний
        settings_handler: Обработчик для настроек
        callbacks_handler: Обработчик для callback_query
    """
    
    # Команды
    dp.message.register(commands.cmd_start, Command("start"))
    dp.message.register(commands.cmd_help, Command("help"))
    
    # Главное меню - слова
    dp.message.register(words_handler.button_add_word, lambda msg: msg.text == "➕ Добавить слово")
    dp.message.register(words_handler.button_my_words, lambda msg: msg.text == "📖 Мои слова")
    dp.message.register(words_handler.handle_text)  # Обработка добавления слов (fallback)
    
    # Главное меню - тренировка
    dp.message.register(quiz_handler.button_quiz_menu, lambda msg: msg.text == "🎯 Тренировка")
    
    # Режимы тренировки
    async def handle_quiz_mode(msg):
        await quiz_handler.start_quiz_mode(msg, msg.text)
    
    dp.message.register(
        handle_quiz_mode,
        lambda msg: msg.text in ["🎯 Умная тренировка (SRS)", "🎲 Случайные слова", "⚡ Сложные слова", "✨ Новые слова"]
    )
    
    # Главное меню - напоминания
    dp.message.register(reminders_handler.button_reminders, lambda msg: msg.text == "🔔 Напоминания")
    dp.message.register(reminders_handler.button_morning_reminders, lambda msg: msg.text == "🌅 Утренние")
    dp.message.register(reminders_handler.button_evening_reminders, lambda msg: msg.text == "🌙 Вечерние")
    dp.message.register(reminders_handler.button_stats, lambda msg: msg.text == "📊 Статистика")
    
    # Главное меню - настройки
    dp.message.register(settings_handler.button_settings, lambda msg: msg.text == "⚙️ Настройки")
    dp.message.register(
        settings_handler.change_morning_time,
        lambda msg: msg.text == "🌅 Установить утреннее время"
    )
    dp.message.register(
        settings_handler.change_evening_time,
        lambda msg: msg.text == "🌙 Установить вечернее время"
    )
    dp.message.register(settings_handler.toggle_reminders, lambda msg: msg.text == "🔔 Вкл/Выкл напоминания")
    
    # FSM обработчики для настроек
    dp.message.register(
        settings_handler.handle_morning_time,
        ReminderStates.waiting_for_morning_time
    )
    dp.message.register(
        settings_handler.handle_evening_time,
        ReminderStates.waiting_for_evening_time
    )
    
    # Назад
    dp.message.register(settings_handler.go_back, lambda msg: msg.text == "⬅️ Назад")
    
    # Callback обработчики (Inline кнопки)
    # Викторина
    dp.callback_query.register(quiz_handler.handle_quiz_callback, F.data.startswith("quiz_"))
    
    # Пагинация
    dp.callback_query.register(callbacks_handler.handle_page_callback, F.data.startswith("page_"))
