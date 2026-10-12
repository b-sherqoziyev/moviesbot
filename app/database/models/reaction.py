from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class MovieReaction(Base):
    """Kinolarga bildirilgan munosabat (Like / Dislike)."""

    __tablename__ = "movie_reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_reaction"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    is_like: Mapped[bool] = mapped_column(Boolean, nullable=False, doc="True: Like, False: Dislike")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    movie: Mapped["Movie"] = relationship("Movie", back_populates="reactions")

    def __repr__(self) -> str:
        return f"<MovieReaction(user_id={self.user_id}, movie_id={self.movie_id}, is_like={self.is_like})>"


class Favorite(Base):
    """Foydalanuvchining saqlab qo'ygan (sevimli) kinolari."""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_favorite"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    movie: Mapped["Movie"] = relationship("Movie", back_populates="favorites")

    def __repr__(self) -> str:
        return f"<Favorite(user_id={self.user_id}, movie_id={self.movie_id})>"


class MovieView(Base):
    """Kinoni ko'rishlar jurnali (Analitika uchun)."""

    __tablename__ = "movie_views"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<MovieView(user_id={self.user_id}, movie_id={self.movie_id})>"
