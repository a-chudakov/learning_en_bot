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
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество слов
        
        Returns:
            List[Tuple]: Список слов (english, russian, transcription, topic)
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            
            # Получаем слова, которые нужно повторить:
            # 1. Слова, которые никогда не повторялись (last_reviewed_at IS NULL)
            # 2. Слова, у которых next_review_date <= now (или не установлена)
            # 3. Слова с высокой сложностью, которые давно не повторялись
            cursor.execute("""
                SELECT english, russian, transcription, topic, 
                       last_reviewed_at, difficulty, review_count
                FROM words
                WHERE user_id = ?
                ORDER BY 
                    CASE 
                        WHEN last_reviewed_at IS NULL THEN 0
                        WHEN difficulty >= 7 THEN 1
                        WHEN difficulty >= 5 THEN 2
                        ELSE 3
                    END,
                    last_reviewed_at ASC NULLS FIRST,
                    difficulty DESC,
                    created_at ASC
                LIMIT ?
            """, (user_id, limit))
            
            words = []
            for row in cursor.fetchall():
                english, russian, transcription, topic, last_reviewed, difficulty, review_count = row
                
                # Если слово никогда не повторялось - точно включить
                if last_reviewed is None:
                    words.append((english, russian, transcription or "", topic or ""))
                    continue
                
                # Вычисляем, нужно ли повторить
                last_reviewed_dt = datetime.fromisoformat(last_reviewed) if isinstance(last_reviewed, str) else last_reviewed
                
                # Для слов с высокой сложностью - показывать чаще
                if difficulty >= 7:
                    days_since_review = (now - last_reviewed_dt).days
                    if days_since_review >= 1:  # Повторять каждый день
                        words.append((english, russian, transcription or "", topic or ""))
                        continue
                
                # Для остальных - использовать базовый интервал
                days_since_review = (now - last_reviewed_dt).days
                # Базовый интервал: 1 день для сложных, 3 дня для средних, 7 для лёгких
                base_interval = max(1, 7 - difficulty)
                if days_since_review >= base_interval:
                    words.append((english, russian, transcription or "", topic or ""))
                    if len(words) >= limit:
                        break
            
            conn.close()
            
            # Если не хватает слов, добавляем случайные новые
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
            # Fallback на случайные слова
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
        """
        Получить статистику по словам, готовым к повторению
        
        Returns:
            dict: Статистика
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            
            # Слова, которые нужно повторить
            cursor.execute("""
                SELECT COUNT(*) FROM words
                WHERE user_id = ? 
                AND (last_reviewed_at IS NULL OR 
                     (julianday(?) - julianday(last_reviewed_at)) >= 1)
            """, (user_id, now))
            ready_to_review = cursor.fetchone()[0] or 0
            
            # Слова с высокой сложностью
            cursor.execute("""
                SELECT COUNT(*) FROM words
                WHERE user_id = ? AND difficulty >= 7
            """, (user_id,))
            difficult_words = cursor.fetchone()[0] or 0
            
            # Никогда не повторённые
            cursor.execute("""
                SELECT COUNT(*) FROM words
                WHERE user_id = ? AND last_reviewed_at IS NULL
            """, (user_id,))
            never_reviewed = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "ready_to_review": ready_to_review,
                "difficult_words": difficult_words,
                "never_reviewed": never_reviewed
            }
        except Exception as e:
            logger.error(f"❌ Error getting review stats: {e}", exc_info=True)
            return {
                "ready_to_review": 0,
                "difficult_words": 0,
                "never_reviewed": 0
            }
