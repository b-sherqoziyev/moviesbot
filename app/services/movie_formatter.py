import math
from typing import Optional, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.config import settings
from app.core.emojis import emoji
from app.core.i18n import i18n
from app.database.models.movie import Movie, MovieMedia


class MovieFormatter:
    """Kinoni foydalanuvchiga yagona, standart va chiroyli formatda
    chiqarib beruvchi generator (Outbound Presenter).
    
    RULES.md qoidalariga binoan:
    - Barcha emojilar `emoji.get()` va `emoji.btn()` orqali olinadi.
    - Barcha matnlar va teglar `i18n.get()` orqali ko'p tilli olinadi.
    """

    @staticmethod
    def format_duration(seconds: Optional[int]) -> Optional[str]:
        """Sekundlarni '2:32:13' yoki '45:10' formatiga aylantirish."""
        if not seconds or seconds <= 0:
            return None
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def format_size(bytes_size: Optional[int]) -> Optional[str]:
        """Baytlarni '1.4 GB' yoki '750 MB' formatiga aylantirish."""
        if not bytes_size or bytes_size <= 0:
            return None
        units = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(bytes_size, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_size / p, 1)
        return f"{s} {units[i]}"

    @classmethod
    def format_quality(cls, quality: Optional[str]) -> Optional[str]:
        """Sifatni aniq piksellar (480p, 720p, 1080p) formatiga o'tkazish.
        HD -> 720p, FHD -> 1080p, 4K -> 2160p va h.k.
        """
        if not quality:
            return None
        q = str(quality).strip().lower()
        mapping = {
            "hd": "720p",
            "fhd": "1080p",
            "fullhd": "1080p",
            "full hd": "1080p",
            "4k": "2160p",
            "uhd": "2160p",
            "2k": "1440p",
            "qhd": "1440p",
            "sd": "480p",
            "360": "360p",
            "480": "480p",
            "720": "720p",
            "1080": "1080p",
            "1440": "1440p",
            "2160": "2160p",
        }
        if q in mapping:
            return mapping[q]
        if q.endswith("p") and q[:-1].isdigit():
            return q
        if q.isdigit():
            return f"{q}p"
        return quality.upper()

    @classmethod
    def format_user_caption(
        cls,
        movie: Movie,
        genres: Optional[List[str]] = None,
        lang: str = "uz"
    ) -> str:
        """Foydalanuvchi kinoni so'raganda ko'rsatiladigan toza va ixcham caption.
        Faqat mavjud bo'lsa:
        1. Kino nomi (va yili)
        2. Tili
        3. Sifati (aniq 480p, 720p, 1080p ko'rinishida)
        4. Davlati
        5. Janri
        6. Ko'rishlar soni
        """
        lines = []

        # 1. Kino nomi (+ yili)
        movie_icon = emoji.get("movie")
        header = f"{movie_icon} <b>{movie.title}</b>"
        if movie.release_year:
            header += f" ({movie.release_year})"
        lines.append(header)
        lines.append("━━━━━━━━━━━━━━━━━━━━")

        # 2. Tili (sifat ustida, agar bor bo'lsa)
        if movie.language:
            lang_icon = emoji.get("language")
            lbl_language = i18n.get("movie_label_language", lang)
            lines.append(f"{lang_icon} <b>{lbl_language}:</b> {movie.language}")

        # 3. Sifati (HD/4K emas, aniq 480p, 720p va h.k.)
        clean_quality = cls.format_quality(movie.quality)
        if clean_quality:
            quality_icon = emoji.get("quality")
            lbl_quality = i18n.get("movie_label_quality", lang)
            lines.append(f"{quality_icon} <b>{lbl_quality}:</b> {clean_quality}")

        # 4. Davlati (agar bor bo'lsa)
        if movie.country:
            country_icon = emoji.get("country")
            lbl_country = i18n.get("movie_label_country", lang)
            lines.append(f"{country_icon} <b>{lbl_country}:</b> {movie.country}")

        # 5. Janri (agar bor bo'lsa)
        if genres:
            genre_icon = emoji.get("genre")
            lbl_genre = i18n.get("movie_label_genre", lang)
            lines.append(f"{genre_icon} <b>{lbl_genre}:</b> {', '.join(genres)}")

        # 6. Ko'rishlar soni (agar bor bo'lsa)
        if movie.views_count > 0:
            views_icon = emoji.get("views")
            lbl_views = i18n.get("movie_label_views", lang)
            lbl_times = i18n.get("movie_label_times", lang)
            lines.append(f"{views_icon} <b>{lbl_views}:</b> {movie.views_count} {lbl_times}")

        return "\n".join(lines)

    @classmethod
    def format_caption(
        cls,
        movie: Movie,
        channel_username: Optional[str] = None,
        genres: Optional[List[str]] = None,
        lang: str = "uz"
    ) -> str:
        """Kino obyektidan barcha mavjud maydonlarni olib, to'liq ma'lumot qolipini yasash (Admin uchun)."""
        lines = []

        # 1. Sarlavha: {movie_emoji} Betmen (2008)
        movie_icon = emoji.get("movie")
        header = f"{movie_icon} <b>{movie.title}</b>"
        if movie.release_year:
            header += f" ({movie.release_year})"
        lines.append(header)
        lines.append("━━━━━━━━━━━━━━━━━━━━")

        # 2. Kodi
        code_icon = emoji.get("code")
        lbl_code = i18n.get("movie_label_code", lang)
        lines.append(f"{code_icon} <b>{lbl_code}:</b> <code>{movie.code}</code>")

        # 3. Janrlari
        if genres:
            genre_icon = emoji.get("genre")
            lbl_genre = i18n.get("movie_label_genre", lang)
            lines.append(f"{genre_icon} <b>{lbl_genre}:</b> {', '.join(genres)}")

        # 4. Davlati
        if movie.country:
            country_icon = emoji.get("country")
            lbl_country = i18n.get("movie_label_country", lang)
            lines.append(f"{country_icon} <b>{lbl_country}:</b> {movie.country}")

        # 5. Tili
        if movie.language:
            lang_icon = emoji.get("language")
            lbl_language = i18n.get("movie_label_language", lang)
            lines.append(f"{lang_icon} <b>{lbl_language}:</b> {movie.language}")

        # 6. Reytingi
        if movie.rating:
            star_icon = emoji.get("star")
            lbl_rating = i18n.get("movie_label_rating", lang)
            lines.append(f"{star_icon} <b>{lbl_rating}:</b> {movie.rating}")

        # 7. Sifati
        clean_quality = cls.format_quality(movie.quality)
        if clean_quality:
            quality_icon = emoji.get("quality")
            lbl_quality = i18n.get("movie_label_quality", lang)
            lines.append(f"{quality_icon} <b>{lbl_quality}:</b> {clean_quality}")

        # 8. Davomiyligi (Telegramdan olingan)
        duration_str = cls.format_duration(movie.duration)
        if duration_str:
            dur_icon = emoji.get("duration")
            lbl_dur = i18n.get("movie_label_duration", lang)
            lines.append(f"{dur_icon} <b>{lbl_dur}:</b> {duration_str}")

        # 9. Hajmi (Telegramdan olingan)
        size_str = cls.format_size(movie.file_size)
        if size_str:
            pkg_icon = emoji.get("package")
            lbl_size = i18n.get("movie_label_size", lang)
            lines.append(f"{pkg_icon} <b>{lbl_size}:</b> {size_str}")

        # 10. Ko'rishlar soni
        if movie.views_count > 0:
            views_icon = emoji.get("views")
            lbl_views = i18n.get("movie_label_views", lang)
            lbl_times = i18n.get("movie_label_times", lang)
            lines.append(f"{views_icon} <b>{lbl_views}:</b> {movie.views_count} {lbl_times}")

        # 11. Tavsif (agar bo'lsa)
        if movie.description:
            desc_icon = emoji.get("description")
            lbl_desc = i18n.get("movie_label_desc", lang)
            lines.append("")
            lines.append(f"{desc_icon} <b>{lbl_desc}:</b> <i>{movie.description}</i>")

        # 12. Asosiy kanal havolasi (env dan MAIN_CHANNEL_USERNAME yoki berilgan username)
        clean_username = (channel_username or "").replace("@", "").strip() or settings.main_channel_username
        if clean_username:
            broadcast_icon = emoji.get("broadcast")
            lbl_channel = i18n.get("movie_label_channel", lang)
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"{broadcast_icon} <b>{lbl_channel}:</b> <a href=\"https://t.me/{clean_username}\">@{clean_username}</a>")

        return "\n".join(lines)

    @classmethod
    def get_movie_keyboard(
        cls,
        movie_id: int,
        bot_username: str,
        likes: int = 0,
        dislikes: int = 0,
        lang: str = "uz",
        movie_code: Optional[str] = None,
        is_favorite: bool = False
    ) -> InlineKeyboardMarkup:
        """Kino tagidagi interaktiv tugmalar (RULES.md: Dynamic Emojis va i18n)."""
        like_text = f"{emoji.raw('like')} {likes}"
        dislike_text = f"{emoji.raw('dislike')} {dislikes}"

        # Saqlash / Saqlangan holati (Tugma bosilganda o'zgarishi uchun)
        fav_label = i18n.get("btn_saved", lang) if is_favorite else i18n.get("btn_favorite", lang)
        fav_icon_key = "check" if is_favorite else "favorite"
        fav_text = emoji.btn(fav_icon_key, fav_label)

        # Do'stlarga ulashish havolasi: to'g'ridan-to'g'ri ?start=1 (kino kodi)
        share_code = movie_code if movie_code else str(movie_id)
        share_text = emoji.btn("link", i18n.get("btn_share", lang))

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=like_text, callback_data=f"react:like:{movie_id}"),
                    InlineKeyboardButton(text=dislike_text, callback_data=f"react:dislike:{movie_id}"),
                    InlineKeyboardButton(text=fav_text, callback_data=f"fav:{movie_id}")
                ],
                [
                    InlineKeyboardButton(
                        text=share_text,
                        url=f"https://t.me/share/url?url=https://t.me/{bot_username}?start={share_code}"
                    )
                ]
            ]
        )

    @classmethod
    def get_quality_selection_keyboard(
        cls,
        movie_id: int,
        media_files: List["MovieMedia"],
        bot_username: str,
        likes: int = 0,
        dislikes: int = 0,
        lang: str = "uz",
        movie_code: Optional[str] = None,
        is_favorite: bool = False
    ) -> InlineKeyboardMarkup:
        """Bir nechta sifat varianti mavjud bo'lganda sifat tanlash tugmalari (Multi-Quality)."""
        dl_icon = emoji.raw("download")
        buttons = []
        quality_row = []

        for mf in media_files:
            size_str = cls.format_size(mf.file_size)
            label = f"{dl_icon} {mf.quality.upper()} ({size_str})" if size_str else f"{dl_icon} {mf.quality.upper()}"
            quality_row.append(
                InlineKeyboardButton(text=label, callback_data=f"dl:{movie_id}:{mf.quality}")
            )
            if len(quality_row) == 2:
                buttons.append(quality_row)
                quality_row = []

        if quality_row:
            buttons.append(quality_row)

        # Reaksiyalar qatori
        like_text = f"{emoji.raw('like')} {likes}"
        dislike_text = f"{emoji.raw('dislike')} {dislikes}"

        # Saqlash / Saqlangan holati
        fav_label = i18n.get("btn_saved", lang) if is_favorite else i18n.get("btn_favorite", lang)
        fav_icon_key = "check" if is_favorite else "favorite"
        fav_text = emoji.btn(fav_icon_key, fav_label)

        buttons.append([
            InlineKeyboardButton(text=like_text, callback_data=f"react:like:{movie_id}"),
            InlineKeyboardButton(text=dislike_text, callback_data=f"react:dislike:{movie_id}"),
            InlineKeyboardButton(text=fav_text, callback_data=f"fav:{movie_id}")
        ])

        # Ulashish qatori (?start=1)
        share_code = movie_code if movie_code else str(movie_id)
        share_text = emoji.btn("link", i18n.get("btn_share", lang))
        buttons.append([
            InlineKeyboardButton(
                text=share_text,
                url=f"https://t.me/share/url?url=https://t.me/{bot_username}?start={share_code}"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

