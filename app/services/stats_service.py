from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.models.movie import Movie
from app.database.models.reaction import Favorite


class StatsService:
    """Foydalanuvchi va tizim statistikasi xizmati."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_stats(self, user: User) -> Dict[str, Any]:
        """Foydalanuvchining shaxsiy ko'rsatkichlari."""
        stmt = select(func.count(Favorite.id)).where(Favorite.user_id == user.telegram_id)
        result = await self.session.execute(stmt)
        fav_count = result.scalar() or 0

        return {
            "referrals_count": user.referrals_count,
            "watched_movies_count": user.watched_movies_count,
            "favorites_count": fav_count,
            "language_code": user.language_code
        }

    async def get_global_stats(self) -> Dict[str, Any]:
        """Umumiy bot ko'rsatkichlari (Admin / Ommaviy)."""
        # Jami faol foydalanuvchilar
        users_stmt = select(func.count(User.id)).where(User.is_active == True)
        users_res = await self.session.execute(users_stmt)
        total_users = users_res.scalar() or 0

        # Jami faol kinolar
        movies_stmt = select(func.count(Movie.id)).where(Movie.is_active == True)
        movies_res = await self.session.execute(movies_stmt)
        total_movies = movies_res.scalar() or 0

        # Jami ko'rishlar soni
        views_stmt = select(func.coalesce(func.sum(Movie.views_count), 0))
        views_res = await self.session.execute(views_stmt)
        total_views = views_res.scalar() or 0

        return {
            "total_users": total_users,
            "total_movies": total_movies,
            "total_views": total_views
        }
