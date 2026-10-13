from typing import Optional, Union, Dict, Any
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import rbac
from app.database.models.user import User
from app.services.user_service import UserService


class AdminPermissionFilter(BaseFilter):
    """RBAC orqali admin ruxsatlarini xavfsiz tekshiruvchi filtr."""

    def __init__(self, permission: Optional[str] = None):
        self.permission = permission

    async def __call__(
        self,
        event: Union[Message, CallbackQuery],
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None,
        **kwargs: Any
    ) -> bool:
        user_tg = event.from_user
        if not user_tg:
            return False

        # 1. Superadmin (GOD Level bypass — har doim ruxsat beriladi)
        if rbac.is_god(user_tg.id):
            return True

        # 2. Agar user ineksiya qilingan bo'lsa
        current_user = user
        if not current_user and session:
            user_service = UserService(session)
            current_user = await user_service.get_by_telegram_id(user_tg.id)

        if not current_user:
            return False

        # 3. Ruxsat talab qilinmagan bo'lsa (faqat moderator yoki admin roli)
        if not self.permission:
            return current_user.role_id in (2, 3)

        # 4. Aniq huquq (permission) bo'yicha tekshirish
        return rbac.has_permission(current_user.telegram_id, current_user.role_id, self.permission)
