import sqlite3
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WordDatabase:
    """Класс для работы с БД слов с поддержкой напоминаний"""
    
    def __init__(self, db_path: str):
        """Инициализация БД"""
        self.db_path = db_path
        self.init_db()
    
    def init_db(self) -> None:
        """Создать таблицу если её нет"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаём таблицу для слов с полями для напоминаний
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    english TEXT NOT NULL,
                    russian TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_reviewed_at TIMESTAMP,
                    review_count INTEGER DEFAULT 0,
                    difficulty INTEGER DEFAULT 1,
                    UNIQUE(user_id, english)
                )
            """)
            
            # Таблица для отслеживания сессий напоминаний
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminder_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
    
    def add_word(self, user_id: int, english: str, russian: str) -> bool:
        """Добавить слово в БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO words (user_id, english, russian)
                VALUES (?, ?, ?)
            """, (user_id, english.lower(), russian))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Word added: {english} - {russian} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding word: {e}")
            return False
    
    def get_user_words(self, user_id: int) -> List[Tuple[str, str]]:
        """Получить все слова пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT english, russian FROM words
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            words = cursor.fetchall()
            conn.close()
            return words
        except Exception as e:
            logger.error(f"❌ Error getting words: {e}")
            return []
    
    def get_user_word_count(self, user_id: int) -> int:
        """Получить количество слов пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM words WHERE user_id = ?
            """, (user_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"❌ Error getting word count: {e}")
            return 0
    
    def delete_word(self, user_id: int, english: str) -> bool:
        """Удалить слово"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM words
                WHERE user_id = ? AND english = ?
            """, (user_id, english.lower()))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Word deleted: {english} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting word: {e}")
            return False
    
    # ==================== НАПОМИНАНИЯ ====================
    
    def get_recent_words(self, user_id: int, limit: int = 15) -> List[Tuple[str, str]]:
        """
        MODE 1: Получить последние N слов (новые)
        Для напоминания свежих слов
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT english, russian FROM words
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            words = cursor.fetchall()
            conn.close()
            return words
        except Exception as e:
            logger.error(f"❌ Error getting recent words: {e}")
            return []
    
    def get_old_words(self, user_id: int, limit: int = 15) -> List[Tuple[str, str]]:
        """
        MODE 2: Получить старые слова (не повторённые давно)
        Для напоминания забытых слов
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Берём слова, которые не повторялись или повторялись давно
            cursor.execute("""
                SELECT english, russian FROM words
                WHERE user_id = ?
                ORDER BY 
                    CASE 
                        WHEN last_reviewed_at IS NULL THEN 0
                        ELSE 1
                    END,
                    last_reviewed_at ASC,
                    created_at ASC
                LIMIT ?
            """, (user_id, limit))
            
            words = cursor.fetchall()
            conn.close()
            return words
        except Exception as e:
            logger.error(f"❌ Error getting old words: {e}")
            return []
    
    def get_difficult_words(self, user_id: int, limit: int = 15) -> List[Tuple[str, str]]:
        """
        MODE 2+: Получить сложные слова (самые тяжелые)
        Для напоминания самых сложных слов
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT english, russian FROM words
                WHERE user_id = ?
                ORDER BY difficulty DESC, review_count ASC
                LIMIT ?
            """, (user_id, limit))
            
            words = cursor.fetchall()
            conn.close()
            return words
        except Exception as e:
            logger.error(f"❌ Error getting difficult words: {e}")
            return []
    
    def mark_word_reviewed(self, user_id: int, english: str, correct: bool = True) -> bool:
        """
        Отметить слово как повторённое
        correct=True - ответ верный
        correct=False - ответ неверный (увеличивает сложность)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем текущие значения
            cursor.execute("""
                SELECT review_count, difficulty FROM words
                WHERE user_id = ? AND english = ?
            """, (user_id, english.lower()))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            review_count, difficulty = result
            
            # Обновляем сложность
            if correct:
                # Если правильный ответ - уменьшаем сложность
                new_difficulty = max(1, difficulty - 1)
            else:
                # Если неправильный - увеличиваем сложность
                new_difficulty = min(10, difficulty + 1)
            
            cursor.execute("""
                UPDATE words
                SET last_reviewed_at = CURRENT_TIMESTAMP,
                    review_count = review_count + 1,
                    difficulty = ?
                WHERE user_id = ? AND english = ?
            """, (new_difficulty, user_id, english.lower()))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Word reviewed: {english} (difficulty: {new_difficulty})")
            return True
        except Exception as e:
            logger.error(f"❌ Error marking word as reviewed: {e}")
            return False
    
    def get_reminder_stats(self, user_id: int) -> dict:
        """
        Получить статистику для напоминаний
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Всего слов
            cursor.execute("SELECT COUNT(*) FROM words WHERE user_id = ?", (user_id,))
            total_words = cursor.fetchone()[0]
            
            # Никогда не повторённые
            cursor.execute("""
                SELECT COUNT(*) FROM words 
                WHERE user_id = ? AND last_reviewed_at IS NULL
            """, (user_id,))
            never_reviewed = cursor.fetchone()[0]
            
            # Повторённые сегодня
            today = datetime.now().date()
            cursor.execute("""
                SELECT COUNT(*) FROM words 
                WHERE user_id = ? AND DATE(last_reviewed_at) = ?
            """, (user_id, today))
            reviewed_today = cursor.fetchone()[0]
            
            # Средняя сложность
            cursor.execute("""
                SELECT AVG(difficulty) FROM words WHERE user_id = ?
            """, (user_id,))
            avg_difficulty = cursor.fetchone()[0] or 1
            
            conn.close()
            
            return {
                "total_words": total_words,
                "never_reviewed": never_reviewed,
                "reviewed_today": reviewed_today,
                "avg_difficulty": round(avg_difficulty, 1),
                "ready_for_reminder": never_reviewed > 0 or reviewed_today < total_words // 3
            }
        except Exception as e:
            logger.error(f"❌ Error getting reminder stats: {e}")
            return {}
