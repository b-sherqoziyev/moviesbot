from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine
)
from app.core.config import settings

# Yuqori unumdorlikka ega Asinxron Engine (Connection Pool bilan)
engine: AsyncEngine = create_async_engine(
    url=settings.database_url,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# Har bir tranzaksiya uchun sessiyalar fabrikasi
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Asinxron sessiyani xavfsiz ochuvchi va yopuvchi context generator."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """Bot to'xtatilganda ulanishlar hovuzini toza yopish."""
    await engine.dispose()
