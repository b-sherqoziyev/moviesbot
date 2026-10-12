from datetime import datetime
from sqlalchemy import DateTime, BigInteger, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Barcha SQLAlchemy modellari uchun asosiy sinf."""
    pass


class TimestampMixin:
    """Yaratilgan va yangilangan vaqtlarni avtomatik saqlovchi mixin."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Yaratilgan vaqti"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Oxirgi yangilangan vaqti"
    )


class AuditMixin:
    """Amalni bajargan admin/foydalanuvchini qayd etuvchi audit mixin."""

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="SET NULL"),
        nullable=True,
        doc="Kim tomonidan yaratilgan (Telegram ID)"
    )
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="SET NULL"),
        nullable=True,
        doc="Oxirgi marta kim tomonidan tahrirlangan (Telegram ID)"
    )
