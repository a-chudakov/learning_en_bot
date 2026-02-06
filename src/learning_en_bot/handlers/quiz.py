"""
Обработчики для интерактивной тренировки/викторины
"""

import json
from typing import Optional
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
    
    def _parse_callback_data(self, data: str) -> Optional[dict]:
        """Парсинг callback_data (короткий формат ≤64 байт + обратная совместимость)"""
        try:
            # quiz_next:user_id или quiz_stop:user_id
            if data.startswith("quiz_next:") or data.startswith("quiz_stop:"):
                parts = data.split(":", 1)
                if len(parts) == 2:
                    try:
                        user_id = int(parts[1])
                        return {'action': parts[0], 'user_id': user_id}
                    except ValueError:
                        pass
            
            # quiz_answer:user_id:choice (короткий формат; word берётся из сессии)
            if data.startswith("quiz_answer:"):
                parts = data.split(":")
                if len(parts) >= 3:
                    try:
                        user_id = int(parts[1])
                        choice = int(parts[2])
                        return {'action': 'quiz_answer', 'user_id': user_id, 'choice': choice}
                    except ValueError:
                        pass
                # Старый формат JSON (обратная совместимость)
                if len(parts) == 2:
                    try:
                        parsed = json.loads(parts[1])
                        return {'action': 'quiz_answer', **parsed}
                    except (ValueError, TypeError):
                        pass
            
            # quiz_show:user_id (короткий формат)
            if data.startswith("quiz_show:"):
                parts = data.split(":", 1)
                if len(parts) == 2:
                    try:
                        user_id = int(parts[1])
                        return {'action': 'quiz_show', 'user_id': user_id}
                    except ValueError:
                        pass
                if len(parts) == 2:
                    try:
                        parsed = json.loads(parts[1])
                        return {'action': 'quiz_show', **parsed}
                    except (ValueError, TypeError):
                        pass
            
            # Старый формат quiz_correct_ / quiz_wrong_
            if data.startswith("quiz_correct_") or data.startswith("quiz_wrong_"):
                parts = data.split("||", 2)
                if len(parts) >= 3:
                    return {
                        'action': parts[0],
                        'word': parts[1],
                        'user_id': int(parts[2]),
                        'choice': -1 if 'correct' in parts[0] else -2
                    }
            
            if data.startswith("quiz_next_") or data.startswith("quiz_stop_"):
                segs = data.split("_")
                if len(segs) >= 3:
                    try:
                        return {'action': f"quiz_{segs[1]}", 'user_id': int(segs[2])}
                    except ValueError:
                        pass
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing callback_data '{data}': {e}")
            return None
    
    async def handle_quiz_callback(self, callback: types.CallbackQuery) -> None:
        """Обработать callback от кнопок викторины"""
        user_id = callback.from_user.id
        data = callback.data
        
        try:
            parsed = self._parse_callback_data(data)
            
            if not parsed:
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return
            
            # Проверка user_id
            if parsed.get('user_id') != user_id:
                await callback.answer("❌ Доступ запрещён", show_alert=True)
                return
            
            action = parsed.get('action', '')
            word = parsed.get('word')
            choice = parsed.get('choice')
            # Короткий формат: слово берём из сессии
            if word is None and action in ("quiz_answer", "quiz_show"):
                word = self.quiz_service.get_current_english(user_id)
            
            if action == "quiz_answer":
                # Обработка выбранного варианта ответа
                if word is not None and choice is not None:
                    # Выбран конкретный вариант (0-3, -1, -2)
                    text, keyboard = self.quiz_service.handle_answer(user_id, word, choice)
                    
                    # Показываем обратную связь
                    if choice == -1:
                        await callback.answer("✅ Отлично!")
                    elif choice == -2:
                        await callback.answer("❌ Продолжай учить!")
                    elif choice >= 0:
                        # Обычный выбор варианта - ответ уже показан в сообщении
                        await callback.answer()  # Просто убираем загрузку
                    
                    if keyboard:
                        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                    else:
                        # Завершение викторины
                        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=None)
                        await callback.message.answer(
                            "⬅️ Главное меню",
                            reply_markup=get_main_menu()
                        )
            
            elif action == "quiz_show":
                # Показать ответ
                if word is not None:
                    text, keyboard = self.quiz_service.show_answer(user_id, word)
                    await callback.answer("👁️ Показан ответ")
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            
            elif action == "quiz_next":
                # Следующее слово
                text, keyboard = self.quiz_service.next_word(user_id)
                await callback.answer()
                if keyboard:
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                else:
                    # Завершение викторины
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=None)
                    await callback.message.answer(
                        "⬅️ Главное меню",
                        reply_markup=get_main_menu()
                    )
            
            elif action == "quiz_stop":
                # Остановить тренировку
                text, _ = self.quiz_service.stop_quiz(user_id)
                await callback.answer()
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=None)
                await callback.message.answer(
                    "⬅️ Главное меню",
                    reply_markup=get_main_menu()
                )
            
            # Обратная совместимость со старым форматом
            elif action == "quiz_correct_" or action == "quiz_wrong_":
                word = parsed.get('word')
                if word:
                    is_correct = 'correct' in action
                    # -1 = "знаю", -2 = "не знал"
                    text, keyboard = self.quiz_service.handle_answer(user_id, word, -1 if is_correct else -2)
                    await callback.answer("✅" if is_correct else "❌")
                    if keyboard:
                        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        
        except Exception as e:
            logger.error(f"❌ Error handling quiz callback: {e}", exc_info=True)
            await callback.answer("❌ Произошла ошибка", show_alert=True)
