"""
Обработчики для интерактивной тренировки/викторины
"""

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from loguru import logger
from src.learning_en_bot.services.quiz_service import QuizService
from src.learning_en_bot.buttons.keyboards import get_main_menu


class QuizHandler:
    """Обработчики для викторины"""
    
    def __init__(self, quiz_service: QuizService):
        self.quiz_service = quiz_service
    
    async def button_quiz_menu(self, message: types.Message) -> None:
        """Показать меню выбора режима тренировки"""
        logger.info(f"User {message.from_user.id} clicked 'Quiz'")
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎯 Умная тренировка (SRS)")],
                [KeyboardButton(text="🎲 Случайные слова")],
                [KeyboardButton(text="⚡ Сложные слова")],
                [KeyboardButton(text="✨ Новые слова")],
                [KeyboardButton(text="⬅️ Назад")],
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            "🎯 <b>ВЫБЕРИ РЕЖИМ ТРЕНИРОВКИ</b>\n\n"
            "• <b>Умная тренировка</b> - слова, которые нужно повторить\n"
            "• <b>Случайные слова</b> - любой набор слов\n"
            "• <b>Сложные слова</b> - слова с высокой сложностью\n"
            "• <b>Новые слова</b> - недавно добавленные",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def start_quiz_mode(self, message: types.Message, mode: str) -> None:
        """Начать тренировку в определённом режиме"""
        user_id = message.from_user.id
        mode_map = {
            "🎯 Умная тренировка (SRS)": "srs",
            "🎲 Случайные слова": "random",
            "⚡ Сложные слова": "difficult",
            "✨ Новые слова": "new"
        }
        
        quiz_mode = mode_map.get(mode, "srs")
        logger.info(f"User {user_id} starting quiz in mode {quiz_mode}")
        
        text, keyboard = self.quiz_service.start_quiz(user_id, mode=quiz_mode, limit=10)
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def handle_quiz_callback(self, callback: types.CallbackQuery) -> None:
        """Обработать callback от кнопок викторины"""
        user_id = callback.from_user.id
        data = callback.data
        
        try:
            if data.startswith("quiz_correct_"):
                # Правильный ответ
                parts = data.split("_")
                if len(parts) >= 4:
                    english = parts[2]
                    cb_user_id = int(parts[3])
                    if cb_user_id == user_id:
                        text, keyboard = self.quiz_service.handle_answer(user_id, english, correct=True)
                        await callback.answer("✅ Правильно!")
                        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            
            elif data.startswith("quiz_wrong_"):
                # Неправильный ответ
                parts = data.split("_")
                if len(parts) >= 4:
                    english = parts[2]
                    cb_user_id = int(parts[3])
                    if cb_user_id == user_id:
                        text, keyboard = self.quiz_service.handle_answer(user_id, english, correct=False)
                        await callback.answer("❌ Неправильно")
                        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            
            elif data.startswith("quiz_show_"):
                # Показать ответ
                parts = data.split("_")
                if len(parts) >= 4:
                    english = parts[2]
                    cb_user_id = int(parts[3])
                    if cb_user_id == user_id:
                        text, keyboard = self.quiz_service.show_answer(user_id, english)
                        await callback.answer("👁️ Показан ответ")
                        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            
            elif data.startswith("quiz_next_"):
                # Следующее слово
                cb_user_id = int(data.split("_")[2])
                if cb_user_id == user_id:
                    text, keyboard = self.quiz_service.next_word(user_id)
                    await callback.answer()
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            
            elif data.startswith("quiz_stop_"):
                # Остановить тренировку
                cb_user_id = int(data.split("_")[2])
                if cb_user_id == user_id:
                    text, _ = self.quiz_service.stop_quiz(user_id)
                    await callback.answer()
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=None)
                    await callback.message.answer(
                        "⬅️ Главное меню",
                        reply_markup=get_main_menu()
                    )
        
        except Exception as e:
            logger.error(f"❌ Error handling quiz callback: {e}", exc_info=True)
            await callback.answer("❌ Произошла ошибка", show_alert=True)
