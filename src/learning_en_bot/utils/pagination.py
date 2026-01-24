"""
Утилиты для пагинации сообщений
"""

from typing import List, Tuple, TypeVar, Callable, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

T = TypeVar('T')


class Paginator:
    """Класс для пагинации списков"""
    
    def __init__(
        self,
        items: List[T],
        items_per_page: int = 10,
        format_func: Callable[[T, int], str] = None
    ):
        """
        Args:
            items: Список элементов для пагинации
            items_per_page: Количество элементов на странице
            format_func: Функция для форматирования элемента (item, index) -> str
        """
        self.items = items
        self.items_per_page = items_per_page
        self.format_func = format_func or (lambda item, idx: str(item))
        self.total_pages = max(1, (len(items) + items_per_page - 1) // items_per_page)
    
    def get_page(self, page: int = 0) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Получить страницу с элементами
        
        Args:
            page: Номер страницы (начиная с 0)
        
        Returns:
            Tuple[text, keyboard]
        """
        page = max(0, min(page, self.total_pages - 1))
        start = page * self.items_per_page
        end = start + self.items_per_page
        
        page_items = self.items[start:end]
        
        # Формируем текст
        lines = []
        for i, item in enumerate(page_items, start=start + 1):
            lines.append(f"{i}. {self.format_func(item, i - 1)}")
        
        text = "\n".join(lines)
        
        # Формируем клавиатуру для навигации
        keyboard_buttons = []
        
        if self.total_pages > 1:
            nav_row = []
            
            # Кнопка "Назад"
            if page > 0:
                nav_row.append(
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=f"page_{page - 1}"
                    )
                )
            
            # Индикатор страницы
            nav_row.append(
                InlineKeyboardButton(
                    text=f"{page + 1}/{self.total_pages}",
                    callback_data="page_info"
                )
            )
            
            # Кнопка "Вперёд"
            if page < self.total_pages - 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text="Вперёд ▶️",
                        callback_data=f"page_{page + 1}"
                    )
                )
            
            keyboard_buttons.append(nav_row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
        
        return text, keyboard
    
    @staticmethod
    def format_word(word_tuple: Tuple[str, str, str, str], index: int) -> str:
        """Форматирование слова для пагинатора"""
        english, russian, transcription, topic = word_tuple
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" (#{topic})" if topic else ""
        return f"<b>{english}</b>{trans_part} - {russian}{topic_part}"
    
    @staticmethod
    def format_word_with_id(word_tuple: Tuple[int, str, str, str, str], index: int) -> str:
        """Форматирование слова с ID для пагинатора"""
        word_id, english, russian, transcription, topic = word_tuple
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" (#{topic})" if topic else ""
        return f"<b>{english}</b>{trans_part} - {russian}{topic_part}"


def paginate_words(
    words: List[Tuple[str, str, str, str]],
    page: int = 0,
    items_per_page: int = 10,
    header: str = "📖 <b>Твои слова:</b>\n\n"
) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Пагинация списка слов
    
    Args:
        words: Список слов (english, russian, transcription, topic)
        page: Номер страницы
        items_per_page: Элементов на странице
        header: Заголовок сообщения
    
    Returns:
        Tuple[text, keyboard]
    """
    paginator = Paginator(words, items_per_page, Paginator.format_word)
    text, keyboard = paginator.get_page(page)
    
    total = len(words)
    footer = f"\n\n<b>Всего слов: {total}</b>"
    
    return header + text + footer, keyboard


def paginate_words_simple(
    words: List[Tuple[str, str, str, str]],
    page: int = 0,
    items_per_page: int = 50,
    header: str = "📖 <b>Твои слова:</b>\n\n"
) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Простая пагинация списка слов (текст без кнопок редактирования)
    
    Args:
        words: Список слов (english, russian, transcription, topic)
        page: Номер страницы
        items_per_page: Элементов на странице
        header: Заголовок сообщения
    
    Returns:
        Tuple[text, keyboard]
    """
    if not words:
        return header + "Пока нет добавленных слов.", None
    
    total_pages = max(1, (len(words) + items_per_page - 1) // items_per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * items_per_page
    end = start + items_per_page
    
    page_items = words[start:end]
    
    # Формируем текст - компактный список
    lines = []
    for i, (english, russian, transcription, topic) in enumerate(page_items, start=start + 1):
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" #{topic}" if topic else ""
        lines.append(f"{i}. <b>{english}</b>{trans_part} — {russian}{topic_part}")
    
    text = "\n".join(lines)
    
    # Навигация только если больше 1 страницы
    keyboard_buttons = []
    if total_pages > 1:
        nav_row = []
        
        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"words_page_{page - 1}"
                )
            )
        
        nav_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="page_info"
            )
        )
        
        if page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="Вперёд ▶️",
                    callback_data=f"words_page_{page + 1}"
                )
            )
        
        keyboard_buttons.append(nav_row)
    
    footer = f"\n\n<i>Всего: {len(words)} | Для редактирования: ✏️ Редактировать</i>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
    return header + text + footer, keyboard


def format_search_results(
    words: List[Tuple[int, str, str, str, str]],
    query: str
) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Форматирование результатов поиска с кнопками редактирования
    
    Args:
        words: Список слов (id, english, russian, transcription, topic)
        query: Поисковый запрос
    
    Returns:
        Tuple[text, keyboard]
    """
    if not words:
        return (
            f"🔍 По запросу «<b>{query}</b>» ничего не найдено.\n\n"
            f"Попробуй другой запрос или проверь написание.",
            None
        )
    
    # Формируем текст
    lines = [f"🔍 Найдено по запросу «<b>{query}</b>»:\n"]
    for i, (word_id, english, russian, transcription, topic) in enumerate(words, 1):
        trans_part = f" [{transcription}]" if transcription else ""
        topic_part = f" #{topic}" if topic else ""
        lines.append(f"{i}. <b>{english}</b>{trans_part} — {russian}{topic_part}")
    
    text = "\n".join(lines)
    
    # Кнопки для каждого слова
    keyboard_buttons = []
    for word_id, english, russian, transcription, topic in words:
        display_text = english[:20] + "…" if len(english) > 20 else english
        row = [
            InlineKeyboardButton(
                text=f"✏️ {display_text}",
                callback_data=f"edit_word:{word_id}"
            ),
            InlineKeyboardButton(
                text="🗑️",
                callback_data=f"delete_word:{word_id}"
            )
        ]
        keyboard_buttons.append(row)
    
    # Кнопка нового поиска
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return text, keyboard


def get_edit_word_keyboard(word_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования слова"""
    buttons = [
        [InlineKeyboardButton(text="✏️ Изменить слово/фразу", callback_data=f"edit_english:{word_id}")],
        [InlineKeyboardButton(text="✏️ Изменить перевод", callback_data=f"edit_russian:{word_id}")],
        [InlineKeyboardButton(text="✏️ Изменить транскрипцию", callback_data=f"edit_transcription:{word_id}")],
        [InlineKeyboardButton(text="✏️ Изменить тему", callback_data=f"edit_topic:{word_id}")],
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"confirm_delete:{word_id}"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_words")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_confirm_keyboard(word_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"do_delete:{word_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"edit_word:{word_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
