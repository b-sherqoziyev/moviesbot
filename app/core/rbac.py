import logging
from typing import Dict, Set, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.role import Role, RolePermission

logger = logging.getLogger(__name__)

# Tizimdagi 3 ta asosiy rol
ROLE_USER_ID = 1
ROLE_MODERATOR_ID = 2
ROLE_ADMIN_ID = 3

DEFAULT_ROLES = [
    {
        "id": ROLE_USER_ID,
        "name": "user",
        "title": "Foydalanuvchi",
        "description": "Standart bot foydalanuvchisi",
        "is_default": True,
        "permissions": []  # Oddiy foydalanuvchida hech qanday admin ruxsati bo'lmaydi!
    },
    {
        "id": ROLE_MODERATOR_ID,
        "name": "moderator",
        "title": "Moderator",
        "description": "Kinolar kontent menejeri",
        "is_default": False,
        "permissions": ["movies.manage", "movies.create", "movies.edit", "movies.delete"]
    },
    {
        "id": ROLE_ADMIN_ID,
        "name": "admin",
        "title": "Administrator",
        "description": "Bot operatsion boshqaruvchisi",
        "is_default": False,
        "permissions": [
            "movies.manage", "movies.create", "movies.edit", "movies.delete",
            "channels.manage", "broadcast.send", "stats.view"
        ]
    }
]


class RBACService:
    """Rollar va Ruxsatlarni boshqaruvchi va keshlovchi xizmat."""

    def __init__(self):
        # Xotiradagi kesh: {role_id: {"movies.manage", "channels.manage", ...}}
        self.permissions_cache: Dict[int, Set[str]] = {}

    def is_god(self, telegram_id: int) -> bool:
        """Foydalanuvchi GOD Level (Superadmin / .env dagi ADMIN_IDS) ekanligini tekshirish."""
        return telegram_id in settings.ADMIN_IDS

    def has_permission(self, telegram_id: int, role_id: int, permission: str) -> bool:
        """Foydalanuvchida berilgan amal uchun ruxsat borligini tekshirish (0ms).
        
        Agar foydalanuvchi .env dagi ADMIN_IDS bo'lsa - avtomatik ravishda True.
        Aks holda xotiradagi keshdan tekshiriladi.
        """
        # 1. GOD Level tekshiruvi (.env)
        if self.is_god(telegram_id):
            return True

        # 2. Xotiradagi kesh orqali tekshirish
        allowed = self.permissions_cache.get(role_id, set())
        return permission in allowed

    async def seed_roles_and_permissions(self, session: AsyncSession) -> None:
        """Bazaga 3 ta rolni va ularning ruxsatlarini sinxronlash (Seeder)."""
        try:
            for role_data in DEFAULT_ROLES:
                # Rol mavjudligini tekshirish
                stmt = select(Role).where(Role.id == role_data["id"])
                result = await session.execute(stmt)
                role = result.scalars().first()

                if not role:
                    role = Role(
                        id=role_data["id"],
                        name=role_data["name"],
                        title=role_data["title"],
                        description=role_data["description"],
                        is_default=role_data["is_default"]
                    )
                    session.add(role)
                    await session.flush()
                    logger.info(f"Yangi rol yaratildi: {role.name}")

                # Bazadagi mavjud ruxsatlarni olish va sinxronlashtirish
                p_stmt = select(RolePermission).where(RolePermission.role_id == role.id)
                p_result = await session.execute(p_stmt)
                current_perms = p_result.scalars().all()
                current_keys = {p.permission_key for p in current_perms}
                target_keys = set(role_data["permissions"])

                # Keraksiz (masalan, user rolidan o'chirilgan) ruxsatlarni bazadan tozalash
                for p in current_perms:
                    if p.permission_key not in target_keys:
                        await session.delete(p)

                # Yangi kerakli ruxsatlarni qo'shish
                for perm_key in (target_keys - current_keys):
                    perm = RolePermission(role_id=role.id, permission_key=perm_key)
                    session.add(perm)

            await session.commit()
            logger.info("Rollar va ruxsatlar muvaffaqiyatli saqlandi (Seeded).")
        except Exception as e:
            await session.rollback()
            logger.error(f"Rollarni kiritishda xatolik: {e}")
            raise

    async def load_cache(self, session: AsyncSession) -> None:
        """Bazadagi barcha ruxsatlarni xotiraga yuklash (Zero I/O query time)."""
        try:
            stmt = select(RolePermission.role_id, RolePermission.permission_key)
            result = await session.execute(stmt)
            rows = result.all()

            cache: Dict[int, Set[str]] = {}
            for role_id, perm_key in rows:
                if role_id not in cache:
                    cache[role_id] = set()
                cache[role_id].add(perm_key)

            self.permissions_cache = cache
            logger.info(f"RBAC keshi yangilandi: {len(self.permissions_cache)} ta rol keshlangan.")
        except Exception as e:
            logger.error(f"RBAC keshini yuklashda xatolik: {e}")
            # Xatolik bo'lsa defaultlarni o'rnatish
            self.permissions_cache = {
                r["id"]: set(r["permissions"]) for r in DEFAULT_ROLES
            }


# Singleton nusxa
rbac = RBACService()
