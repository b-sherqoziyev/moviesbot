import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Foydalanuvchilar bilan ishlash biznes logikasi."""

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

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
        return user, is_new

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Telegram ID bo'yicha foydalanuvchini olish."""
        return await self.repo.get_by_telegram_id(telegram_id)

    async def set_language(self, telegram_id: int, language_code: str) -> bool:
        """Foydalanuvchi tilini o'zgartirish."""
        return await self.repo.update_language(telegram_id, language_code)

    async def set_active(self, telegram_id: int, is_active: bool) -> bool:
        """Foydalanuvchi faolligini yangilash."""
        return await self.repo.set_active_status(telegram_id, is_active)
