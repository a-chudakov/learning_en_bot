"""
Middleware для проверки доступа пользователя (приватный бот)
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from loguru import logger
from src.config import get_config


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки доступа к боту"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Проверить доступ пользователя"""
        config = get_config()
        
        # Если allowed_user_id не установлен - доступ открыт для всех
        if config.allowed_user_id is None:
            return await handler(event, data)
        
        # Получаем user_id из события
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        # Проверяем доступ
        if user_id and user_id != config.allowed_user_id:
            logger.warning(f"❌ Access denied for user {user_id} (allowed: {config.allowed_user_id})")
            
            # Отправляем сообщение об отказе в доступе
            if isinstance(event, Message):
                await event.answer(
                    "🔒 <b>Доступ запрещён</b>\n\n"
                    "Этот бот приватный и доступен только владельцу.",
                    parse_mode="HTML"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "🔒 Доступ запрещён",
                    show_alert=True
                )
            
            return  # Блокируем обработку
        
        # Доступ разрешён - продолжаем
        return await handler(event, data)
