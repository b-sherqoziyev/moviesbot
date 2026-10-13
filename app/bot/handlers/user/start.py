import logging
from typing import Callable
from aiogram import Router, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.loader import subscription_service, redis_client
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
    state: FSMContext,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """/start komandasi, referallar va deep-link kino kodlarini qabul qiluvchi toza handler."""
    # 1. RULES.md Qoidasi: FSM Holatini tozalash (State Killer)
    await state.clear()

    args = command.args.strip() if command.args else None
    pending_movie_code = None

    # 2. Referal havolasini servis orqali tekshirish
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.replace("ref_", ""))
            user_service = UserService(session, redis_client)
            await user_service.set_referrer(user, referrer_id)
        except ValueError:
            pass
        args = None
    elif args:
        # Deep-link orqali to'g'ridan-to'g'ri kino kodi kelgan (masalan: /start 1 yoki /start m_1)
        clean_code = args[2:].strip() if args.startswith("m_") else args.strip()
        pending_movie_code = clean_code

    # 3. Obunani tekshirish
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

    # 4. Agar obuna bo'lsa va deep-link orqali kino so'ralgan bo'lsa -> Darhol kinoni yuborish
    if pending_movie_code:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_code(pending_movie_code, telegram_id=user.telegram_id)
        if movie:
            await deliver_movie_message(bot, message.chat.id, movie, movie_service, user_lang=user.language_code)
            return
        else:
            await message.answer(text=_("movie_not_found"))
            return

    # 5. Oddiy start xabari va Reply menyu
    from app.core.rbac import rbac
    from app.bot.keyboards.reply.main_keyboards import get_main_reply_keyboard

    is_admin = rbac.is_god(user.telegram_id) or user.role_id in (2, 3)
    main_kb = get_main_reply_keyboard(is_admin=is_admin, lang=user.language_code)
    welcome_text = _("welcome", name=user.first_name)
    await message.answer(text=welcome_text, reply_markup=main_kb)
