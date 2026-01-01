import logging
from typing import List, Tuple
from src.learning_en_bot.database import WordDatabase

logger = logging.getLogger(__name__)


class ReminderSystem:
    """Система напоминаний со смарт-выбором слов"""
    
    def __init__(self, db: WordDatabase):
        self.db = db
    
    def get_reminder_mode_recommendation(self, user_id: int) -> str:
        """
        Рекомендовать оптимальный режим напоминания
        """
        stats = self.db.get_reminder_stats(user_id)
        
        if stats["total_words"] == 0:
            return "no_words"
        
        # Если много новых слов - начинаем с них
        if stats["never_reviewed"] >= 10:
            return "mode_1_recent"
        
        # Если уже знаем новые - повторяем старые
        if stats["never_reviewed"] < 5 and stats["total_words"] > 15:
            return "mode_2_old"
        
        # Если есть сложные слова - тренируем их
        if stats["avg_difficulty"] > 3:
            return "mode_2_difficult"
        
        # По умолчанию - новые слова
        return "mode_1_recent"
    
    def get_reminder_words(self, user_id: int, mode: str = None, limit: int = 10) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Получить слова для напоминания в зависимости от режима
        
        Returns:
            (mode_description, words_list)
        """
        if mode is None:
            mode = self.get_reminder_mode_recommendation(user_id)
        
        stats = self.db.get_reminder_stats(user_id)
        
        if stats["total_words"] == 0:
            return ("❌ Нет добавленных слов", [])
        
        # MODE 1: Новые слова
        if mode == "mode_1_recent":
            words = self.db.get_recent_words(user_id, limit)
            description = f"📝 <b>НОВЫЕ СЛОВА ({len(words)})</b>\n\nПовторяем последние добавленные:"
            return (description, words)
        
        # MODE 2: Старые слова
        elif mode == "mode_2_old":
            words = self.db.get_old_words(user_id, limit)
            description = f"🔄 <b>ПОВТОРЕНИЕ СТАРЫХ ({len(words)})</b>\n\nЭти слова давно не повторялись:"
            return (description, words)
        
        # MODE 2: Сложные слова
        elif mode == "mode_2_difficult":
            words = self.db.get_difficult_words(user_id, limit)
            description = f"⚡ <b>ТРЕНИРОВКА СЛОЖНЫХ ({len(words)})</b>\n\nСамые трудные для тебя слова:"
            return (description, words)
        
        # MODE MIXED: Комбинированный
        elif mode == "mode_mixed":
            recent = self.db.get_recent_words(user_id, limit // 2)
            old = self.db.get_old_words(user_id, limit // 2)
            words = recent + old
            description = f"🎯 <b>КОМБИНИРОВАННОЕ ПОВТОРЕНИЕ ({len(words)})</b>\n\nНовые и старые слова вместе:"
            return (description, words)
        
        else:
            return ("❌ Неизвестный режим", [])
    
    def format_reminder_message(self, description: str, words: List[Tuple[str, str]]) -> str:
        """
        Форматировать красивое сообщение напоминания
        """
        if not words:
            return f"{description}\n\n❌ Нет слов для этого режима"
        
        words_text = "\n".join([
            f"<code>{i+1}.</code> <code>{en}</code> - <code>{ru}</code>"
            for i, (en, ru) in enumerate(words)
        ])
        
        message = f"{description}\n\n{words_text}"
        return message
    
    def get_stats_message(self, user_id: int) -> str:
        """
        Получить сообщение со статистикой
        """
        stats = self.db.get_reminder_stats(user_id)
        
        if stats["total_words"] == 0:
            return "📊 <b>Статистика</b>\n\nПока нет слов 🙁"
        
        message = (
            f"📊 <b>Твоя статистика</b>\n\n"
            f"📝 <b>Всего слов:</b> {stats['total_words']}\n"
            f"✨ <b>Никогда не повторённых:</b> {stats['never_reviewed']}\n"
            f"🎯 <b>Повторено сегодня:</b> {stats['reviewed_today']}\n"
            f"⚡ <b>Средняя сложность:</b> {stats['avg_difficulty']}/10\n\n"
        )
        
        if stats['ready_for_reminder']:
            message += "✅ <b>Готово к напоминаниям!</b>"
        else:
            message += "⏳ Продолжай добавлять слова для лучшего обучения"
        
        return message
