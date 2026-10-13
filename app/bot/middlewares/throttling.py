import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Anti-Flood va Rate-Limiting middleware.
    
    Har bir foydalanuvchi so'rovlarini Redis orqali nazorat qiladi.
    Belgilangan tezlikdan oshib ketgan xabarlarni cheklaydi.
    """

    def __init__(self, redis_client: aioredis.Redis, limit_seconds: float = 0.6):
        self.redis = redis_client
        self.limit = limit_seconds

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        key = f"throttle:{user_id}"
        # setnx (set if not exists) yoki TTL bilan qulflash
        is_locked = await self.redis.get(key)
        if is_locked:
            # Agar limitdan oshsa, ogohlantirish yoki e'tiborsiz qoldirish
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("Iltimos, biroz kuting...", show_alert=False)
                except Exception:
                    pass
            logger.warning(f"Foydalanuvchi {user_id} tez-tez so'rov yuborgani sababli cheklandi (Throttled).")
            return None

        # Belgilangan muddatga kalit qo'yish
        await self.redis.set(key, "1", px=int(self.limit * 1000))
        return await handler(event, data)
