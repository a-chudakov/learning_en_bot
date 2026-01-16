"""
Утилиты для пагинации сообщений
"""

from typing import List, Tuple, TypeVar, Callable
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
