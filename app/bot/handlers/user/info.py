import logging
from typing import Callable
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.core.rbac import rbac
from app.core.emojis import emoji
from app.database.models.user import User
from app.database.models.movie import Movie
from app.database.models.reaction import Favorite

logger = logging.getLogger(__name__)
router = Router(name="user_info")


@router.message(Command("stat", "status"))
async def handle_stat_command(
    message: Message,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Foydalanuvchining shaxsiy va adminlar uchun bot statistikasi (Minimalist UI)."""
    # 1. Shaxsiy statistika
    ref_stmt = select(func.count(User.id)).where(User.referrer_id == user.telegram_id)
    ref_res = await session.execute(ref_stmt)
    ref_count = ref_res.scalar() or 0

    fav_stmt = select(func.count(Favorite.id)).where(Favorite.user_id == user.telegram_id)
    fav_res = await session.execute(fav_stmt)
    fav_count = fav_res.scalar() or 0

    lang_map = {
        "uz": f"O'zbekcha {emoji.get('flag_uz')}",
        "ru": f"Русский {emoji.get('flag_ru')}",
        "en": f"English {emoji.get('flag_en')}"
    }
    lang_display = lang_map.get(user.language_code, user.language_code)

    stats_icon = emoji.get("stats")
    user_icon = emoji.get("user")
    users_icon = emoji.get("users")
    star_icon = emoji.get("star")
    lang_icon = emoji.get("language")
    code_icon = emoji.get("code")
    admin_icon = emoji.get("admin")

    pcs = _("unit_pcs")
    times = _("movie_label_times")

    lines = [
        f"{stats_icon} <b>{_('stat_personal_title')}</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"{user_icon} <b>{_('stat_name')}:</b> {user.first_name}",
        f"{code_icon} <b>ID:</b> <code>{user.telegram_id}</code>",
        f"{users_icon} <b>{_('stat_referrals')}:</b> {ref_count}{pcs}",
        f"{star_icon} <b>{_('stat_favorites')}:</b> {fav_count}{pcs}",
        f"{lang_icon} <b>{_('stat_language')}:</b> {lang_display}"
    ]

    # 2. Faqat haqiqiy Admin yoki God bo'lsa -> Tizim statistikasini qo'shish (stats.view huquqi)
    if rbac.is_god(user.telegram_id) or rbac.has_permission(user.telegram_id, user.role_id, "stats.view"):
        total_users_stmt = select(func.count(User.id))
        total_users_res = await session.execute(total_users_stmt)
        total_users = total_users_res.scalar() or 0

        total_movies_stmt = select(func.count(Movie.id)).where(Movie.is_active == True)
        total_movies_res = await session.execute(total_movies_stmt)
        total_movies = total_movies_res.scalar() or 0

        total_views_stmt = select(func.sum(Movie.views_count)).where(Movie.is_active == True)
        total_views_res = await session.execute(total_views_stmt)
        total_views = total_views_res.scalar() or 0

        movie_icon = emoji.get("movie")
        views_icon = emoji.get("views")

        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            f"{admin_icon} <b>{_('stat_admin_title')}</b>",
            f"{users_icon} {_('stat_total_users')}: <b>{total_users}{pcs}</b>",
            f"{movie_icon} {_('stat_total_movies')}: <b>{total_movies}{pcs}</b>",
            f"{views_icon} {_('stat_total_views')}: <b>{total_views} {times}</b>"
        ])

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("help"))
async def handle_help_command(
    message: Message,
    _: Callable[..., str]
) -> None:
    """Foydalanuvchilar uchun qisqa, minimalist va qulay qo'llanma."""
    help_icon = emoji.get("help")
    popcorn_icon = emoji.get("popcorn")
    channel_icon = emoji.get("broadcast")

    channel_info = ""
    clean_ch = settings.main_channel_username
    if clean_ch:
        channel_info = f"\n━━━━━━━━━━━━━━━━━━━━\n{channel_icon} <b>{_('movie_label_channel')}:</b> <a href=\"https://t.me/{clean_ch}\">@{clean_ch}</a>"

    text = (
        f"{help_icon} <b>{_('help_title')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{popcorn_icon} <b>{_('help_how_to')}</b>\n"
        f"• {_('help_by_code')}\n"
        f"• {_('help_by_title')}\n\n"
        f"⚡️ <b>{_('help_commands')}</b>\n"
        f"/start — {_('help_cmd_start')}\n"
        f"/top — {_('help_cmd_top')}\n"
        f"/stat — {_('help_cmd_stat')}\n"
        f"/language — {_('help_cmd_lang')}\n"
        f"/help — {_('help_cmd_help')}"
        f"{channel_info}"
    )
    await message.answer(text, parse_mode="HTML")
