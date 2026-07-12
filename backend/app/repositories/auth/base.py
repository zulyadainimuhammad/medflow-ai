from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository[ModelT: Base]:
    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def create(self, instance: ModelT, *, flush: bool = True, refresh: bool = False) -> ModelT:
        self.session.add(instance)
        if flush:
            await self.session.flush()
        if refresh:
            await self.session.refresh(instance)
        return instance

    async def get_by_pk(self, pk: Any) -> ModelT | None:
        return await self.session.get(self.model, pk)

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        order_by: InstrumentedAttribute[Any] | None = None,
    ) -> list[ModelT]:
        stmt: Select[tuple[ModelT]] = select(self.model).offset(offset).limit(limit)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def scalar_one_or_none(self, stmt: Select[tuple[ModelT]]) -> ModelT | None:
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def scalars_all(self, stmt: Select[tuple[ModelT]]) -> list[ModelT]:
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, instance: ModelT, *, flush: bool = True) -> None:
        await self.session.delete(instance)
        if flush:
            await self.session.flush()

    async def add_all(self, instances: Iterable[ModelT], *, flush: bool = True) -> Sequence[ModelT]:
        self.session.add_all(instances)
        if flush:
            await self.session.flush()
        return list(instances)

    async def update_fields(self, instance: ModelT, **fields: Any) -> ModelT:
        for field_name, value in fields.items():
            setattr(instance, field_name, value)
        await self.session.flush()
        return instance
