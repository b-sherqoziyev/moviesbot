import logging
from typing import Callable
from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emojis import emoji
from app.bot.filters.admin import AdminPermissionFilter
from app.bot.filters.i18n import I18nButtonFilter
from app.bot.keyboards.reply.main_keyboards import get_admin_reply_keyboard, get_main_reply_keyboard
from app.database.models.user import User
from app.services.stats_service import StatsService

logger = logging.getLogger(__name__)
router = Router(name="admin_panel")
router.message.filter(AdminPermissionFilter())
router.callback_query.filter(AdminPermissionFilter())


@router.message(I18nButtonFilter("btn_manage", emoji_key="admin"))
async def open_admin_panel(
    message: Message,
    user: User,
    _: Callable[..., str]
) -> None:
    """Admin 'Boshqaruv' tugmasini bosganda reply menyuni 2:2 formatda yangilab admin panelga o'tish."""
    admin_kb = get_admin_reply_keyboard(lang=user.language_code)
    admin_icon = emoji.get("admin")
    welcome_text = f"{admin_icon} <b>{_('admin_panel_welcome')}</b>"
    await message.answer(text=welcome_text, reply_markup=admin_kb)


@router.message(I18nButtonFilter("btn_main_menu", emoji_key="back"))
async def return_to_main_menu(
    message: Message,
    user: User,
    _: Callable[..., str]
) -> None:
    """Admin panelidan asosiy 1:2:1 menyuga qaytish."""
    main_kb = get_main_reply_keyboard(is_admin=True, lang=user.language_code)
    welcome_text = _("welcome", name=user.first_name)
    await message.answer(text=welcome_text, reply_markup=main_kb)


@router.message(I18nButtonFilter("btn_stats_menu", emoji_key="stats"))
async def show_admin_system_stats(
    message: Message,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Admin panelida tizim statistikasini ko'rish."""
    stats_service = StatsService(session)
    global_stats = await stats_service.get_global_stats()

    stats_icon = emoji.get("stats")
    users_icon = emoji.get("users")
    movie_icon = emoji.get("movie")
    views_icon = emoji.get("views")

    report_lines = [
        f"{stats_icon} <b>{_('stat_admin_title')}</b>\n",
        f"{users_icon} <b>{_('stat_total_users')}:</b> {global_stats['total_users']}",
        f"{movie_icon} <b>{_('stat_total_movies')}:</b> {global_stats['total_movies']}",
        f"{views_icon} <b>{_('stat_total_views')}:</b> {global_stats['total_views']}"
    ]
    await message.answer(text="\n".join(report_lines))
