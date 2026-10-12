from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Barcha modellar uchun umumiy Generic CRUD operatsiyalari (DRY)."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """ID orqali bitta yozuvni olish."""
        return await self.session.get(self.model, id)

    async def get_one_or_none(self, **filter_by) -> Optional[ModelType]:
        """Berilgan filtr bo'yicha bitta yozuvni olish."""
        stmt = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, limit: int = 100, offset: int = 0, **filter_by) -> List[ModelType]:
        """Ro'yxatni sahifalab (pagination) olish."""
        stmt = select(self.model).filter_by(**filter_by).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **data) -> ModelType:
        """Yangi yozuv qo'shish."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: Any, **data) -> Optional[ModelType]:
        """Mavjud yozuvni yangilash."""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()

    async def delete(self, id: Any) -> bool:
        """Yozuvni o'chirish."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, **filter_by) -> bool:
        """Yozuv mavjudligini tekshirish."""
        stmt = select(func.count()).select_from(self.model).filter_by(**filter_by)
        result = await self.session.execute(stmt)
        return (result.scalar() or 0) > 0

    async def count(self, **filter_by) -> int:
        """Jami yozuvlar sonini hisoblash."""
        stmt = select(func.count()).select_from(self.model).filter_by(**filter_by)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
