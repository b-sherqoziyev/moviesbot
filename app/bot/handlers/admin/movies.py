import logging
from typing import Callable
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.rbac import rbac
from app.core.emojis import emoji
from app.database.models.movie import Movie
from app.database.models.user import User
from app.services.movie_service import MovieService
from app.services.movie_formatter import MovieFormatter

logger = logging.getLogger(__name__)
router = Router(name="admin_movies")


@router.message(Command("del", "delete"))
async def handle_delete_movie(
    message: Message,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kinoni o'chirish: Bazada nofaol qilish VA kanaldagi postni ham parallel o'chirish."""
    # 1. Huquqni tekshirish (Stealth/Ghost mode: oddiy userlar uchun indamay e'tiborsiz qoldiriladi)
    if not (rbac.is_god(user.telegram_id) or rbac.has_permission(user.telegram_id, user.role_id, "movies.delete")):
        return


    # 2. Argumentni olish (/del 122)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        warn_icon = emoji.get("warning")
        await message.answer(f"{warn_icon} {_('admin_movie_del_format')}")
        return

    code_to_delete = args[1].strip().upper()
    movie_service = MovieService(session)
    movie = await movie_service.repo.get_by_code(code_to_delete)

    if not movie:
        err_icon = emoji.get("error")
        await message.answer(f"{err_icon} <code>{code_to_delete}</code> — {_('movie_not_found')}")
        return

    # 3. Agar kanalda post bo'lsa -> Kanaldagi postni ham parallel o'chirish!
    deleted_from_channel = False
    if movie.channel_id and movie.channel_message_id:
        try:
            await bot.delete_message(
                chat_id=movie.channel_id,
                message_id=movie.channel_message_id
            )
            deleted_from_channel = True
        except Exception as e:
            logger.warning(f"Kanaldagi postni o'chirishda xatolik: {e}")

    # 4. Bazada Soft-Delete qilish
    await movie_service.repo.soft_delete(movie.id, admin_id=user.telegram_id)

    del_icon = emoji.get("delete")
    movie_icon = emoji.get("movie")
    code_icon = emoji.get("code")
    check_icon = emoji.get("check")
    warn_icon = emoji.get("warning")

    channel_status = (
        f"{check_icon} {_('admin_movie_channel_deleted')}"
        if deleted_from_channel
        else f"{warn_icon} {_('admin_movie_channel_failed')}"
    )

    await message.answer(
        f"{del_icon} <b>{_('admin_movie_deleted')}</b>\n\n"
        f"{movie_icon} {_('movie_label_desc')}: <b>{movie.title}</b>\n"
        f"{code_icon} {_('movie_label_code')}: <code>{movie.code}</code>\n"
        f"{channel_status}"
    )


@router.message(Command("movie"))
async def handle_admin_movie_info(
    message: Message,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kino haqida to'liq admin ma'lumotlarini ko'rish (RULES.md i18n & dynamic emojis)."""
    # 1. Huquqni tekshirish (Stealth/Ghost mode: oddiy userlar uchun indamay e'tiborsiz qoldiriladi)
    if not (rbac.is_god(user.telegram_id) or rbac.has_permission(user.telegram_id, user.role_id, "movies.manage")):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        warn_icon = emoji.get("warning")
        await message.answer(f"{warn_icon} {_('admin_movie_info_format')}")
        return

    code = args[1].strip().upper()
    movie_service = MovieService(session)
    movie = await movie_service.repo.get_by_code(code)

    if not movie:
        err_icon = emoji.get("error")
        await message.answer(f"{err_icon} <code>{code}</code> — {_('movie_not_found')}")
        return

    genres = await movie_service.get_movie_genres(movie.id)
    duration_str = MovieFormatter.format_duration(movie.duration) or "—"
    size_str = MovieFormatter.format_size(movie.file_size) or "—"

    stats_icon = emoji.get("stats")
    movie_icon = emoji.get("movie")
    code_icon = emoji.get("code")
    star_icon = emoji.get("star")
    country_icon = emoji.get("country")
    speech_icon = emoji.get("speech")
    quality_icon = emoji.get("quality")
    genre_icon = emoji.get("genre")
    dur_icon = emoji.get("duration")
    pkg_icon = emoji.get("package")
    views_icon = emoji.get("views")
    like_icon = emoji.get("like")
    dislike_icon = emoji.get("dislike")
    fav_icon = emoji.get("favorite")
    broadcast_icon = emoji.get("broadcast")

    info_text = (
        f"{stats_icon} <b>{_('admin_movie_info_title')}</b>\n\n"
        f"{movie_icon} <b>{_('movie_label_desc')}:</b> {movie.title}\n"
        f"{code_icon} <b>{_('movie_label_code')}:</b> <code>{movie.code}</code>\n"
        f"📅 <b>Yili:</b> {movie.release_year or '—'}\n"
        f"{star_icon} <b>{_('movie_label_rating')}:</b> {movie.rating or '—'}\n"
        f"{country_icon} <b>{_('movie_label_country')}:</b> {movie.country or '—'}\n"
        f"{speech_icon} <b>{_('movie_label_language')}:</b> {movie.language or '—'}\n"
        f"{quality_icon} <b>{_('movie_label_quality')}:</b> {movie.quality or '—'}\n"
        f"{genre_icon} <b>{_('movie_label_genre')}:</b> {', '.join(genres) if genres else '—'}\n"
        f"{dur_icon} <b>{_('movie_label_duration')}:</b> {duration_str}\n"
        f"{pkg_icon} <b>{_('movie_label_size')}:</b> {size_str}\n\n"
        f"{views_icon} <b>{_('movie_label_views')}:</b> {movie.views_count}\n"
        f"{like_icon} <b>Layklar:</b> {movie.likes_count}\n"
        f"{dislike_icon} <b>Dislayklar:</b> {movie.dislikes_count}\n"
        f"{fav_icon} <b>Sevimlilar:</b> {movie.favorites_count}\n"
        f"{broadcast_icon} <b>Kanal post ID:</b> {movie.channel_message_id or '—'}"
    )
    await message.answer(info_text)


@router.message(Command("movies"))
async def handle_admin_movies_list(
    message: Message,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kinolar umumiy statistikasi (RULES.md i18n & dynamic emojis)."""
    # 1. Huquqni tekshirish (Stealth/Ghost mode: oddiy userlar uchun indamay e'tiborsiz qoldiriladi)
    if not (rbac.is_god(user.telegram_id) or rbac.has_permission(user.telegram_id, user.role_id, "stats.view")):
        return

    stmt = select(func.count(Movie.id)).where(Movie.is_active == True)
    res = await session.execute(stmt)
    total_active = res.scalar() or 0

    movie_service = MovieService(session)
    top_movies = await movie_service.get_top_movies(limit=10)

    bot_info = await bot.get_me()
    bot_username = bot_info.username or "moviesreel_bot"

    movie_icon = emoji.get("movie")
    top_icon = emoji.get("top_movies")
    views_icon = emoji.get("views")

    lines = [
        f"{movie_icon} {_('admin_movies_total', count=total_active)}\n",
        f"{top_icon} <b>{_('admin_movies_top')}</b>"
    ]
    for i, m in enumerate(top_movies, 1):
        link = f"https://t.me/{bot_username}?start={m.code}"
        lines.append(f"{i}. <a href=\"{link}\">{m.title}</a> — {views_icon} {m.views_count}")

    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)
