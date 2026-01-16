"""
Обработчики для работы со словами (добавление, просмотр)
"""

from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.utils.pagination import paginate_words


class WordsHandler:
    """Обработчики для работы со словами"""
    
    def __init__(self, db: WordDatabase):
        self.db = db
    
    async def button_add_word(self, message: types.Message) -> None:
        """Показать инструкцию по добавлению слова"""
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
    
    async def button_my_words(self, message: types.Message, page: int = 0) -> None:
        """Показать слова пользователя с пагинацией"""
        logger.info(f"User {message.from_user.id} clicked 'My words', page {page}")
        words = self.db.get_user_words(message.from_user.id)
        
        if not words:
            await message.answer(
                "📖 <b>Твои слова:</b>\n\nПока нет добавленных слов.",
                parse_mode="HTML"
            )
        else:
            header = f"📖 <b>Твои слова ({len(words)}):</b>\n\n"
            text, keyboard = paginate_words(words, page=page, header=header)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def handle_text(self, message: types.Message) -> None:
        """Обработать добавление слова из текста"""
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
