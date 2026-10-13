from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.channel import Channel
from app.database.repositories.base import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    """Majburiy a'zolik homiy kanallari bilan ishlovchi repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(Channel, session)

    async def get_active_channels(self) -> List[Channel]:
        """Barcha faol kanallarni prioriteti bo'yicha saralab olish."""
        stmt = (
            select(Channel)
            .where(Channel.is_active == True)
            .order_by(Channel.priority.desc(), Channel.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_channels(self) -> List[Channel]:
        """Barcha kanallarni (faol va nofaol) ro'yxatini olish."""
        stmt = (
            select(Channel)
            .order_by(Channel.priority.desc(), Channel.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


    async def get_by_channel_id(self, channel_id: int) -> Optional[Channel]:
        """Kanal ID si bo'yicha qidirish."""
        stmt = select(Channel).where(Channel.channel_id == channel_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def toggle_active(self, channel_id: int, is_active: bool, admin_id: int) -> bool:
        """Kanal faolligini o'zgartirish."""
        stmt = (
            update(Channel)
            .where(Channel.channel_id == channel_id)
            .values(is_active=is_active, updated_by=admin_id)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
