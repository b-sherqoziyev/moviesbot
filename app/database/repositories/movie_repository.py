from typing import Optional, List
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.movie import Movie, MovieMedia
from app.database.repositories.base import BaseRepository


class MovieRepository(BaseRepository[Movie]):
    """Kinolar bilan ishlovchi repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(Movie, session)

    async def get_by_code(self, code: str) -> Optional[Movie]:
        """Film kodi bo'yicha qidirish (Indeks orqali 1ms)."""
        stmt = (
            select(Movie)
            .where(Movie.code == code.strip(), Movie.is_active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_file_unique_id(self, file_unique_id: str) -> Optional[Movie]:
        """Faylning unikal ID si bo'yicha qidirish (dublikat yuklanmasligi uchun)."""
        stmt = select(Movie).where(Movie.file_unique_id == file_unique_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_channel_post(self, channel_id: int, channel_message_id: int) -> Optional[Movie]:
        """Kanal ID va Post ID bo'yicha kinoni topish (Sinxron CRUD / Edit uchun)."""
        stmt = select(Movie).where(
            Movie.channel_id == channel_id,
            Movie.channel_message_id == channel_message_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_movie_media_files(self, movie_id: int) -> List[MovieMedia]:
        """Kinoning barcha sifatlardagi media fayllari ro'yxatini olish."""
        stmt = (
            select(MovieMedia)
            .where(MovieMedia.movie_id == movie_id)
            .order_by(MovieMedia.quality.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_media_by_quality(self, movie_id: int, quality: str) -> Optional[MovieMedia]:
        """Kinoning aniq sifati bo'yicha media faylini olish."""
        stmt = select(MovieMedia).where(
            MovieMedia.movie_id == movie_id,
            MovieMedia.quality == quality.lower().strip()
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_or_update_media(
        self,
        movie_id: int,
        quality: str,
        file_id: str,
        file_unique_id: str,
        file_type: str = "video",
        file_size: Optional[int] = None,
        duration: Optional[int] = None,
        channel_id: Optional[int] = None,
        channel_message_id: Optional[int] = None
    ) -> MovieMedia:
        """Kinoga yangi sifatdagi media faylni ulash yoki yangilash."""
        clean_quality = quality.lower().strip()
        media = await self.get_media_by_quality(movie_id, clean_quality)
        if media:
            media.file_id = file_id
            media.file_unique_id = file_unique_id
            media.file_type = file_type
            media.file_size = file_size or media.file_size
            media.duration = duration or media.duration
            media.channel_id = channel_id or media.channel_id
            media.channel_message_id = channel_message_id or media.channel_message_id
            return media

        media = MovieMedia(
            movie_id=movie_id,
            quality=clean_quality,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            file_size=file_size,
            duration=duration,
            channel_id=channel_id,
            channel_message_id=channel_message_id
        )
        self.session.add(media)
        return media

    async def search_by_title(self, query: str, limit: int = 10, offset: int = 0) -> List[Movie]:
        """Nomi bo'yicha qidirish (Pagination bilan)."""
        stmt = (
            select(Movie)
            .where(Movie.title.ilike(f"%{query.strip()}%"), Movie.is_active == True)
            .order_by(desc(Movie.views_count))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_top_movies(self, limit: int = 10) -> List[Movie]:
        """Eng ko'p ko'rilgan filmlar ro'yxatini olish (Indeks orqali)."""
        stmt = (
            select(Movie)
            .where(Movie.is_active == True)
            .order_by(desc(Movie.views_count))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def increment_views(self, movie_id: int) -> None:
        """Kino ko'rishlar sonini atomik 1 taga oshirish."""
        stmt = (
            update(Movie)
            .where(Movie.id == movie_id)
            .values(views_count=Movie.views_count + 1)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def soft_delete(self, movie_id: int, admin_id: int) -> bool:
        """Kinoni o'chirish (Soft Delete: is_active=False)."""
        stmt = (
            update(Movie)
            .where(Movie.id == movie_id)
            .values(is_active=False, updated_by=admin_id)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
