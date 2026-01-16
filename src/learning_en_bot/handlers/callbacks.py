"""
Обработчики callback_query (для пагинации и других inline-кнопок)
"""

from aiogram import types
from loguru import logger
from src.learning_en_bot.database import WordDatabase
from src.learning_en_bot.utils.pagination import paginate_words


class CallbacksHandler:
    """Обработчики callback_query"""
    
    def __init__(self, db: WordDatabase):
        self.db = db
    
    async def handle_page_callback(self, callback: types.CallbackQuery) -> None:
        """Обработать переключение страницы пагинации"""
        try:
            data = callback.data
            if data.startswith("page_"):
                page_str = data.split("_")[1]
                
                if page_str == "info":
                    await callback.answer("Это текущая страница", show_alert=False)
                    return
                
                page = int(page_str)
                user_id = callback.from_user.id
                
                words = self.db.get_user_words(user_id)
                header = f"📖 <b>Твои слова ({len(words)}):</b>\n\n"
                text, keyboard = paginate_words(words, page=page, header=header)
                
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                await callback.answer()
        
        except Exception as e:
            logger.error(f"❌ Error handling page callback: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при переключении страницы", show_alert=True)
