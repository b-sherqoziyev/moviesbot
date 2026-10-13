import json
import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.database.models.user import User
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

USER_CACHE_TTL = 1800  # 30 daqiqa


class UserService:
    """Foydalanuvchilar bilan ishlash biznes logikasi va Redis kesh qatlami."""

    def __init__(self, session: AsyncSession, redis_client: Optional[aioredis.Redis] = None):
        self.session = session
        self.repo = UserRepository(session)
        self.redis = redis_client

    async def get_or_create_user(
        self,
        telegram_id: int,
        first_name: str,
        username: Optional[str] = None,
        referrer_id: Optional[int] = None,
        language_code: str = "uz"
    ) -> Tuple[User, bool]:
        """Foydalanuvchini olish yoki ro'yxatdan o'tkazish.
        
        Qaytaradi:
            (User, is_new: bool)
        """
        # O'ziga o'zi referal bo'lishining oldini olish
        if referrer_id == telegram_id:
            referrer_id = None

        user, is_new = await self.repo.get_or_create(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            referrer_id=referrer_id,
            language_code=language_code
        )
        if is_new:
            logger.info(f"Yangi foydalanuvchi ro'yxatdan o'tdi: {telegram_id} (@{username})")

        # Keshni yangilash
        if self.redis:
            await self._cache_user(user)

        return user, is_new

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Telegram ID bo'yicha foydalanuvchini olish."""
        return await self.repo.get_by_telegram_id(telegram_id)

    async def set_referrer(self, user: User, referrer_id: int) -> bool:
        """Referal bog'lash amali (Faqat servis qatlamida)."""
        if user.referrer_id or user.telegram_id == referrer_id:
            return False

        user.referrer_id = referrer_id
        await self.repo.increment_referrals(referrer_id)
        await self.session.commit()
        if self.redis:
            await self._cache_user(user)
        logger.info(f"Foydalanuvchi {user.telegram_id} uchun referal bog'landi: {referrer_id}")
        return True

    async def set_language(self, telegram_id: int, language_code: str) -> bool:
        """Foydalanuvchi tilini o'zgartirish va keshni yangilash."""
        updated = await self.repo.update_language(telegram_id, language_code)
        if updated and self.redis:
            await self.redis.delete(f"user_cache:{telegram_id}")
        return updated

    async def set_active(self, telegram_id: int, is_active: bool) -> bool:
        """Foydalanuvchi faolligini yangilash."""
        updated = await self.repo.set_active_status(telegram_id, is_active)
        if updated and self.redis:
            await self.redis.delete(f"user_cache:{telegram_id}")
        return updated

    async def _cache_user(self, user: User) -> None:
        """Foydalanuvchi asosiy parametrlarini Redis ga yozish."""
        if not self.redis:
            return
        data = {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username or "",
            "language_code": user.language_code,
            "is_vip": getattr(user, "is_vip", False),
            "is_active": user.is_active,
            "referrer_id": user.referrer_id
        }
        await self.redis.set(f"user_cache:{user.telegram_id}", json.dumps(data), ex=USER_CACHE_TTL)
