import logging
from typing import Callable
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.emojis import emoji
from app.bot.filters.admin import AdminPermissionFilter
from app.bot.states.admin_states import AdminMovieStates
from app.database.models.movie import Movie
from app.database.models.user import User
from app.services.movie_service import MovieService
from app.services.movie_formatter import MovieFormatter

logger = logging.getLogger(__name__)
router = Router(name="admin_movies")
router.message.filter(AdminPermissionFilter("movies.manage"))
router.callback_query.filter(AdminPermissionFilter("movies.manage"))


from app.bot.filters.i18n import I18nButtonFilter


async def render_movies_menu(
    session: AsyncSession,
    _: Callable[..., str],
    bot_username: str | None = None
) -> tuple[str, InlineKeyboardMarkup]:
    """Admin kinolar bo'limi matni va boshqaruv inline tugmalarini tayyorlash (DRY)."""
    movie_service = MovieService(session)
    count_stmt = select(func.count(Movie.id)).where(Movie.is_active == True)
    count_res = await session.execute(count_stmt)
    total_count = count_res.scalar() or 0

    top_movies = await movie_service.get_top_movies(limit=5)
    movie_icon = emoji.get("movie")
    stats_icon = emoji.get("stats")

    lines = [
        f"{movie_icon} <b>{_('admin_movies_title')}</b>",
        f"{stats_icon} {_('admin_movies_total', count=total_count)}\n",
        f"<b>{_('admin_movies_top')}</b>"
    ]

    for i, m in enumerate(top_movies, start=1):
        if bot_username:
            link = f"https://t.me/{bot_username}?start={m.code}"
            lines.append(f'{i}. <a href="{link}">{m.title}</a> (<code>{m.code}</code>) — 👁 {m.views_count}')
        else:
            lines.append(f"{i}. <b>{m.title}</b> (<code>{m.code}</code>) — 👁 {m.views_count}")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Film tafsiloti", callback_data="admin_movie_info_ask"),
                InlineKeyboardButton(text="🗑 Filmni o'chirish", callback_data="admin_movie_del_ask")
            ]
        ]
    )
    return "\n".join(lines), markup


@router.message(I18nButtonFilter("btn_movies_manage", emoji_key="movie"))
async def show_admin_movies_menu(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Admin panelida kinolar bo'limi boshqaruvi."""
    bot_info = await bot.get_me()
    text, markup = await render_movies_menu(session, _, bot_username=bot_info.username)
    await message.answer(
        text=text,
        reply_markup=markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )



@router.callback_query(F.data == "admin_movie_info_ask")
async def cb_movie_info_ask(callback: CallbackQuery, state: FSMContext, _: Callable[..., str]) -> None:
    """Film tafsilotini ko'rish uchun kod so'rash."""
    await state.set_state(AdminMovieStates.waiting_for_info_code)
    cancel_btn = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn_cancel"), callback_data="admin_movie_cancel")]]
    )
    await callback.message.edit_text(
        text="ℹ️ Ma'lumot olmoqchi bo'lgan film kodini yuboring (masalan: 1):",
        reply_markup=cancel_btn
    )
    await callback.answer()


@router.callback_query(F.data == "admin_movie_del_ask")
async def cb_movie_del_ask(callback: CallbackQuery, state: FSMContext, _: Callable[..., str]) -> None:
    """Filmni o'chirish uchun kod so'rash."""
    await state.set_state(AdminMovieStates.waiting_for_del_code)
    cancel_btn = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn_cancel"), callback_data="admin_movie_cancel")]]
    )
    await callback.message.edit_text(
        text="⚠️ O'chirmoqchi bo'lgan film kodini yuboring (masalan: 1):",
        reply_markup=cancel_btn
    )
    await callback.answer()


@router.callback_query(F.data == "admin_movie_cancel")
async def cb_movie_cancel(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kino amallarini bekor qilish va asosiy kino menyusiga qaytish."""
    await state.clear()
    await callback.answer("Amal bekor qilindi.")
    bot_info = await bot.get_me()
    text, markup = await render_movies_menu(session, _, bot_username=bot_info.username)
    await callback.message.edit_text(
        text=text,
        reply_markup=markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )




@router.message(AdminMovieStates.waiting_for_info_code)
async def process_movie_info_code(
    message: Message,
    state: FSMContext,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Admin kiritgan kod bo'yicha film ma'lumotini chiqarish."""
    code = message.text.strip().upper()
    await state.clear()

    movie_service = MovieService(session)
    movie = await movie_service.repo.get_by_code(code)
    if not movie:
        err_icon = emoji.get("error")
        await message.answer(f"{err_icon} <code>{code}</code> — {_('movie_not_found')}")
        return

    genres = await movie_service.get_movie_genres(movie.id, lang=user.language_code)
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
    calendar_icon = emoji.get("calendar")

    info_text = (
        f"{stats_icon} <b>{_('admin_movie_info_title')}</b>\n\n"
        f"{movie_icon} <b>{_('movie_label_desc')}:</b> {movie.title}\n"
        f"{code_icon} <b>{_('movie_label_code')}:</b> <code>{movie.code}</code>\n"
        f"{calendar_icon} <b>{_('movie_label_year')}:</b> {movie.release_year or '—'}\n"
        f"{star_icon} <b>{_('movie_label_rating')}:</b> {movie.rating or '—'}\n"
        f"{country_icon} <b>{_('movie_label_country')}:</b> {movie.country or '—'}\n"
        f"{speech_icon} <b>{_('movie_label_language')}:</b> {movie.language or '—'}\n"
        f"{quality_icon} <b>{_('movie_label_quality')}:</b> {movie.quality or '—'}\n"
        f"{genre_icon} <b>{_('movie_label_genre')}:</b> {', '.join(genres) if genres else '—'}\n"
        f"{dur_icon} <b>{_('movie_label_duration')}:</b> {duration_str}\n"
        f"{pkg_icon} <b>{_('movie_label_size')}:</b> {size_str}\n\n"
        f"{views_icon} <b>{_('movie_label_views')}:</b> {movie.views_count}\n"
        f"{like_icon} <b>{_('movie_label_likes')}:</b> {movie.likes_count}\n"
        f"{dislike_icon} <b>{_('movie_label_dislikes')}:</b> {movie.dislikes_count}\n"
        f"{fav_icon} <b>{_('movie_label_favorites')}:</b> {movie.favorites_count}\n"
        f"{broadcast_icon} <b>{_('movie_label_post_id')}:</b> {movie.channel_message_id or '—'}"
    )
    await message.answer(info_text)
    text, markup = await render_movies_menu(session, _)
    await message.answer(text=text, reply_markup=markup, parse_mode="HTML")



@router.message(AdminMovieStates.waiting_for_del_code)
async def process_movie_del_code(
    message: Message,
    state: FSMContext,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Admin kiritgan kod bo'yicha filmni bazadan va kanaldan o'chirish."""
    code = message.text.strip().upper()
    await state.clear()

    movie_service = MovieService(session)
    movie = await movie_service.repo.get_by_code(code)
    if not movie:
        err_icon = emoji.get("error")
        await message.answer(f"{err_icon} <code>{code}</code> — {_('movie_not_found')}")
        return

    # Kanaldan postni o'chirish
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

    # Bazada soft delete
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
    text, markup = await render_movies_menu(session, _)
    await message.answer(text=text, reply_markup=markup, parse_mode="HTML")

