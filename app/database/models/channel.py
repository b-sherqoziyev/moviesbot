from sqlalchemy import BigInteger, String, Boolean, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import Base, TimestampMixin, AuditMixin


class Channel(Base, TimestampMixin, AuditMixin):
    """Majburiy a'zolik homiy kanallari modeli."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False, doc="Telegram kanal ID si")
    title: Mapped[str] = mapped_column(String(128), nullable=False, doc="Kanal nomi")
    url: Mapped[str] = mapped_column(String(255), nullable=False, doc="Kanal havolasi (https://t.me/...)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Tekshiruvda faolmi")
    priority: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, doc="Tartiblash (0, 1, 2...)")

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, channel_id={self.channel_id}, title='{self.title}')>"
