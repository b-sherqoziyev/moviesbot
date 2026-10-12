from datetime import datetime
from typing import Optional, Any
from sqlalchemy import (
    BigInteger, String, Integer, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import Base


class BroadcastTask(Base):
    """Admin xabar tarqatish (Broadcast) vazifalari va statistikasi."""

    __tablename__ = "broadcast_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        doc="Xabarni yuborgan admin Telegram ID si"
    )
    message_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="text, photo, video, animation, document, forward"
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Xabar matni yoki caption")
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, doc="Media file_id")
    reply_markup: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True, doc="Inline tugmalar")

    total_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Rejadagi jami foydalanuvchilar")
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Yetkazilganlar soni")
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Yetib bormaganlar (bloklaganlar)")
    status: Mapped[str] = mapped_column(
        String(20),
        default="queued",
        nullable=False,
        index=True,
        doc="queued, running, completed, stopped"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<BroadcastTask(id={self.id}, admin_id={self.admin_id}, status='{self.status}', sent={self.sent_count})>"
