"""
Сервис для интерактивной тренировки/викторины
"""

from typing import List, Tuple, Optional, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.services.srs_service import SRSService


class QuizService:
    """Сервис для управления викториной"""
    
    def __init__(self, db: WordDatabase, srs_service: SRSService):
        self.db = db
        self.srs_service = srs_service
        # Храним активные сессии: {user_id: {'words': [...], 'current_index': 0, 'correct': 0, 'total': 0}}
        self.active_sessions: Dict[int, Dict] = {}
    
    def start_quiz(
        self,
        user_id: int,
        mode: str = "srs",
        limit: int = 10
    ) -> Tuple[Optional[str], Optional[InlineKeyboardMarkup]]:
        """
        Начать новую сессию викторины
        
        Args:
            user_id: ID пользователя
            mode: Режим ('srs', 'random', 'difficult', 'new')
            limit: Количество слов
        
        Returns:
            Tuple[message_text, keyboard]
        """
        try:
            if mode == "srs":
                words = self.srs_service.get_words_to_review(user_id, limit)
            elif mode == "random":
                words = self.db.get_random_words(user_id, limit)
            elif mode == "difficult":
                difficult_words = self.db.get_difficult_words(user_id, limit)
                # Преобразуем формат
                words = [(w[0], w[1], "", "") for w in difficult_words]
            elif mode == "new":
                recent_words = self.db.get_recent_words(user_id, limit)
                words = [(w[0], w[1], "", "") for w in recent_words]
            else:
                words = self.db.get_random_words(user_id, limit)
            
            if not words:
                return (
                    "❌ <b>Нет слов для тренировки!</b>\n\n"
                    "Добавь слова через ➕ Добавить слово",
                    None
                )
            
            # Сохраняем сессию
            self.active_sessions[user_id] = {
                'words': words,
                'current_index': 0,
                'correct': 0,
                'total': len(words),
                'mode': mode
            }
            
            # Показываем первое слово
            return self.show_current_word(user_id)
            
        except Exception as e:
            logger.error(f"❌ Error starting quiz: {e}", exc_info=True)
            return (
                "❌ <b>Ошибка при запуске тренировки</b>\n\n"
                "Попробуй ещё раз позже.",
                None
            )
    
    def show_current_word(self, user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Показать текущее слово в викторине
        
        Returns:
            Tuple[message_text, keyboard]
        """
        if user_id not in self.active_sessions:
            return (
                "❌ <b>Сессия не найдена</b>\n\n"
                "Начни новую тренировку через 🎯 Тренировка",
                None
            )
        
        session = self.active_sessions[user_id]
        words = session['words']
        current_index = session['current_index']
        correct = session['correct']
        total = session['total']
        
        if current_index >= len(words):
            # Тренировка завершена
            return self.finish_quiz(user_id)
        
        english, russian, transcription, topic = words[current_index]
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" <i>({topic})</i>" if topic else ""
        
        progress = f"{current_index + 1}/{total}"
        correct_rate = f"Правильно: {correct}/{current_index}" if current_index > 0 else ""
        
        message = (
            f"🎯 <b>ТРЕНИРОВКА</b> [{progress}]\n\n"
            f"📝 <b>Переведи слово:</b>\n\n"
            f"<code>{english}</code>{trans_part}{topic_part}\n\n"
            f"{correct_rate}"
        )
        
        # Создаём inline-кнопки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Знаю",
                    callback_data=f"quiz_correct_{english}_{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Не знаю",
                    callback_data=f"quiz_wrong_{english}_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁️ Показать ответ",
                    callback_data=f"quiz_show_{english}_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏹️ Завершить",
                    callback_data=f"quiz_stop_{user_id}"
                )
            ]
        ])
        
        return message, keyboard
    
    def handle_answer(
        self,
        user_id: int,
        english: str,
        correct: bool
    ) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
        """
        Обработать ответ пользователя
        
        Args:
            user_id: ID пользователя
            english: Английское слово
            correct: Был ли ответ правильным
        
        Returns:
            Tuple[feedback_message, next_word_keyboard]
        """
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        words = session['words']
        current_index = session['current_index']
        
        # Проверяем, что это правильное слово
        if current_index < len(words) and words[current_index][0] != english:
            return ("❌ Ошибка: слово не совпадает", None)
        
        # Обновляем статистику
        if correct:
            session['correct'] += 1
        
        # Обновляем в БД через SRS
        self.srs_service.update_word_after_review(user_id, english, correct)
        
        # Переходим к следующему слову
        session['current_index'] += 1
        
        # Формируем сообщение с результатом
        russian = words[current_index][1] if current_index < len(words) else ""
        transcription = words[current_index][2] if current_index < len(words) and len(words[current_index]) > 2 else ""
        
        if correct:
            feedback = f"✅ <b>Правильно!</b> 🎉\n\n"
        else:
            trans_part = f" [{transcription}]" if transcription else ""
            feedback = (
                f"❌ <b>Неправильно!</b>\n\n"
                f"Правильный ответ: <code>{russian}</code>{trans_part}\n\n"
                f"Это слово нужно повторить! 📚\n\n"
            )
        
        # Показываем следующее слово
        if session['current_index'] < len(words):
            next_msg, next_keyboard = self.show_current_word(user_id)
            return feedback + "➡️ Следующее слово:", next_keyboard
        else:
            # Тренировка завершена
            return self.finish_quiz(user_id)
    
    def show_answer(self, user_id: int, english: str) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Показать ответ на слово
        
        Returns:
            Tuple[message_text, keyboard]
        """
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        words = session['words']
        current_index = session['current_index']
        
        # Ищем слово в сессии
        word_data = None
        for i, (en, ru, trans, topic) in enumerate(words):
            if en == english and i == current_index:
                word_data = (en, ru, trans, topic)
                break
        
        if not word_data:
            return ("❌ Слово не найдено", None)
        
        en, ru, trans, topic = word_data
        trans_part = f" [{trans}]" if trans else ""
        topic_part = f" <i>({topic})</i>" if topic else ""
        
        message = (
            f"👁️ <b>ОТВЕТ:</b>\n\n"
            f"<b>{en}</b>{trans_part} = <code>{ru}</code>{topic_part}\n\n"
            f"Запомни это слово! 📚"
        )
        
        # Кнопки для продолжения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Знаю это",
                    callback_data=f"quiz_correct_{en}_{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Не знал",
                    callback_data=f"quiz_wrong_{en}_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Продолжить",
                    callback_data=f"quiz_next_{user_id}"
                )
            ]
        ])
        
        return message, keyboard
    
    def next_word(self, user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
        """Перейти к следующему слову без ответа"""
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        session['current_index'] += 1
        
        if session['current_index'] >= len(session['words']):
            return self.finish_quiz(user_id)
        
        return self.show_current_word(user_id)
    
    def finish_quiz(self, user_id: int) -> Tuple[str, None]:
        """
        Завершить викторину и показать результаты
        
        Returns:
            Tuple[results_message, None]
        """
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        correct = session['correct']
        total = session['total']
        attempted = session['current_index']
        
        percentage = int((correct / attempted * 100)) if attempted > 0 else 0
        
        # Эмодзи в зависимости от результата
        if percentage >= 80:
            emoji = "🌟"
            message_text = "Отличный результат!"
        elif percentage >= 60:
            emoji = "👍"
            message_text = "Хороший результат!"
        else:
            emoji = "💪"
            message_text = "Продолжай тренироваться!"
        
        results = (
            f"🎉 <b>ТРЕНИРОВКА ЗАВЕРШЕНА</b> {emoji}\n\n"
            f"📊 <b>Результаты:</b>\n"
            f"✅ Правильно: {correct}/{attempted}\n"
            f"📈 Точность: {percentage}%\n"
            f"📝 Всего слов: {total}\n\n"
            f"{message_text}\n\n"
            f"Хочешь ещё? 🎯"
        )
        
        # Удаляем сессию
        del self.active_sessions[user_id]
        
        return results, None
    
    def stop_quiz(self, user_id: int) -> Tuple[str, None]:
        """Остановить викторину досрочно"""
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        correct = session['correct']
        attempted = session['current_index']
        
        if attempted > 0:
            message = (
                f"⏹️ <b>ТРЕНИРОВКА ОСТАНОВЛЕНА</b>\n\n"
                f"📊 Правильно: {correct}/{attempted}\n\n"
                f"Можешь продолжить позже! 💪"
            )
        else:
            message = "⏹️ <b>ТРЕНИРОВКА ОСТАНОВЛЕНА</b>\n\nНачни новую когда будешь готов! 💪"
        
        del self.active_sessions[user_id]
        return message, None
    
    def is_quiz_active(self, user_id: int) -> bool:
        """Проверить, активна ли сессия викторины"""
        return user_id in self.active_sessions
