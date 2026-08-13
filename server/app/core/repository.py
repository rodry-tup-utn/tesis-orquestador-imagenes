from typing import Generic, TypeVar, Type, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select
from sqlalchemy import func

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):

    def __init__(self, session: AsyncSession, model: Type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, record_id: int) -> ModelT | None:
        return await self.session.get(self.model, record_id)

    async def get_all(self, offset: int = 0, limit: int = 20) -> Sequence[ModelT]:
        result = await self.session.execute(select(self.model).offset(offset).limit(limit))
        return result.scalars().all()

    async def count(self) -> int:
        statement = select(func.count()).select_from(self.model)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
