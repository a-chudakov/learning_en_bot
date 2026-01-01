import sqlite3
import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class WordDatabase:
    """Класс для работы с БД слов"""
    
    def __init__(self, db_path: str):
        """Инициализация БД"""
        self.db_path = db_path
        self.init_db()
    
    def init_db(self) -> None:
        """Создать таблицу если её нет"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаём таблицу для слов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    english TEXT NOT NULL,
                    russian TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, english)
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
