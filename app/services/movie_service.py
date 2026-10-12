import re
import logging
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.movie import Movie, MovieMedia
from app.database.models.reaction import MovieView, MovieReaction, Favorite
from app.database.repositories.movie_repository import MovieRepository
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


from app.database.models.genre import Genre, MovieGenre
from app.services.caption_parser import SmartCaptionParser, ParsedMovieData


class MovieService:
    """Kinolar bilan ishlash biznes logikasi va aqlli post parser."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MovieRepository(session)
        self.user_repo = UserRepository(session)

    async def get_by_code(self, code: str, telegram_id: Optional[int] = None) -> Optional[Movie]:
        """Kodni tozalab qidirish va ko'rishlar sonini kunlik 1 marta oshirish (Anti-Spam / Anti-Nakrutka)."""
        clean_code = code.strip().upper()
        movie = await self.repo.get_by_code(clean_code)
        if not movie:
            return None

        # 1. Kunlik ko'rishlar cheklovi (1 user = 1 movie = 24 soatda faqat 1 marta oshadi)
        should_increment = True
        if telegram_id:
            try:
                from app.bot.loader import redis_client
                key = f"movie_view:{telegram_id}:{movie.id}"
                # 24 soat (86400 soniya) ichida faqat 1-marta True qaytaradi
                is_first_today = await redis_client.set(key, 1, ex=86400, nx=True)
                should_increment = bool(is_first_today)
            except Exception as e:
                logger.warning(f"Redis view-lock tekshirishda xatolik: {e}")
                should_increment = False

        if should_increment:
            await self.repo.increment_views(movie.id)
            movie.views_count += 1
            if telegram_id:
                await self.user_repo.increment_watched_movies(telegram_id)
                view_log = MovieView(user_id=telegram_id, movie_id=movie.id)
                self.session.add(view_log)
                await self.session.commit()

        return movie

    async def get_movie_genres(self, movie_id: int) -> List[str]:
        """Kino janrlari nomlarini ro'yxat qilib olish."""
        stmt = (
            select(Genre.name_uz)
            .join(MovieGenre, MovieGenre.genre_id == Genre.id)
            .where(MovieGenre.movie_id == movie_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_title(self, query: str, limit: int = 10, offset: int = 0) -> List[Movie]:
        """Nomi bo'yicha qidirish."""
        return await self.repo.search_by_title(query, limit=limit, offset=offset)

    async def get_top_movies(self, limit: int = 10) -> List[Movie]:
        """Eng ko'p ko'rilgan filmlar ro'yxatini olish."""
        return await self.repo.get_top_movies(limit=limit)

    async def get_next_available_code(self) -> str:
        """Admin kod kiritmagan bo'lsa, navbatdagi bo'sh raqamni avtomatik generatsiya qilish."""
        stmt = select(func.count(Movie.id))
        result = await self.session.execute(stmt)
        total = result.scalar() or 0
        return str(total + 1)

    def parse_movie_caption(self, caption: Optional[str]) -> Tuple[str, Optional[str]]:
        """Kanal postining izohidan (caption) film nomi va kodini ajratib olish (Orqaga moslik uchun)."""
        parsed = SmartCaptionParser.parse(caption)
        return parsed.title, parsed.code

    async def sync_genres(self, movie_id: int, genre_names: List[str]) -> None:
        """Kino janrlarini bazaga kiritish va ko'pdan-ko'pga bog'lash."""
        if not genre_names:
            return

        for name in genre_names:
            name_clean = name.strip()
            if not name_clean:
                continue

            # Janr mavjudligini tekshirish
            stmt = select(Genre).where(func.lower(Genre.name_uz) == func.lower(name_clean))
            res = await self.session.execute(stmt)
            genre = res.scalars().first()

            if not genre:
                code_slug = re.sub(r'[^a-zA-Z0-9_]', '_', name_clean.lower())
                genre = Genre(
                    name_uz=name_clean,
                    name_ru=name_clean,
                    name_en=name_clean,
                    code=code_slug,
                    is_active=True
                )
                self.session.add(genre)
                await self.session.flush()

            # Bog'lanishni tekshirish
            link_stmt = select(MovieGenre).where(
                MovieGenre.movie_id == movie_id,
                MovieGenre.genre_id == genre.id
            )
            link_res = await self.session.execute(link_stmt)
            if not link_res.scalars().first():
                link = MovieGenre(movie_id=movie_id, genre_id=genre.id)
                self.session.add(link)

        await self.session.commit()

    @staticmethod
    def is_similar_title(t1: str, t2: str) -> bool:
        """Ikki kino nomining o'xshashligini tekshirish (Kodni tekshirish va to'qnashuvdan himoya)."""
        clean1 = re.sub(r'[^a-zA-Z0-9а-яА-Яoʻo‘g‘]', '', t1.lower())
        clean2 = re.sub(r'[^a-zA-Z0-9а-яА-Яoʻo‘g‘]', '', t2.lower())
        if not clean1 or not clean2 or clean1 == "nomsizfilm" or clean2 == "nomsizfilm":
            return True
        return clean1 in clean2 or clean2 in clean1

    async def get_movie_media_files(self, movie_id: int) -> List[MovieMedia]:
        """Kinoning barcha sifatlardagi media fayllari ro'yxatini olish."""
        return await self.repo.get_movie_media_files(movie_id)

    async def get_media_by_quality(self, movie_id: int, quality: str) -> Optional[MovieMedia]:
        """Kinoning aniq sifati bo'yicha media faylini olish."""
        return await self.repo.get_media_by_quality(movie_id, quality)

    async def add_or_update_movie_from_post(
        self,
        parsed_data: ParsedMovieData,
        file_id: str,
        file_unique_id: str,
        file_type: str = "video",
        caption: Optional[str] = None,
        file_size: Optional[int] = None,
        duration: Optional[int] = None,
        channel_id: Optional[int] = None,
        channel_message_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Movie:
        """Kanaldan kelgan post ma'lumotlarini to'liq, sifatlarni ko'paytiruvchi va to'qnashuvdan himoyalangan tarzda saqlash."""
        code = parsed_data.code
        if not code:
            code = await self.get_next_available_code()
        clean_code = code.strip().upper()

        # 1. Avval post_id yoki kod bo'yicha qidirish
        existing = None
        if channel_id and channel_message_id:
            existing = await self.repo.get_by_channel_post(channel_id, channel_message_id)

        if not existing:
            existing = await self.repo.get_by_code(clean_code)

        # 2. To'qnashuv (Collision) tekshiruvi:
        # Agar bu kod mavjud bo'lsa, lekin nomi BUTUNLAY boshqa yangi kino bo'lsa:
        if existing and (existing.channel_id != channel_id or existing.channel_message_id != channel_message_id):
            if not self.is_similar_title(parsed_data.title, existing.title):
                # Kod to'qnashuvi! Yangi kinoni eski kinoning ustiga yozmaymiz!
                new_code = await self.get_next_available_code()
                logger.warning(
                    f"KOD TO'QNASHOVI: {clean_code} kodi allaqachon '{existing.title}' uchun band! "
                    f"'{parsed_data.title}' ga avtomatik yangi kod berildi: {new_code}"
                )
                clean_code = new_code
                existing = None  # Yangi kino sifatida kiritiladi

        if existing:
            # Mavjud kinoga yangi sifat (Multi-Quality) ulash yoki yangilash
            quality = parsed_data.quality or existing.quality or "720p"
            existing.code = clean_code
            if parsed_data.title and parsed_data.title != "Nomsiz Film":
                existing.title = parsed_data.title
            existing.release_year = parsed_data.release_year or existing.release_year
            existing.rating = parsed_data.rating if parsed_data.rating is not None else existing.rating
            existing.country = parsed_data.country or existing.country
            existing.language = parsed_data.language or existing.language
            existing.quality = quality
            existing.description = parsed_data.description or existing.description
            existing.file_id = file_id
            existing.file_unique_id = file_unique_id
            existing.file_type = file_type
            existing.caption = caption
            existing.file_size = file_size or existing.file_size
            existing.duration = duration or existing.duration
            existing.updated_by = created_by
            existing.is_active = True

            # MovieMedia jadvaliga ham sifat faylini saqlash/yangilash
            await self.repo.add_or_update_media(
                movie_id=existing.id,
                quality=quality,
                file_id=file_id,
                file_unique_id=file_unique_id,
                file_type=file_type,
                file_size=file_size,
                duration=duration,
                channel_id=channel_id,
                channel_message_id=channel_message_id
            )

            await self.session.commit()
            await self.session.refresh(existing)

            if parsed_data.genres:
                await self.sync_genres(existing.id, parsed_data.genres)

            logger.info(f"Kino va uning sifati ({quality}) yangilandi: [{existing.code}] {existing.title}")
            return existing

        # Yangi qo'shish (Create)
        quality = parsed_data.quality or "720p"
        movie = Movie(
            code=clean_code,
            title=parsed_data.title,
            release_year=parsed_data.release_year,
            rating=parsed_data.rating,
            country=parsed_data.country,
            language=parsed_data.language,
            quality=quality,
            description=parsed_data.description,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            caption=caption,
            file_size=file_size,
            duration=duration,
            channel_id=channel_id,
            channel_message_id=channel_message_id,
            created_by=created_by
        )
        self.session.add(movie)
        await self.session.commit()
        await self.session.refresh(movie)

        # MovieMedia jadvaliga ham sifat faylini biriktirish
        await self.repo.add_or_update_media(
            movie_id=movie.id,
            quality=quality,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            file_size=file_size,
            duration=duration,
            channel_id=channel_id,
            channel_message_id=channel_message_id
        )
        await self.session.commit()

        if parsed_data.genres:
            await self.sync_genres(movie.id, parsed_data.genres)

        logger.info(f"Yangi kino bazaga kiritildi: [{movie.code}] {movie.title} | Sifat: {quality} (ID: {movie.id})")
        return movie

    async def update_movie_caption_from_channel(
        self,
        channel_id: int,
        channel_message_id: int,
        new_caption: str
    ) -> Optional[Movie]:
        """Admin kanaldagi post matnini o'zgartirganda (edited_channel_post) bazadagi kinoni parallel yangilash."""
        movie = await self.repo.get_by_channel_post(channel_id, channel_message_id)
        if not movie:
            return None

        parsed = SmartCaptionParser.parse(new_caption)
        if parsed.code:
            movie.code = parsed.code.strip().upper()
        if parsed.title and parsed.title != "Nomsiz Film":
            movie.title = parsed.title
        if parsed.release_year:
            movie.release_year = parsed.release_year
        if parsed.rating is not None:
            movie.rating = parsed.rating
        if parsed.country:
            movie.country = parsed.country
        if parsed.language:
            movie.language = parsed.language
        if parsed.quality:
            movie.quality = parsed.quality
        if parsed.description:
            movie.description = parsed.description
        movie.caption = new_caption

        await self.session.commit()
        await self.session.refresh(movie)

        if parsed.genres:
            await self.sync_genres(movie.id, parsed.genres)

        logger.info(f"Kanaldagi tahrir bazaga sinxronlandi: [{movie.code}] {movie.title}")
        return movie

    async def add_movie(
        self,
        code: str,
        title: str,
        file_id: str,
        file_unique_id: str,
        file_type: str = "video",
        caption: Optional[str] = None,
        file_size: Optional[int] = None,
        duration: Optional[int] = None,
        channel_id: Optional[int] = None,
        channel_message_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Movie:
        """Eski add_movie chaqiruvlari uchun orqaga moslik (deprecated, use add_or_update_movie_from_post)."""
        parsed = SmartCaptionParser.parse(caption)
        parsed.code = code
        parsed.title = title
        return await self.add_or_update_movie_from_post(
            parsed_data=parsed,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            caption=caption,
            file_size=file_size,
            duration=duration,
            channel_id=channel_id,
            channel_message_id=channel_message_id,
            created_by=created_by
        )

    async def toggle_reaction(self, user_id: int, movie_id: int, is_like: bool) -> Tuple[int, int]:
        """Kino uchun Like yoki Dislike bildirish (va qaytarib olish)."""
        stmt = select(MovieReaction).where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()
        movie = await self.repo.get_by_id(movie_id)
        if not movie:
            return 0, 0

        if existing:
            if existing.is_like == is_like:
                # O'z reaksiyasini qaytarib olish
                await self.session.delete(existing)
                if is_like:
                    movie.likes_count = max(0, movie.likes_count - 1)
                else:
                    movie.dislikes_count = max(0, movie.dislikes_count - 1)
            else:
                # Reaksiyani o'zgartirish (masalan Like dan Dislike ga)
                existing.is_like = is_like
                if is_like:
                    movie.likes_count += 1
                    movie.dislikes_count = max(0, movie.dislikes_count - 1)
                else:
                    movie.dislikes_count += 1
                    movie.likes_count = max(0, movie.likes_count - 1)
        else:
            # Yangi reaksiya
            reaction = MovieReaction(user_id=user_id, movie_id=movie_id, is_like=is_like)
            self.session.add(reaction)
            if is_like:
                movie.likes_count += 1
            else:
                movie.dislikes_count += 1

        await self.session.commit()
        await self.session.refresh(movie)
        return movie.likes_count, movie.dislikes_count

    async def toggle_favorite(self, user_id: int, movie_id: int) -> bool:
        """Kinoni sevimlilarga qo'shish yoki olib tashlash."""
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.movie_id == movie_id
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()
        movie = await self.repo.get_by_id(movie_id)

        if existing:
            await self.session.delete(existing)
            if movie:
                movie.favorites_count = max(0, movie.favorites_count - 1)
            is_added = False
        else:
            fav = Favorite(user_id=user_id, movie_id=movie_id)
            self.session.add(fav)
            if movie:
                movie.favorites_count += 1
            is_added = True

        await self.session.commit()
        return is_added

    async def is_favorite(self, user_id: int, movie_id: int) -> bool:
        """Foydalanuvchi ushbu kinoni sevimlilariga saqlaganmi?"""
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.movie_id == movie_id
        )
        res = await self.session.execute(stmt)
        return res.scalars().first() is not None

