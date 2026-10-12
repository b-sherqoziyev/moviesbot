import logging
from typing import Callable, Any
from aiogram import Router, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.loader import subscription_service
from app.bot.keyboards.inline.user_keyboards import get_subscription_keyboard
from app.database.models.user import User
from app.bot.handlers.user.movie import deliver_movie_message
from app.services.movie_service import MovieService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def handle_start_command(
    message: Message,
    command: CommandObject,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """/start komandasi, referallar va deep-link kino kodlarini qabul qiluvchi handler."""
    args = command.args.strip() if command.args else None
    pending_movie_code = None

    # 1. Referal havolasini tekshirish (masalan: /start ref_5061909214)
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.replace("ref_", ""))
            user_service = UserService(session)
            # Agar yangi user bo'lsa va hali referali yo'q bo'lsa
            if not user.referrer_id and user.telegram_id != referrer_id:
                user.referrer_id = referrer_id
                await session.commit()
                logger.info(f"Foydalanuvchi {user.telegram_id} referal orqali kirdi: {referrer_id}")
        except ValueError:
            pass
        args = None
    elif args:
        # Deep-link orqali to'g'ridan-to'g'ri kino kodi kelgan (masalan: /start 1 yoki eski /start m_1)
        clean_code = args[2:].strip() if args.startswith("m_") else args.strip()
        pending_movie_code = clean_code

    # 2. Obunani tekshirish (4 bosqichli zanjir)
    is_sub, not_sub = await subscription_service.check_subscription(bot, user, session)
    if not is_sub:
        text = _("subscribe_prompt")
        reply_markup = get_subscription_keyboard(
            unsubscribed_channels=not_sub,
            user_lang=user.language_code,
            pending_code=pending_movie_code
        )
        await message.answer(text=text, reply_markup=reply_markup)
        return

    # 3. Agar obuna bo'lsa va deep-link orqali kino so'ralgan bo'lsa -> Darhol kinoni yuborish
    if pending_movie_code:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_code(pending_movie_code, telegram_id=user.telegram_id)
        if movie:
            await deliver_movie_message(bot, message.chat.id, movie, movie_service, user_lang=user.language_code)
            return
        else:
            await message.answer(text=_("movie_not_found"))
            return

    # 4. Oddiy start xabari
    welcome_text = _("welcome", name=user.first_name)
    await message.answer(text=welcome_text)
