from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import Base


class SystemSetting(Base):
    """Tizim sozlamalari (kodni o'zgartirmasdan admin panel orqali o'zgartirish uchun)."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True, doc="Sozlama kaliti (masalan: referral_reward)")
    value: Mapped[str] = mapped_column(Text, nullable=False, doc="Sozlama qiymati")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    updated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="SET NULL"),
        nullable=True,
        doc="Kim tomonidan yangilangan"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"
