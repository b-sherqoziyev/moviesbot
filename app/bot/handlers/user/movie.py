import logging
from typing import Callable
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.loader import subscription_service
from app.bot.keyboards.inline.user_keyboards import get_subscription_keyboard
from app.database.models.user import User
from app.database.models.movie import Movie
from app.services.movie_service import MovieService

logger = logging.getLogger(__name__)
router = Router(name="movie")


from app.core.emojis import emoji
from app.core.i18n import i18n
from app.services.movie_formatter import MovieFormatter


async def deliver_movie_message(
    bot: Bot,
    chat_id: int,
    movie: Movie,
    movie_service: MovieService,
    user_lang: str = "uz"
) -> None:
    """Kinoni yagona standart formatda foydalanuvchiga yuborish yordamchisi (Multi-Quality & i18n)."""
    genres = await movie_service.get_movie_genres(movie.id)
    caption = MovieFormatter.format_caption(movie, genres=genres, lang=user_lang)
    bot_info = await bot.get_me()
    media_files = await movie_service.get_movie_media_files(movie.id)

    is_fav = await movie_service.is_favorite(user_id=chat_id, movie_id=movie.id)

    # Agar bir nechta sifat varianti mavjud bo'lsa -> Sifat tanlash menyusi
    if len(media_files) > 1:
        quality_prompt = i18n.get("select_quality_prompt", user_lang)
        full_text = f"{caption}\n\n👇 <b>{quality_prompt}</b>"
        keyboard = MovieFormatter.get_quality_selection_keyboard(
            movie_id=movie.id,
            media_files=media_files,
            bot_username=bot_info.username or "moviesreel_bot",
            likes=movie.likes_count,
            dislikes=movie.dislikes_count,
            lang=user_lang,
            movie_code=movie.code,
            is_favorite=is_fav
        )
        await bot.send_message(
            chat_id=chat_id,
            text=full_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    # Faqat 1 ta sifat bo'lsa -> To'g'ridan-to'g'ri video
    keyboard = MovieFormatter.get_movie_keyboard(
        movie_id=movie.id,
        bot_username=bot_info.username or "moviesreel_bot",
        likes=movie.likes_count,
        dislikes=movie.dislikes_count,
        lang=user_lang,
        movie_code=movie.code,
        is_favorite=is_fav
    )

    if movie.file_type == "video":
        await bot.send_video(
            chat_id=chat_id,
            video=movie.file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await bot.send_document(
            chat_id=chat_id,
            document=movie.file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_movie_search(
    message: Message,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Foydalanuvchi kino kodi yoki nomini yuborganda kinoni berish yoki qidirish."""
    query = message.text.strip()

    # 1. Obunani tekshirish (4 bosqichli zanjir)
    is_sub, not_sub = await subscription_service.check_subscription(bot, user, session)
    if not is_sub:
        text = _("subscribe_prompt")
        reply_markup = get_subscription_keyboard(
            unsubscribed_channels=not_sub,
            user_lang=user.language_code,
            pending_code=query
        )
        await message.answer(text=text, reply_markup=reply_markup)
        return

    movie_service = MovieService(session)

    # 2. Kod bo'yicha qidirish (1ms)
    movie = await movie_service.get_by_code(query, telegram_id=user.telegram_id)
    if movie:
        await deliver_movie_message(bot, message.chat.id, movie, movie_service, user_lang=user.language_code)
        return

    # 3. Agar kod bo'yicha topilmasa -> Nomi bo'yicha qidirish
    movies = await movie_service.search_by_title(query, limit=5)
    if movies:
        movie_lines = []
        movie_icon = emoji.get("movie")
        search_icon = emoji.get("search")
        for i, m in enumerate(movies, 1):
            year_info = f" ({m.release_year})" if m.release_year else ""
            quality_info = f" [{m.quality}]" if m.quality else ""
            movie_lines.append(
                f"{i}. {movie_icon} <b>{m.title}</b>{year_info}{quality_info} — {_('movie_label_code')}: <code>{m.code}</code>"
            )
        list_text = "\n".join(movie_lines)
        await message.answer(text=f"{search_icon} <b>Qidiruv:</b>\n\n{list_text}")
        return

    # 4. Umuman topilmadi
    await message.answer(text=_("movie_not_found"))


@router.callback_query(F.data.startswith("check_sub"))
async def handle_check_subscription_callback(
    callback: CallbackQuery,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """'Obunani tekshirish' inline tugmasi bosilganda qayta tekshiruv."""
    pending_code = None
    parts = callback.data.split(":")
    if len(parts) > 1 and parts[1].strip():
        pending_code = parts[1].strip()

    is_sub, not_sub = await subscription_service.check_subscription(bot, user, session)

    if not is_sub:
        # Hali obuna bo'lmagan
        await callback.answer(text=_("not_subscribed_warning"), show_alert=True)
        # Tugmalarni yangilash
        reply_markup = get_subscription_keyboard(
            unsubscribed_channels=not_sub,
            user_lang=user.language_code,
            pending_code=pending_code
        )
        try:
            await callback.message.edit_reply_markup(reply_markup=reply_markup)
        except Exception:
            pass
        return

    # Barcha kanallarga a'zo bo'ldi!
    await callback.answer(text=_("subscribed_success"))
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Agar kutib turilgan kino kodi bo'lsa -> Darhol o'sha kinoni jo'natish!
    if pending_code:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_code(pending_code, telegram_id=user.telegram_id)
        if movie:
            await deliver_movie_message(bot, callback.message.chat.id, movie, movie_service, user_lang=user.language_code)
            return

    await callback.message.answer(text=_("subscribed_success"))


@router.callback_query(F.data.startswith("react:"))
async def handle_movie_reaction(
    callback: CallbackQuery,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kino like yoki dislike tugmasi bosilganda (RULES.md i18n & dynamic emojis)."""
    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    reaction_type = parts[1]
    try:
        movie_id = int(parts[2])
    except ValueError:
        return

    is_like = (reaction_type == "like")
    movie_service = MovieService(session)
    new_likes, new_dislikes = await movie_service.toggle_reaction(
        user_id=user.telegram_id,
        movie_id=movie_id,
        is_like=is_like
    )

    movie = await movie_service.repo.get_by_id(movie_id)
    is_fav = await movie_service.is_favorite(user_id=user.telegram_id, movie_id=movie_id)
    movie_code = movie.code if movie else str(movie_id)
    media_files = await movie_service.get_movie_media_files(movie_id)
    bot_info = await bot.get_me()

    if len(media_files) > 1 and not (callback.message.video or callback.message.document):
        updated_keyboard = MovieFormatter.get_quality_selection_keyboard(
            movie_id=movie_id,
            media_files=media_files,
            bot_username=bot_info.username or "moviesreel_bot",
            likes=new_likes,
            dislikes=new_dislikes,
            lang=user.language_code,
            movie_code=movie_code,
            is_favorite=is_fav
        )
    else:
        updated_keyboard = MovieFormatter.get_movie_keyboard(
            movie_id=movie_id,
            bot_username=bot_info.username or "moviesreel_bot",
            likes=new_likes,
            dislikes=new_dislikes,
            lang=user.language_code,
            movie_code=movie_code,
            is_favorite=is_fav
        )

    try:
        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception:
        pass

    msg = _("reaction_liked") if is_like else _("reaction_disliked")
    await callback.answer(text=msg)


@router.callback_query(F.data.startswith("fav:"))
async def handle_movie_favorite(
    callback: CallbackQuery,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kinoni sevimlilarga saqlash yoki o'chirish (RULES.md i18n)."""
    parts = callback.data.split(":")
    if len(parts) < 2:
        return

    try:
        movie_id = int(parts[1])
    except ValueError:
        return

    movie_service = MovieService(session)
    movie = await movie_service.repo.get_by_id(movie_id)
    if not movie:
        await callback.answer(text=_("movie_not_found"), show_alert=True)
        return

    is_added = await movie_service.toggle_favorite(
        user_id=user.telegram_id,
        movie_id=movie_id
    )

    # Tugmani real vaqtda yangilash (⭐ Saqlash <-> ✅ Saqlangan)
    bot_info = await bot.get_me()
    media_files = await movie_service.get_movie_media_files(movie_id)

    if len(media_files) > 1 and not (callback.message.video or callback.message.document):
        new_keyboard = MovieFormatter.get_quality_selection_keyboard(
            movie_id=movie_id,
            media_files=media_files,
            bot_username=bot_info.username or "moviesreel_bot",
            likes=movie.likes_count,
            dislikes=movie.dislikes_count,
            lang=user.language_code,
            movie_code=movie.code,
            is_favorite=is_added
        )
    else:
        new_keyboard = MovieFormatter.get_movie_keyboard(
            movie_id=movie_id,
            bot_username=bot_info.username or "moviesreel_bot",
            likes=movie.likes_count,
            dislikes=movie.dislikes_count,
            lang=user.language_code,
            movie_code=movie.code,
            is_favorite=is_added
        )

    try:
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    except Exception:
        pass

    alert_text = _("fav_added") if is_added else _("fav_removed")
    await callback.answer(text=alert_text, show_alert=False)


@router.callback_query(F.data.startswith("dl:"))
async def handle_movie_quality_download(
    callback: CallbackQuery,
    bot: Bot,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Foydalanuvchi tanlagan sifatdagi videoni yetkazib berish (Multi-Quality Delivery)."""
    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    try:
        movie_id = int(parts[1])
    except ValueError:
        return
    quality = parts[2]

    movie_service = MovieService(session)
    movie = await movie_service.repo.get_by_id(movie_id)
    if not movie:
        await callback.answer(text=_("movie_not_found"), show_alert=True)
        return

    media = await movie_service.get_media_by_quality(movie_id, quality)
    if not media:
        await callback.answer(text=_("movie_not_found"), show_alert=True)
        return

    genres = await movie_service.get_movie_genres(movie.id)
    caption = MovieFormatter.format_caption(movie, genres=genres, lang=user.language_code)
    bot_info = await bot.get_me()
    is_fav = await movie_service.is_favorite(user_id=user.telegram_id, movie_id=movie.id)
    keyboard = MovieFormatter.get_movie_keyboard(
        movie_id=movie.id,
        bot_username=bot_info.username or "moviesreel_bot",
        likes=movie.likes_count,
        dislikes=movie.dislikes_count,
        lang=user.language_code,
        movie_code=movie.code,
        is_favorite=is_fav
    )

    await callback.answer(text=f"{media.quality.upper()}...")
    if media.file_type == "video":
        await bot.send_video(
            chat_id=callback.message.chat.id,
            video=media.file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=media.file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.message(Command("top"))
async def handle_top_movies(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Eng ko'p ko'rilgan TOP-10 filmlar ro'yxati (Minimalist va to'g'ridan-to'g'ri havolali)."""
    movie_service = MovieService(session)
    top_movies = await movie_service.get_top_movies(limit=10)

    if not top_movies:
        await message.answer(text=_("movie_not_found"))
        return

    bot_info = await bot.get_me()
    bot_username = bot_info.username or "moviesreel_bot"
    top_icon = emoji.get("top_movies")
    views_icon = emoji.get("views")

    lines = [
        f"{top_icon} <b>{_('top_movies_title')}</b>\n"
    ]

    for i, m in enumerate(top_movies, 1):
        link = f"https://t.me/{bot_username}?start={m.code}"
        lines.append(f"{i}. <a href=\"{link}\">{m.title}</a> — {views_icon} {m.views_count}")

    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


