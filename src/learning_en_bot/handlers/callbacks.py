"""
Обработчики callback_query (для пагинации и других inline-кнопок)
"""

from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.utils.pagination import (
    paginate_words_simple, 
    format_search_results,
    get_edit_word_keyboard,
    get_delete_confirm_keyboard
)
from src.learning_en_bot.fsm_states import EditWordStates


class CallbacksHandler:
    """Обработчики callback_query"""
    
    def __init__(self, db: WordDatabase):
        self.db = db
    
    async def handle_page_callback(self, callback: types.CallbackQuery) -> None:
        """Обработать переключение страницы пагинации (старый формат)"""
        try:
            data = callback.data
            if data.startswith("page_"):
                page_str = data.split("_")[1]
                
                if page_str == "info":
                    await callback.answer("Это текущая страница", show_alert=False)
                    return
                
                page = int(page_str)
                user_id = callback.from_user.id
                
                words = self.db.get_user_words(user_id)
                header = f"📖 <b>Твои слова ({len(words)}):</b>\n\n"
                text, keyboard = paginate_words_simple(words, page=page, header=header)
                
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                await callback.answer()
        
        except Exception as e:
            logger.error(f"❌ Error handling page callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при переключении страницы", show_alert=True)
    
    async def handle_words_page_callback(self, callback: types.CallbackQuery) -> None:
        """Обработать переключение страницы списка слов"""
        try:
            data = callback.data
            page = int(data.split("_")[2])
            user_id = callback.from_user.id
            
            words = self.db.get_user_words(user_id)
            header = f"📖 <b>Твои слова ({len(words)}):</b>\n\n"
            text, keyboard = paginate_words_simple(words, page=page, header=header)
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer()
        
        except Exception as e:
            logger.error(f"❌ Error handling words page callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def handle_new_search_callback(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Начать новый поиск"""
        await state.set_state(EditWordStates.waiting_for_search_query)
        await callback.message.edit_text(
            "🔍 <b>Поиск слова для редактирования</b>\n\n"
            "Введи слово или часть слова/фразы для поиска.\n\n"
            "<i>Для отмены отправь /cancel</i>",
            parse_mode="HTML"
        )
        await callback.answer()
    
    async def handle_search_query(self, message: types.Message, state: FSMContext) -> None:
        """Обработать поисковый запрос"""
        query = message.text.strip()
        user_id = message.from_user.id
        
        if len(query) < 1:
            await message.answer("Введи хотя бы 1 символ для поиска")
            return
        
        await state.clear()
        
        words = self.db.search_words(user_id, query, limit=10)
        text, keyboard = format_search_results(words, query)
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def handle_edit_word_callback(self, callback: types.CallbackQuery) -> None:
        """Показать меню редактирования слова"""
        try:
            word_id = int(callback.data.split(":")[1])
            user_id = callback.from_user.id
            
            word = self.db.get_word_by_id(user_id, word_id)
            if not word:
                await callback.answer("❌ Слово не найдено", show_alert=True)
                return
            
            trans_part = f" [{word['transcription']}]" if word['transcription'] else ""
            topic_part = f"\n🏷️ Тема: #{word['topic']}" if word['topic'] else ""
            
            text = (
                f"✏️ <b>Редактирование</b>\n\n"
                f"🇬🇧 <b>{word['english']}</b>{trans_part}\n"
                f"🇷🇺 {word['russian']}{topic_part}\n\n"
                f"Выбери, что изменить:"
            )
            
            keyboard = get_edit_word_keyboard(word_id)
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer()
        
        except Exception as e:
            logger.error(f"❌ Error handling edit word callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def handle_edit_field_callback(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Начать редактирование конкретного поля"""
        try:
            data = callback.data
            parts = data.split(":")
            field = parts[0].replace("edit_", "")  # english, russian, transcription, topic
            word_id = int(parts[1])
            user_id = callback.from_user.id
            
            word = self.db.get_word_by_id(user_id, word_id)
            if not word:
                await callback.answer("❌ Слово не найдено", show_alert=True)
                return
            
            # Сохраняем word_id в состояние
            await state.update_data(editing_word_id=word_id)
            
            field_names = {
                "english": ("слово/фразу", word['english'], EditWordStates.waiting_for_new_english),
                "russian": ("перевод", word['russian'], EditWordStates.waiting_for_new_russian),
                "transcription": ("транскрипцию", word['transcription'] or "не указана", EditWordStates.waiting_for_new_transcription),
                "topic": ("тему", word['topic'] or "не указана", EditWordStates.waiting_for_new_topic)
            }
            
            if field not in field_names:
                await callback.answer("❌ Неизвестное поле", show_alert=True)
                return
            
            name, current, next_state = field_names[field]
            
            await state.set_state(next_state)
            
            text = (
                f"✏️ <b>Редактирование</b>\n\n"
                f"Текущее значение: <code>{current}</code>\n\n"
                f"Отправь новое значение для поля «{name}»\n"
                f"или /cancel для отмены"
            )
            
            await callback.message.edit_text(text, parse_mode="HTML")
            await callback.answer()
        
        except Exception as e:
            logger.error(f"❌ Error handling edit field callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def handle_delete_word_callback(self, callback: types.CallbackQuery) -> None:
        """Показать подтверждение удаления (быстрое)"""
        try:
            word_id = int(callback.data.split(":")[1])
            user_id = callback.from_user.id
            
            word = self.db.get_word_by_id(user_id, word_id)
            if not word:
                await callback.answer("❌ Слово не найдено", show_alert=True)
                return
            
            text = (
                f"🗑️ <b>Удалить слово?</b>\n\n"
                f"<b>{word['english']}</b> - {word['russian']}"
            )
            
            keyboard = get_delete_confirm_keyboard(word_id)
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer()
        
        except Exception as e:
            logger.error(f"❌ Error handling delete word callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def handle_confirm_delete_callback(self, callback: types.CallbackQuery) -> None:
        """Подтвердить удаление из меню редактирования"""
        await self.handle_delete_word_callback(callback)
    
    async def handle_do_delete_callback(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Выполнить удаление слова"""
        try:
            word_id = int(callback.data.split(":")[1])
            user_id = callback.from_user.id
            
            success = self.db.delete_word_by_id(user_id, word_id)
            
            if success:
                await callback.answer("✅ Слово удалено", show_alert=False)
                # Предлагаем новый поиск
                await state.set_state(EditWordStates.waiting_for_search_query)
                await callback.message.edit_text(
                    "✅ <b>Слово удалено!</b>\n\n"
                    "🔍 Введи запрос для поиска другого слова\n"
                    "или нажми кнопку в меню.",
                    parse_mode="HTML"
                )
            else:
                await callback.answer("❌ Ошибка при удалении", show_alert=True)
        
        except Exception as e:
            logger.error(f"❌ Error handling do delete callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def handle_back_to_words_callback(self, callback: types.CallbackQuery, state: FSMContext) -> None:
        """Вернуться к поиску слов"""
        try:
            await state.set_state(EditWordStates.waiting_for_search_query)
            await callback.message.edit_text(
                "🔍 <b>Поиск слова для редактирования</b>\n\n"
                "Введи слово или часть слова/фразы для поиска.\n\n"
                "<i>Для отмены отправь /cancel</i>",
                parse_mode="HTML"
            )
            await callback.answer()
        
        except Exception as e:
            logger.error(f"❌ Error handling back to words callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка", show_alert=True)
    
    # Обработчики FSM для редактирования полей
    async def handle_new_english(self, message: types.Message, state: FSMContext) -> None:
        """Обработать новое значение английского слова/фразы"""
        await self._update_word_field(message, state, "english")
    
    async def handle_new_russian(self, message: types.Message, state: FSMContext) -> None:
        """Обработать новое значение перевода"""
        await self._update_word_field(message, state, "russian")
    
    async def handle_new_transcription(self, message: types.Message, state: FSMContext) -> None:
        """Обработать новое значение транскрипции"""
        await self._update_word_field(message, state, "transcription")
    
    async def handle_new_topic(self, message: types.Message, state: FSMContext) -> None:
        """Обработать новое значение темы"""
        await self._update_word_field(message, state, "topic")
    
    async def _update_word_field(self, message: types.Message, state: FSMContext, field: str) -> None:
        """Обновить поле слова"""
        try:
            data = await state.get_data()
            word_id = data.get("editing_word_id")
            
            if not word_id:
                await message.answer("❌ Ошибка: слово не найдено")
                await state.clear()
                return
            
            new_value = message.text.strip()
            
            # Убираем квадратные скобки из транскрипции
            if field == "transcription" and new_value.startswith("[") and new_value.endswith("]"):
                new_value = new_value[1:-1].strip()
            
            # Убираем # из темы
            if field == "topic" and new_value.startswith("#"):
                new_value = new_value[1:].strip()
            
            user_id = message.from_user.id
            
            # Обновляем только нужное поле
            update_kwargs = {field: new_value}
            success = self.db.update_word(user_id, word_id, **update_kwargs)
            
            await state.clear()
            
            if success:
                word = self.db.get_word_by_id(user_id, word_id)
                if word:
                    trans_part = f" [{word['transcription']}]" if word['transcription'] else ""
                    topic_part = f"\n🏷️ Тема: #{word['topic']}" if word['topic'] else ""
                    
                    text = (
                        f"✅ <b>Обновлено!</b>\n\n"
                        f"🇬🇧 <b>{word['english']}</b>{trans_part}\n"
                        f"🇷🇺 {word['russian']}{topic_part}\n\n"
                        f"Выбери, что ещё изменить:"
                    )
                    
                    keyboard = get_edit_word_keyboard(word_id)
                    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await message.answer("✅ Обновлено!")
            else:
                await message.answer(
                    "❌ Ошибка при обновлении.\n"
                    "Возможно, такое слово уже существует."
                )
        
        except Exception as e:
            logger.error(f"❌ Error updating word field: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка")
            await state.clear()
