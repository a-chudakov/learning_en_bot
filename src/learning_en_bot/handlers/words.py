"""
Обработчики для работы со словами (добавление, просмотр)
"""

from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.utils.pagination import paginate_words_simple
from src.learning_en_bot.fsm_states import EditWordStates


class WordsHandler:
    """Обработчики для работы со словами"""
    
    def __init__(self, db: WordDatabase):
        self.db = db
    
    async def button_add_word(self, message: types.Message) -> None:
        """Показать инструкцию по добавлению слова или фразы"""
        logger.info(f"User {message.from_user.id} clicked 'Add word'")
        await message.answer(
            "📝 <b>Добавление слова или фразы</b>\n\n"
            "Формат:\n"
            "<code>слово/фраза - перевод - транскрипция</code>\n\n"
            "<b>Примеры слов:</b>\n"
            "<code>cat - кот - [kæt]</code>\n"
            "<code>hello - привет</code>\n\n"
            "<b>Примеры фраз:</b>\n"
            "<code>a black cat - чёрная кошка</code>\n"
            "<code>to be honest - честно говоря</code>\n"
            "<code>break a leg - удачи! (идиома)</code>\n\n"
            "💡 Можно добавить тему через #:\n"
            "<code>break a leg - удачи - #idioms</code>",
            parse_mode="HTML"
        )
    
    async def button_my_words(self, message: types.Message, page: int = 0) -> None:
        """Показать слова пользователя (простой список)"""
        logger.info(f"User {message.from_user.id} clicked 'My words', page {page}")
        words = self.db.get_user_words(message.from_user.id)
        
        if not words:
            await message.answer(
                "📖 <b>Твои слова:</b>\n\nПока нет добавленных слов.\n\n"
                "Нажми «➕ Добавить» чтобы начать!",
                parse_mode="HTML"
            )
        else:
            header = f"📖 <b>Твои слова ({len(words)}):</b>\n\n"
            text, keyboard = paginate_words_simple(words, page=page, header=header)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def button_edit_word(self, message: types.Message, state: FSMContext) -> None:
        """Начать поиск слова для редактирования"""
        logger.info(f"User {message.from_user.id} clicked 'Edit word'")
        
        word_count = self.db.get_user_word_count(message.from_user.id)
        
        if word_count == 0:
            await message.answer(
                "✏️ <b>Редактирование</b>\n\n"
                "У тебя пока нет слов для редактирования.\n"
                "Сначала добавь слова через «➕ Добавить»",
                parse_mode="HTML"
            )
            return
        
        await state.set_state(EditWordStates.waiting_for_search_query)
        await message.answer(
            "🔍 <b>Поиск слова для редактирования</b>\n\n"
            "Введи слово или часть слова/фразы для поиска.\n"
            "Можно искать на русском или английском.\n\n"
            "Например: <code>cat</code> или <code>кот</code>\n\n"
            "<i>Для отмены отправь /cancel</i>",
            parse_mode="HTML"
        )
    
    async def handle_text(self, message: types.Message) -> None:
        """Обработать добавление слова из текста"""
        logger.info(f"User {message.from_user.id} sent: {message.text}")
        
        # Пропускаем команды и кнопки (они обрабатываются другими handlers)
        if not message.text or " - " not in message.text:
            # Если это не формат слова и не команда - игнорируем
            return
        
        # Парсим строку: слово - перевод - транскрипция #тема
        text = message.text.strip()
        
        # Извлекаем тему (если есть)
        topic = None
        if " #" in text:
            parts_with_topic = text.split(" #", 1)
            text = parts_with_topic[0].strip()
            topic = parts_with_topic[1].strip() if len(parts_with_topic) > 1 else None
        
        # Разбиваем на части (минимум 2 части: слово и перевод)
        parts = [p.strip() for p in text.split(" - ")]
        
        if len(parts) < 2:
            await message.answer(
                "❌ Неправильный формат!\n\n"
                "Отправь: <code>слово - перевод</code>\n"
                "Или: <code>слово - перевод - транскрипция</code>\n\n"
                "Примеры:\n"
                "• <code>cat - кот</code>\n"
                "• <code>cat - кот - kæt</code>\n"
                "• <code>cat - кот - [kæt]</code>",
                parse_mode="HTML"
            )
            return
        
        word = parts[0]
        translation = parts[1]
        
        # Транскрипция опциональна (3-я часть или пустая)
        transcription = None
        if len(parts) > 2:
            transcription = parts[2]
            # Убираем квадратные скобки если есть (принимаем в любом формате)
            if transcription.startswith("[") and transcription.endswith("]"):
                transcription = transcription[1:-1].strip()
        
        # Базовая валидация
        if not word or not translation:
            await message.answer(
                "❌ Слово и перевод обязательны!",
                parse_mode="HTML"
            )
            return
        
        success = self.db.add_word(message.from_user.id, word, translation, transcription, topic)
        
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
