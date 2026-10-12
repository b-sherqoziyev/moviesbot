from typing import List
from sqlalchemy import String, Boolean, Integer, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class Genre(Base):
    """Kinolar janrlari ma'lumotnomasi (Jangari, Komediya va h.k.)."""

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_uz: Mapped[str] = mapped_column(String(64), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(64), nullable=False)
    name_en: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, doc="action, comedy...")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    movie_genres: Mapped[List["MovieGenre"]] = relationship("MovieGenre", back_populates="genre")

    def __repr__(self) -> str:
        return f"<Genre(id={self.id}, code='{self.code}', name_uz='{self.name_uz}')>"


class MovieGenre(Base):
    """Kino va Janr o'rtasidagi bog'lanish jadvali (Many-to-Many)."""

    __tablename__ = "movie_genres"
    __table_args__ = (
        UniqueConstraint("movie_id", "genre_id", name="uq_movie_genre"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    genre_id: Mapped[int] = mapped_column(Integer, ForeignKey("genres.id", ondelete="CASCADE"), nullable=False)

    movie: Mapped["Movie"] = relationship("Movie", back_populates="genres")
    genre: Mapped["Genre"] = relationship("Genre", back_populates="movie_genres")

    def __repr__(self) -> str:
        return f"<MovieGenre(movie_id={self.movie_id}, genre_id={self.genre_id})>"
