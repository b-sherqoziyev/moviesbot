from typing import List
from sqlalchemy import String, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base


class Role(Base):
    """Foydalanuvchilar rollari jadvali (superadmin, admin, moderator, user)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, doc="Tizim nomi")
    title: Mapped[str] = mapped_column(String(64), nullable=False, doc="Ko'rinadigan nomi")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Standart rolmi")

    # Munosabatlar
    users: Mapped[List["User"]] = relationship("User", back_populates="role")
    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', title='{self.title}')>"


class RolePermission(Base):
    """Rollar va ruxsatlar (permissions) bog'lanishi jadvali."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_key", name="uq_role_permission"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True, doc="Ruxsat kaliti")

    role: Mapped["Role"] = relationship("Role", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission='{self.permission_key}')>"
