from typing import Optional, List
from sqlalchemy import (
    BigInteger, String, Boolean, Integer, SmallInteger, Text, Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, AuditMixin


class Movie(Base, TimestampMixin, AuditMixin):
    """Kinolar modeli."""

    __tablename__ = "movies"
    __table_args__ = (
        Index("idx_movies_views_desc", "views_count", postgresql_using="btree"),
        Index("idx_movies_code", "code"),
        Index("idx_movies_title", "title"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, doc="Film kodi (masalan: 124)")
    title: Mapped[str] = mapped_column(String(255), nullable=False, doc="Film nomi")
    original_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Film tavsifi")

    # Telegram Media fayl ma'lumotlari (Asosiy / Standart sifat)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False, doc="Telegram file_id")
    file_unique_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    file_type: Mapped[str] = mapped_column(String(20), default="video", nullable=False, doc="video yoki document")
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, doc="Hajmi (bayt)")
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, doc="Davomiyligi (sekund)")
    quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, doc="720p, 1080p va h.k.")
    release_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(nullable=True, doc="IMDb yoki film reytingi (masalan 9.0)")
    language: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, doc="Film tili (masalan O'zbek tili)")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Film haqida qisqacha tavsif")

    # Tezkor hisoblagichlar (Counters)
    views_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, doc="Ko'rishlar soni")
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Yoqtirishlar")
    dislikes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Yoqtirmasliklar")
    favorites_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Saqlab olinganlar")

    # Holat va VIP
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Faqat VIP foydalanuvchilar uchunmi")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Faol/O'chirilgan (Soft Delete)")

    # Maxfiy ombor kanaldagi ma'lumotlar
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, doc="Ombor kanal ID si")
    channel_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, doc="Ombor kanaldagi post ID")

    # Munosabatlar
    reactions: Mapped[List["MovieReaction"]] = relationship(
        "MovieReaction",
        back_populates="movie",
        cascade="all, delete-orphan"
    )
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite",
        back_populates="movie",
        cascade="all, delete-orphan"
    )
    genres: Mapped[List["MovieGenre"]] = relationship(
        "MovieGenre",
        back_populates="movie",
        cascade="all, delete-orphan"
    )
    media_files: Mapped[List["MovieMedia"]] = relationship(
        "MovieMedia",
        back_populates="movie",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Movie(id={self.id}, code='{self.code}', title='{self.title}', views={self.views_count})>"


class MovieMedia(Base, TimestampMixin):
    """Kinoning turli sifatlardagi media fayllari (1080p, 720p, 480p)."""

    __tablename__ = "movie_media"
    __table_args__ = (
        UniqueConstraint("movie_id", "quality", name="uq_movie_quality"),
        Index("idx_movie_media_movie_id", "movie_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    quality: Mapped[str] = mapped_column(String(32), nullable=False, doc="1080p, 720p, 480p")
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    file_type: Mapped[str] = mapped_column(String(20), default="video", nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    channel_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    movie: Mapped["Movie"] = relationship("Movie", back_populates="media_files")

    def __repr__(self) -> str:
        return f"<MovieMedia(id={self.id}, movie_id={self.movie_id}, quality='{self.quality}')>"
