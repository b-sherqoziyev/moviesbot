from typing import List, Optional
from decimal import Decimal
from sqlalchemy import BigInteger, String, Boolean, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Foydalanuvchilar modeli."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="uz", nullable=False)

    # Rol (RBAC)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False, default=1)
    role: Mapped["Role"] = relationship("Role", back_populates="users")

    # Holat va Referal
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Botni bloklamaganmi")
    referrer_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="SET NULL"),
        nullable=True,
        doc="Taklif qilgan foydalanuvchi Telegram ID si"
    )

    # Tezkor hisoblagichlar (Counters)
    referrals_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Do'stlari soni")
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    watched_movies_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Ko'rgan filmlari")

    # Munosabatlar
    referrer: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[telegram_id],
        back_populates="referrals"
    )
    referrals: Mapped[List["User"]] = relationship(
        "User",
        back_populates="referrer"
    )

    @property
    def is_vip(self) -> bool:
        """Foydalanuvchining VIP maqomini aniqlash."""
        return False

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"
