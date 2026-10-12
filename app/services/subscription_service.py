import logging
from typing import Tuple, List, Optional
import redis.asyncio as aioredis
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rbac import rbac
from app.database.models.channel import Channel
from app.database.models.user import User
from app.database.repositories.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)

# Redis kalitlari prefiksi
REDIS_SUB_TTL = 300  # 5 daqiqa (Oltin o'rtaliq xavfsizlik yostig'i)
REDIS_JOIN_REQ_TTL = 86400 * 7  # 7 kun


class SubscriptionService:
    """Majburiy a'zolik kanallari (Public, Private, Invite) tekshiruvi va Redis kesh xizmati."""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def get_channels_version(self) -> int:
        """Kanallar ro'yxati o'zgarganini bilish uchun Redis versiyasi."""
        ver = await self.redis.get("channels_version")
        if not ver:
            await self.redis.set("channels_version", 1)
            return 1
        return int(ver)

    async def bump_channels_version(self) -> None:
        """Admin kanal qo'shganda/o'chirganda barcha eski keshlarni 0 soniyada kuchsizlantirish."""
        await self.redis.incr("channels_version")
        await self.redis.delete("cached_active_channels")
        logger.info("Kanallar versiyasi oshirildi, barcha eski keshlar yangilandi.")

    async def invalidate_user_cache(self, telegram_id: int) -> None:
        """User kanaldan chiqqanda uning keshini darhol o'chirish."""
        ver = await self.get_channels_version()
        await self.redis.delete(f"sub:{ver}:{telegram_id}")

    async def record_join_request(self, channel_id: int, telegram_id: int) -> None:
        """User kanalga 'Request to Join' (So'rov) yuborganda Redis ga qayd etish."""
        key = f"join_req:{channel_id}:{telegram_id}"
        await self.redis.set(key, 1, ex=REDIS_JOIN_REQ_TTL)
        logger.info(f"Join request qayd etildi: user {telegram_id} -> kanal {channel_id}")

    async def has_join_request(self, channel_id: int, telegram_id: int) -> bool:
        """User ushbu kanalga so'rov yuborganmi yo'qmi tekshirish."""
        key = f"join_req:{channel_id}:{telegram_id}"
        return bool(await self.redis.get(key))

    async def check_subscription(
        self,
        bot: Bot,
        user: User,
        session: AsyncSession
    ) -> Tuple[bool, List[Channel]]:
        """Foydalanuvchining majburiy kanallarga a'zoligini 4 bosqichli zanjir orqali tekshirish.
        
        Qaytaradi:
            (is_subscribed: bool, not_subscribed_channels: List[Channel])
        """
        # 1-BOSQICH: GOD-Level (Superadmin) Bypass
        if rbac.is_god(user.telegram_id):
            return True, []

        # 2-BOSQICH: VIP Status Bypass (Imtiyoz)
        if getattr(user, "is_vip", False):
            return True, []

        # 3-BOSQICH: Redis Kesh tekshiruvi (Oxirgi 5 daqiqa ichida tekshirilgan bo'lsa)
        ver = await self.get_channels_version()
        cache_key = f"sub:{ver}:{user.telegram_id}"
        if await self.redis.get(cache_key):
            return True, []

        # 4-BOSQICH: Bazadan faol kanallarni olish
        channel_repo = ChannelRepository(session)
        channels = await channel_repo.get_active_channels()

        # Chegara holati: Bazada hali kanallar 0 ta bo'lsa -> Darhol ruxsat berish!
        if not channels:
            return True, []

        not_subscribed: List[Channel] = []

        # Har bir kanalni tekshirish
        for ch in channels:
            try:
                member = await bot.get_chat_member(chat_id=ch.channel_id, user_id=user.telegram_id)
                # A'zolik maqomlari
                if member.status in (
                    ChatMemberStatus.CREATOR,
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.MEMBER
                ):
                    continue

                # Agar oddiy a'zo bo'lmasa, lekin so'rov yuborgan (Request to join) bo'lsa-chi?
                if await self.has_join_request(ch.channel_id, user.telegram_id):
                    continue

                not_subscribed.append(ch)

            except Exception as e:
                # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa, log qilib so'rovni tekshirish
                logger.warning(f"Kanal {ch.channel_id} tekshirishda xatolik: {e}")
                if await self.has_join_request(ch.channel_id, user.telegram_id):
                    continue
                not_subscribed.append(ch)

        # Agar barcha kanallarga a'zo bo'lsa -> Redis ga 5 daqiqalik kesh qo'yish
        if not not_subscribed:
            await self.redis.set(cache_key, 1, ex=REDIS_SUB_TTL)
            return True, []

        return False, not_subscribed
