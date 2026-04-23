"""
Регистрация всех обработчиков
"""

from aiogram import Dispatcher, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from src.learning_en_bot.handlers import commands, words, quiz, reminders, settings, callbacks
from src.learning_en_bot.fsm_states import ReminderStates, EditWordStates
from src.learning_en_bot.buttons.keyboards import get_main_menu


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
    
    # Команда отмены редактирования
    async def cancel_edit(message, state: FSMContext):
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
    dp.message.register(cancel_edit, Command("cancel"))
    
    # Главное меню - слова
    dp.message.register(words_handler.button_add_word, lambda msg: msg.text == "➕ Добавить")
    dp.message.register(words_handler.button_my_words, lambda msg: msg.text == "📖 Мои слова")
    dp.message.register(words_handler.button_edit_word, lambda msg: msg.text == "✏️ Редактировать")
    
    # Главное меню - тренировка
    dp.message.register(quiz_handler.button_quiz_menu, lambda msg: msg.text == "🎯 Тренировка")
    
    # Режимы тренировки
    async def handle_quiz_mode(msg):
        await quiz_handler.start_quiz_mode(msg, msg.text)
    
    dp.message.register(
        handle_quiz_mode,
        lambda msg: msg.text in ["🎯 Умная тренировка (SRS)", "🎲 Случайные слова", "⚡ Сложные слова", "✨ Новые слова"]
    )
    
    # Главное меню - напоминания (просто показывает 5 случайных слов)
    dp.message.register(reminders_handler.button_reminders, lambda msg: msg.text == "🔔 Напоминания")
    dp.message.register(reminders_handler.button_stats, lambda msg: msg.text == "📊 Статистика")
    
    # Главное меню - помощь
    dp.message.register(commands.cmd_help, lambda msg: msg.text == "❓ Помощь")
    
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
    
    # FSM обработчики для настроек (регистрируем до общего текстового handler)
    dp.message.register(
        settings_handler.handle_morning_time,
        ReminderStates.waiting_for_morning_time
    )
    dp.message.register(
        settings_handler.handle_evening_time,
        ReminderStates.waiting_for_evening_time
    )
    
    # FSM обработчики для редактирования слов
    dp.message.register(
        callbacks_handler.handle_search_query,
        EditWordStates.waiting_for_search_query
    )
    dp.message.register(
        callbacks_handler.handle_new_english,
        EditWordStates.waiting_for_new_english
    )
    dp.message.register(
        callbacks_handler.handle_new_russian,
        EditWordStates.waiting_for_new_russian
    )
    dp.message.register(
        callbacks_handler.handle_new_transcription,
        EditWordStates.waiting_for_new_transcription
    )
    dp.message.register(
        callbacks_handler.handle_new_topic,
        EditWordStates.waiting_for_new_topic
    )
    
    # Назад
    dp.message.register(settings_handler.go_back, lambda msg: msg.text == "⬅️ Назад")
    
    # Callback обработчики (Inline кнопки)
    # Викторина
    dp.callback_query.register(quiz_handler.handle_quiz_callback, F.data.startswith("quiz_"))
    
    # Пагинация (старый формат)
    dp.callback_query.register(callbacks_handler.handle_page_callback, F.data.startswith("page_"))
    
    # Пагинация слов с редактированием
    dp.callback_query.register(callbacks_handler.handle_words_page_callback, F.data.startswith("words_page_"))
    
    # Редактирование слов
    dp.callback_query.register(callbacks_handler.handle_edit_word_callback, F.data.startswith("edit_word:"))
    dp.callback_query.register(callbacks_handler.handle_edit_field_callback, F.data.startswith("edit_english:"))
    dp.callback_query.register(callbacks_handler.handle_edit_field_callback, F.data.startswith("edit_russian:"))
    dp.callback_query.register(callbacks_handler.handle_edit_field_callback, F.data.startswith("edit_transcription:"))
    dp.callback_query.register(callbacks_handler.handle_edit_field_callback, F.data.startswith("edit_topic:"))
    
    # Удаление слов
    dp.callback_query.register(callbacks_handler.handle_delete_word_callback, F.data.startswith("delete_word:"))
    dp.callback_query.register(callbacks_handler.handle_confirm_delete_callback, F.data.startswith("confirm_delete:"))
    dp.callback_query.register(callbacks_handler.handle_do_delete_callback, F.data.startswith("do_delete:"))
    
    # Назад к списку слов
    dp.callback_query.register(callbacks_handler.handle_back_to_words_callback, F.data == "back_to_words")
    
    # Новый поиск
    dp.callback_query.register(callbacks_handler.handle_new_search_callback, F.data == "new_search")
    
    # ВСЕГДА ПОСЛЕДНИМ - обработка добавления слов (fallback для текстовых сообщений)
    # Это должно быть в самом конце, чтобы не перехватывать кнопки и команды
    dp.message.register(words_handler.handle_text)