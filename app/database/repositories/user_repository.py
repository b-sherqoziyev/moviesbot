from typing import Optional, Tuple, AsyncIterator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.user import User
from app.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Foydalanuvchilar bilan ishlovchi repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Telegram ID bo'yicha foydalanuvchini olish."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str,
        username: Optional[str] = None,
        referrer_id: Optional[int] = None,
        language_code: str = "uz"
    ) -> Tuple[User, bool]:
        """Foydalanuvchi mavjud bo'lsa olish, yo'q bo'lsa ro'yxatdan o'tkazish."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Username yoki ism o'zgargan bo'lsa yangilash
            if user.first_name != first_name or user.username != username or not user.is_active:
                user.first_name = first_name
                user.username = username
                user.is_active = True
                await self.session.commit()
            return user, False

        # Yangi foydalanuvchi yaratish
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            referrer_id=referrer_id,
            language_code=language_code
        )
        self.session.add(user)

        # Agar referal orqali kirgan bo'lsa, taklif qiluvchining hisoblagichini oshirish
        if referrer_id and referrer_id != telegram_id:
            await self.increment_referrals(referrer_id)

        await self.session.commit()
        await self.session.refresh(user)
        return user, True

    async def update_language(self, telegram_id: int, language_code: str) -> bool:
        """Foydalanuvchi tilini yangilash."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(language_code=language_code)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def set_active_status(self, telegram_id: int, is_active: bool) -> bool:
        """Foydalanuvchi faolligini o'zgartirish (masalan, botni bloklagan bo'lsa)."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_active=is_active)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def increment_referrals(self, telegram_id: int) -> None:
        """Referallar hisoblagichini 1 taga oshirish."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(referrals_count=User.referrals_count + 1)
        )
        await self.session.execute(stmt)

    async def increment_watched_movies(self, telegram_id: int) -> None:
        """Ko'rilgan filmlar hisoblagichini 1 taga oshirish."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(watched_movies_count=User.watched_movies_count + 1)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_all_active_telegram_ids_stream(self, chunk_size: int = 1000) -> AsyncIterator[list[int]]:
        """Broadcast xabar tarqatish uchun xotirani to'ldirmasdan ID larni partiya (chunk) qilib olish."""
        stmt = select(User.telegram_id).where(User.is_active == True)
        result = await self.session.stream(stmt)
        chunk = []
        async for row in result:
            chunk.append(row[0])
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk
