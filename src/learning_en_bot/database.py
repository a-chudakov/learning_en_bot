"""
Работа с базой данных (SQLite)
Включает систему отслеживания слов для напоминаний
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from loguru import logger


class WordDatabase:
    """Класс для работы с БД слов с поддержкой напоминаний"""
    
    def __init__(self, db_path: str):
        """Инициализация БД"""
        self.db_path = db_path
        # Создаём директорию для БД если её нет
        try:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"❌ Error creating database directory: {e}")
            raise
        self.init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД"""
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            logger.error(f"❌ Error connecting to database: {e}")
            raise
    
    def init_db(self) -> None:
        """Создать таблицу если её нет"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Создаём таблицу для слов с полями для напоминаний
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    english TEXT NOT NULL,
                    russian TEXT NOT NULL,
                    transcription TEXT,
                    topic TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_reviewed_at TIMESTAMP,
                    review_count INTEGER DEFAULT 0,
                    difficulty INTEGER DEFAULT 1,
                    UNIQUE(user_id, english)
                )
            """)
            
            # Таблица для тем/категорий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
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
            
            # Таблица для настроек пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    morning_time TEXT NOT NULL DEFAULT '09:00',
                    evening_time TEXT NOT NULL DEFAULT '20:00',
                    reminders_enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
            # Проверяем и добавляем недостающие колонки (миграция)
            self._migrate_db(conn)
            
            logger.info(f"✅ Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"❌ Database error during initialization: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error initializing database: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _migrate_db(self, conn: sqlite3.Connection) -> None:
        """Добавить новые колонки если их нет (миграция старой БД)"""
        try:
            cursor = conn.cursor()
            
            # Получаем информацию о таблице
            cursor.execute("PRAGMA table_info(words)")
            columns = {row[1] for row in cursor.fetchall()}
            
            # Добавляем недостающие колонки
            if "last_reviewed_at" not in columns:
                cursor.execute("ALTER TABLE words ADD COLUMN last_reviewed_at TIMESTAMP")
                logger.info("✅ Added column: last_reviewed_at")
            
            if "review_count" not in columns:
                cursor.execute("ALTER TABLE words ADD COLUMN review_count INTEGER DEFAULT 0")
                logger.info("✅ Added column: review_count")
            
            if "difficulty" not in columns:
                cursor.execute("ALTER TABLE words ADD COLUMN difficulty INTEGER DEFAULT 1")
                logger.info("✅ Added column: difficulty")
            
            if "transcription" not in columns:
                cursor.execute("ALTER TABLE words ADD COLUMN transcription TEXT")
                logger.info("✅ Added column: transcription")
            
            if "topic" not in columns:
                cursor.execute("ALTER TABLE words ADD COLUMN topic TEXT")
                logger.info("✅ Added column: topic")
            
            conn.commit()
            logger.info("✅ Database migration completed")
        except Exception as e:
            logger.error(f"❌ Error during migration: {e}")
            conn.rollback()
    
    def add_word(self, user_id: int, english: str, russian: str, transcription: str = None, topic: str = None) -> bool:
        """Добавить слово в БД"""
        if not english or not russian:
            logger.warning(f"Attempted to add empty word for user {user_id}")
            return False
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO words (user_id, english, russian, transcription, topic)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, english.lower().strip(), russian.strip(), transcription.strip() if transcription else None, topic.strip() if topic else None))
            
            conn.commit()
            logger.info(f"✅ Word added: {english} - {russian} for user {user_id}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Word already exists: {english} for user {user_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"❌ Database error adding word: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error adding word: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def get_user_words(self, user_id: int) -> List[Tuple[str, str, str, str]]:
        """Получить все слова пользователя (english, russian, transcription, topic)"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id: {user_id}")
            return []
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT english, russian, transcription, topic FROM words
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            words = cursor.fetchall()
            return words
        except sqlite3.Error as e:
            logger.error(f"❌ Database error getting words: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error getting words: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
    def get_random_words(self, user_id: int, limit: int = 5) -> List[Tuple[str, str, str, str]]:
        """Получить случайные слова для напоминания (english, russian, transcription, topic)"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id: {user_id}")
            return []
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT english, russian, transcription, topic FROM words
                WHERE user_id = ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (user_id, limit))
            
            words = cursor.fetchall()
            return words
        except sqlite3.Error as e:
            logger.error(f"❌ Database error getting random words: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error getting random words: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
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
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id: {user_id}")
            return False
        if not english or not english.strip():
            logger.warning(f"Attempted to delete empty word for user {user_id}")
            return False
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM words
                WHERE user_id = ? AND english = ?
            """, (user_id, english.lower().strip()))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logger.info(f"✅ Word deleted: {english} for user {user_id}")
            else:
                logger.warning(f"Word not found: {english} for user {user_id}")
            
            return deleted
        except sqlite3.Error as e:
            logger.error(f"❌ Database error deleting word: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error deleting word: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
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
            result = cursor.fetchone()
            total_words = result[0] if result else 0
            
            # Никогда не повторённые
            cursor.execute("""
                SELECT COUNT(*) FROM words 
                WHERE user_id = ? AND last_reviewed_at IS NULL
            """, (user_id,))
            result = cursor.fetchone()
            never_reviewed = result[0] if result else 0
            
            # Повторённые сегодня
            today = datetime.now().date()
            cursor.execute("""
                SELECT COUNT(*) FROM words 
                WHERE user_id = ? AND DATE(last_reviewed_at) = ?
            """, (user_id, today))
            result = cursor.fetchone()
            reviewed_today = result[0] if result else 0
            
            # Средняя сложность
            cursor.execute("""
                SELECT AVG(difficulty) FROM words WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            avg_difficulty = result[0] if result and result[0] else 1
            
            conn.close()
            
            # Безопасный расчёт ready_for_reminder
            ready_for_reminder = never_reviewed > 0
            if total_words > 0 and reviewed_today < total_words // 3:
                ready_for_reminder = True
            
            return {
                "total_words": total_words,
                "never_reviewed": never_reviewed,
                "reviewed_today": reviewed_today,
                "avg_difficulty": round(float(avg_difficulty), 1),
                "ready_for_reminder": ready_for_reminder
            }
        except Exception as e:
            logger.error(f"❌ Error getting reminder stats: {e}", exc_info=True)
            # Возвращаем безопасные значения вместо пустого dict
            return {
                "total_words": 0,
                "never_reviewed": 0,
                "reviewed_today": 0,
                "avg_difficulty": 1.0,
                "ready_for_reminder": False
            }

    # ==================== НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ ====================
    
    def get_user_settings(self, user_id: int) -> dict:
        """Получить настройки пользователя"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id: {user_id}")
            return {
                "morning_time": "09:00",
                "evening_time": "20:00",
                "reminders_enabled": True
            }
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT morning_time, evening_time, reminders_enabled 
                FROM user_settings 
                WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "morning_time": result[0],
                    "evening_time": result[1],
                    "reminders_enabled": bool(result[2])
                }
            else:
                # Создаём стандартные настройки
                self.update_user_settings(user_id, "09:00", "20:00", True)
                return {
                    "morning_time": "09:00",
                    "evening_time": "20:00",
                    "reminders_enabled": True
                }
        except sqlite3.Error as e:
            logger.error(f"❌ Database error getting user settings: {e}", exc_info=True)
            return {
                "morning_time": "09:00",
                "evening_time": "20:00",
                "reminders_enabled": True
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error getting user settings: {e}", exc_info=True)
            return {
                "morning_time": "09:00",
                "evening_time": "20:00",
                "reminders_enabled": True
            }
        finally:
            if conn:
                conn.close()
    
    def update_user_settings(self, user_id: int, morning_time: str = None, 
                           evening_time: str = None, reminders_enabled: bool = None) -> bool:
        """Обновить настройки пользователя"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id: {user_id}")
            return False
        
        # Валидация времени
        if morning_time and not self._validate_time_format(morning_time):
            logger.warning(f"Invalid morning_time format: {morning_time}")
            return False
        if evening_time and not self._validate_time_format(evening_time):
            logger.warning(f"Invalid evening_time format: {evening_time}")
            return False
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Получаем текущие настройки
            cursor.execute("""
                SELECT morning_time, evening_time, reminders_enabled 
                FROM user_settings 
                WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                # Обновляем существующие
                new_morning = morning_time if morning_time else result[0]
                new_evening = evening_time if evening_time else result[1]
                new_enabled = reminders_enabled if reminders_enabled is not None else bool(result[2])
                
                cursor.execute("""
                    UPDATE user_settings
                    SET morning_time = ?,
                        evening_time = ?,
                        reminders_enabled = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_morning, new_evening, int(new_enabled), user_id))
            else:
                # Создаём новые
                cursor.execute("""
                    INSERT INTO user_settings 
                    (user_id, morning_time, evening_time, reminders_enabled)
                    VALUES (?, ?, ?, ?)
                """, (user_id, 
                      morning_time or "09:00",
                      evening_time or "20:00",
                      int(reminders_enabled) if reminders_enabled is not None else 1))
            
            conn.commit()
            logger.info(f"✅ User settings updated: {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ Database error updating user settings: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error updating user settings: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def _validate_time_format(self, time_str: str) -> bool:
        """Валидация формата времени HH:MM"""
        try:
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                return False
            hours = int(parts[0])
            minutes = int(parts[1])
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except (ValueError, IndexError):
            return False
