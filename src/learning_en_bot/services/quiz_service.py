"""
Сервис для интерактивной тренировки/викторины с вариантами ответа
"""

import random
from typing import List, Tuple, Optional, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.services.srs_service import SRSService


class QuizService:
    """Сервис для управления викториной с вариантами ответа"""
    
    def __init__(self, db: WordDatabase, srs_service: SRSService):
        self.db = db
        self.srs_service = srs_service
        # Храним активные сессии: {user_id: {'words': [...], 'current_index': 0, 'correct': 0, 'total': 0, 'state': 'question'/'result'}}
        self.active_sessions: Dict[int, Dict] = {}
    
    def _generate_wrong_options(
        self,
        user_id: int,
        correct_translation: str,
        count: int = 3
    ) -> List[str]:
        """
        Сгенерировать неправильные варианты ответа
        
        Args:
            user_id: ID пользователя
            correct_translation: Правильный перевод (чтобы исключить)
            count: Количество неправильных вариантов
        
        Returns:
            List неправильных переводов
        """
        # Получаем все переводы пользователя
        all_words = self.db.get_user_words(user_id)
        all_translations = [word[1] for word in all_words if word[1] != correct_translation]
        
        # Если недостаточно вариантов, используем стандартные
        if len(all_translations) < count:
            # Добавляем стандартные неправильные варианты
            standard_wrong = ["дом", "дерево", "вода", "книга", "стол", "окно", "рука", "нога"]
            standard_wrong = [w for w in standard_wrong if w != correct_translation]
            all_translations.extend(standard_wrong[:count - len(all_translations)])
        
        # Берём случайные неправильные варианты
        if len(all_translations) >= count:
            wrong_options = random.sample(all_translations, count)
        else:
            wrong_options = all_translations
        
        return wrong_options
    
    def get_current_english(self, user_id: int) -> Optional[str]:
        """Текущее слово в сессии (для коротких callback_data ≤64 байт)."""
        if user_id not in self.active_sessions:
            return None
        session = self.active_sessions[user_id]
        words = session['words']
        idx = session['current_index']
        if idx >= len(words):
            return None
        return words[idx][0]
    
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
                    "Добавь слова через ➕ Добавить",
                    None
                )
            
            # Сохраняем сессию
            self.active_sessions[user_id] = {
                'words': words,
                'current_index': 0,
                'correct': 0,
                'total': len(words),
                'mode': mode,
                'state': 'question'  # 'question' или 'result'
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
        Показать текущее слово в викторине с вариантами ответа
        
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
        correct_count = session['correct']
        total = session['total']
        
        if current_index >= len(words):
            # Тренировка завершена
            return self.finish_quiz(user_id)
        
        english, russian, transcription, topic = words[current_index]
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" <i>({topic})</i>" if topic else ""
        
        progress = f"{current_index + 1}/{total}"
        correct_rate = f"✅ Правильно: {correct_count}/{current_index}" if current_index > 0 else ""
        
        # Генерируем варианты ответа
        wrong_options = self._generate_wrong_options(user_id, russian, count=3)
        all_options = [russian] + wrong_options
        random.shuffle(all_options)  # Перемешиваем варианты
        
        # Находим индекс правильного ответа
        correct_index = all_options.index(russian)
        
        # Сохраняем правильный индекс и варианты в сессии
        session['correct_index'] = correct_index
        session['options'] = all_options
        session['state'] = 'question'
        
        # Формируем сообщение
        options_text = "\n".join([
            f"{chr(65 + i)}) <code>{option}</code>"
            for i, option in enumerate(all_options)
        ])
        
        message = (
            f"🎯 <b>ТРЕНИРОВКА</b> [{progress}]\n\n"
            f"📝 <b>Выбери правильный перевод:</b>\n\n"
            f"<b>{english}</b>{trans_part}{topic_part}\n\n"
            f"{options_text}\n\n"
            f"{correct_rate}"
        )
        
        # Создаём inline-кнопки с вариантами
        keyboard_buttons = []
        
        # Короткий callback_data (лимит Telegram 64 байта); слово берётся из сессии в handler
        for i in range(0, len(all_options), 2):
            row = []
            for j in range(i, min(i + 2, len(all_options))):
                option_letter = chr(65 + j)
                row.append(
                    InlineKeyboardButton(
                        text=f"{option_letter}) {all_options[j][:15]}",
                        callback_data=f"quiz_answer:{user_id}:{j}"
                    )
                )
            keyboard_buttons.append(row)
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="👁️ Показать ответ",
                callback_data=f"quiz_show:{user_id}"
            )
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="⏹️ Завершить",
                callback_data=f"quiz_stop:{user_id}"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        return message, keyboard
    
    def handle_answer(
        self,
        user_id: int,
        english: str,
        choice_index: int
    ) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
        """
        Обработать выбранный вариант ответа
        
        Args:
            user_id: ID пользователя
            english: Английское слово
            choice_index: Индекс выбранного варианта (0-3), -1 = "знаю", -2 = "не знаю"
        
        Returns:
            Tuple[feedback_message, next_button_keyboard]
        """
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        words = session['words']
        current_index = session['current_index']
        
        # Проверяем, что это правильное слово
        if current_index >= len(words) or words[current_index][0] != english:
            return ("❌ Ошибка: слово не совпадает", None)
        
        # Получаем текущее слово ДО обновления индекса
        english_word, russian, transcription, topic = words[current_index]
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" <i>({topic})</i>" if topic else ""
        
        # Обработка специальных случаев: -1 = "знаю", -2 = "не знаю"
        if choice_index == -1:
            # Пользователь сказал "Знаю это" после показа ответа
            is_correct = True
            session['correct'] += 1
        elif choice_index == -2:
            # Пользователь сказал "Не знал" после показа ответа
            is_correct = False
        else:
            # Обычный выбор варианта
            correct_index = session.get('correct_index', 0)
            options = session.get('options', [])
            
            # Проверяем правильность ответа
            is_correct = (choice_index == correct_index)
            
            # Обновляем статистику
            if is_correct:
                session['correct'] += 1
        
        # Обновляем в БД через SRS
        self.srs_service.update_word_after_review(user_id, english, is_correct)
        
        # Меняем состояние на 'result'
        session['state'] = 'result'
        
        # Формируем сообщение с результатом
        if is_correct:
            feedback = (
                f"✅ <b>Правильно!</b> 🎉\n\n"
                f"<b>{english}</b>{trans_part} = <code>{russian}</code>{topic_part}\n\n"
            )
        else:
            if choice_index >= 0 and choice_index < len(session.get('options', [])):
                selected_option = session['options'][choice_index]
                feedback = (
                    f"❌ <b>Неправильно!</b>\n\n"
                    f"Твой ответ: <code>{selected_option}</code>\n"
                    f"Правильный: <code>{russian}</code>{trans_part}{topic_part}\n\n"
                    f"Это слово нужно повторить! 📚\n\n"
                )
            else:
                feedback = (
                    f"❌ <b>Неправильно!</b>\n\n"
                    f"Правильный ответ: <code>{russian}</code>{trans_part}{topic_part}\n\n"
                    f"Это слово нужно повторить! 📚\n\n"
                )
        
        # Кнопка для перехода к следующему слову
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Следующее слово",
                    callback_data=f"quiz_next:{user_id}"
                )
            ]
        ])
        
        return feedback, keyboard
    
    def show_answer(self, user_id: int, english: str) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Показать ответ на слово (без выбора варианта)
        
        Returns:
            Tuple[message_text, keyboard]
        """
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        words = session['words']
        current_index = session['current_index']
        
        # Проверяем, что это правильное слово
        if current_index >= len(words) or words[current_index][0] != english:
            return ("❌ Слово не найдено", None)
        
        english_word, russian, transcription, topic = words[current_index]
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" <i>({topic})</i>" if topic else ""
        
        message = (
            f"👁️ <b>ОТВЕТ:</b>\n\n"
            f"<b>{english}</b>{trans_part} = <code>{russian}</code>{topic_part}\n\n"
            f"Запомни это слово! 📚"
        )
        
        # Короткий callback_data (лимит 64 байта)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Знаю это",
                    callback_data=f"quiz_answer:{user_id}:-1"
                ),
                InlineKeyboardButton(
                    text="❌ Не знал",
                    callback_data=f"quiz_answer:{user_id}:-2"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Следующее слово",
                    callback_data=f"quiz_next:{user_id}"
                )
            ]
        ])
        
        return message, keyboard
    
    def next_word(self, user_id: int) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
        """Перейти к следующему слову"""
        if user_id not in self.active_sessions:
            return ("❌ Сессия не найдена", None)
        
        session = self.active_sessions[user_id]
        session['current_index'] += 1
        session['state'] = 'question'
        
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
