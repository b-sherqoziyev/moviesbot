from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    BigInteger, String, Boolean, Integer, Numeric, DateTime, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, AuditMixin


class VIPPlan(Base, TimestampMixin, AuditMixin):
    """VIP Obuna tarif rejalari modeli."""

    __tablename__ = "vip_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, doc="Tarif nomi")
    days: Mapped[int] = mapped_column(Integer, nullable=False, doc="Davomiyligi (kun)")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, doc="Narxi")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="Sotuvda mavjudmi")

    subscriptions: Mapped[list["UserSubscription"]] = relationship("UserSubscription", back_populates="plan")

    def __repr__(self) -> str:
        return f"<VIPPlan(id={self.id}, name='{self.name}', price={self.price})>"


class UserSubscription(Base, TimestampMixin):
    """Foydalanuvchining faol yoki o'tgan VIP obunasi."""

    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vip_plans.id", ondelete="SET NULL"),
        nullable=True
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    plan: Mapped[Optional["VIPPlan"]] = relationship("VIPPlan", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<UserSubscription(user_id={self.user_id}, end_date='{self.end_date}')>"


class Payment(Base, TimestampMixin):
    """To'lov tranzaksiyalari modeli (Click, Payme, Stars, Crypto)."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("vip_plans.id", ondelete="SET NULL"),
        nullable=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, doc="click, payme, stars, crypto")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, doc="To'langan summa")
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True, doc="pending, paid, cancelled")
    external_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status='{self.status}')>"
