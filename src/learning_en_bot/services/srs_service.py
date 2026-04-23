"""
Сервис для алгоритма интервального повторения (Spaced Repetition System)
"""

from datetime import datetime, timedelta
from typing import List, Tuple
from loguru import logger
from src.learning_en_bot.database import WordDatabase


class SRSService:
    """Сервис для управления интервальным повторением слов"""
    
    def __init__(self, db: WordDatabase):
        self.db = db
    
    def calculate_next_review_date(
        self,
        last_reviewed: datetime,
        difficulty: int,
        correct: bool,
        streak: int = 0
    ) -> datetime:
        """
        Вычислить дату следующего повторения на основе алгоритма SRS
        
        Args:
            last_reviewed: Дата последнего повторения
            difficulty: Текущая сложность слова (1-10)
            correct: Был ли ответ правильным
            streak: Серия правильных ответов подряд
        
        Returns:
            datetime: Дата следующего повторения
        """
        if not last_reviewed:
            return datetime.now() + timedelta(days=1)
        
        if correct:
            # Если правильный ответ - увеличиваем интервал
            # Интервал растёт экспоненциально, но учитывает сложность
            base_interval = 1
            multiplier = 2.0
            
            # Учитываем streak (серию правильных ответов)
            interval_days = base_interval * (multiplier ** min(streak, 5))
            
            # Корректировка на основе сложности
            # Чем выше сложность, тем чаще нужно повторять
            difficulty_factor = max(0.5, 1.0 - (difficulty - 1) * 0.1)
            interval_days *= difficulty_factor
            
            # Ограничиваем максимальный интервал
            interval_days = min(interval_days, 365)
            
            # Минимальный интервал - 1 день
            interval_days = max(interval_days, 1)
        else:
            # Если неправильный ответ - повторить завтра
            interval_days = 1
        
        return last_reviewed + timedelta(days=int(interval_days))
    
    def get_words_to_review(self, user_id: int, limit: int = 10) -> List[Tuple[str, str, str, str]]:
        """
        Получить слова, которые нужно повторить по алгоритму SRS

        Returns:
            List[Tuple]: Список слов (english, russian, transcription, topic)
        """
        try:
            now = datetime.now()
            rows = self.db.get_words_sorted_for_srs(user_id, limit)

            words = []
            for english, russian, transcription, topic, last_reviewed, difficulty, review_count in rows:
                if last_reviewed is None:
                    words.append((english, russian, transcription or "", topic or ""))
                    continue

                last_reviewed_dt = datetime.fromisoformat(last_reviewed) if isinstance(last_reviewed, str) else last_reviewed

                if difficulty >= 7:
                    if (now - last_reviewed_dt).days >= 1:
                        words.append((english, russian, transcription or "", topic or ""))
                        continue

                base_interval = max(1, 7 - difficulty)
                if (now - last_reviewed_dt).days >= base_interval:
                    words.append((english, russian, transcription or "", topic or ""))
                    if len(words) >= limit:
                        break

            if len(words) < limit:
                random_words = self.db.get_random_words(user_id, limit - len(words))
                for word_tuple in random_words:
                    if word_tuple not in words:
                        words.append(word_tuple)
                        if len(words) >= limit:
                            break

            return words[:limit]
        except Exception as e:
            logger.error(f"❌ Error getting words to review: {e}", exc_info=True)
            return self.db.get_random_words(user_id, limit)
    
    def update_word_after_review(
        self,
        user_id: int,
        english: str,
        correct: bool
    ) -> bool:
        """
        Обновить слово после повторения с учётом SRS
        
        Args:
            user_id: ID пользователя
            english: Английское слово
            correct: Был ли ответ правильным
        
        Returns:
            bool: Успешность обновления
        """
        return self.db.mark_word_reviewed(user_id, english, correct)
    
    def get_review_stats(self, user_id: int) -> dict:
        """Получить статистику по словам, готовым к повторению"""
        return self.db.get_srs_stats(user_id, datetime.now())
