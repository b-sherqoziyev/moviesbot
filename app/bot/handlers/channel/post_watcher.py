import logging
from aiogram import Router, F
from aiogram.enums import ChatMemberStatus
from aiogram.types import Message, ChatJoinRequest, ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.bot.loader import subscription_service
from app.services.caption_parser import SmartCaptionParser
from app.services.movie_service import MovieService

logger = logging.getLogger(__name__)
router = Router(name="channel_post_watcher")


@router.chat_join_request()
async def handle_chat_join_request(event: ChatJoinRequest) -> None:
    """Kanalga 'Request to Join' (Qo'shilish so'rovi) yuborilganda uni Redis da qayd etish."""
    channel_id = event.chat.id
    user_id = event.from_user.id
    await subscription_service.record_join_request(channel_id, user_id)
    logger.info(f"Foydalanuvchi {user_id} kanal {channel_id} ga so'rov yubordi.")


@router.chat_member()
async def handle_chat_member_updated(event: ChatMemberUpdated) -> None:
    """Foydalanuvchi kanaldan chiqqanda uning keshini 0 soniyada o'chirish."""
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    # Agar oldin a'zo bo'lib, endi chiqqan (LEFT yoki KICKED) bo'lsa
    if old_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR) and new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        user_id = event.from_user.id
        await subscription_service.invalidate_user_cache(user_id)
        logger.info(f"Foydalanuvchi {user_id} kanaldan chiqdi, keshi darhol tozalandi.")


@router.channel_post(F.video | F.document)
async def handle_channel_movie_post(
    message: Message,
    session: AsyncSession
) -> None:
    """Kanalga kino yuklanganda avtomatik ushlab, parametrlarini aqlli ajratib bazaga saqlash (Parallel Create)."""
    # Faqat belgilangan MOVIE_CHANNEL_ID dan kelgan postlarni qabul qilish
    if settings.MOVIE_CHANNEL_ID and message.chat.id != settings.MOVIE_CHANNEL_ID:
        return

    caption = message.caption or ""
    movie_service = MovieService(session)

    # 1. Smart Caption Parser orqali barcha parametrlarni tahlil qilish
    parsed_data = SmartCaptionParser.parse(caption)

    # 2. Media fayl ma'lumotlarini olish
    if message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
        file_type = "video"
        file_size = message.video.file_size
        duration = message.video.duration
        # Agar sifat matnda yozilmagan bo'lsa, Telegram piksellaridan avtomatik aniqlash
        if not parsed_data.quality:
            parsed_data.quality = SmartCaptionParser.detect_quality_from_resolution(
                width=message.video.width,
                height=message.video.height
            )
    elif message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        file_type = "document"
        file_size = message.document.file_size
        duration = None
    else:
        return

    # 3. Bazaga kiritish yoki yangilash
    movie = await movie_service.add_or_update_movie_from_post(
        parsed_data=parsed_data,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_type=file_type,
        caption=caption,
        file_size=file_size,
        duration=duration,
        channel_id=message.chat.id,
        channel_message_id=message.message_id
    )

    logger.info(
        f"Kanal posti bazaga saqlandi: [{movie.code}] {movie.title} | "
        f"Yil: {movie.release_year} | Reyting: {movie.rating} | Sifat: {movie.quality} | Til: {movie.language}"
    )


@router.edited_channel_post(F.caption)
async def handle_edited_channel_movie_post(
    message: Message,
    session: AsyncSession
) -> None:
    """Admin kanaldagi post matnini tahrirlaganda bazadagi kinoni parallel sinxron yangilash (Parallel Update)."""
    # Faqat belgilangan MOVIE_CHANNEL_ID dan kelgan tahrirlarni qabul qilish
    if settings.MOVIE_CHANNEL_ID and message.chat.id != settings.MOVIE_CHANNEL_ID:
        return

    caption = message.caption or ""
    if not caption:
        return

    movie_service = MovieService(session)
    updated_movie = await movie_service.update_movie_caption_from_channel(
        channel_id=message.chat.id,
        channel_message_id=message.message_id,
        new_caption=caption
    )

    if updated_movie:
        logger.info(f"Kanaldagi tahrir bazaga muvaffaqiyatli sinxronlandi: [{updated_movie.code}] {updated_movie.title}")
    else:
        logger.warning(f"Kanaldagi tahrirlangan post bazadan topilmadi: {message.chat.id}:{message.message_id}")
