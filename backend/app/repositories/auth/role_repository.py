from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.auth import Role, UserRole
from app.repositories.auth.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Role)

    async def list_roles(self) -> list[Role]:
        stmt = select(Role).order_by(Role.name.asc())
        return await self.scalars_all(stmt)

    async def get_role_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        return await self.scalar_one_or_none(stmt)

    async def assign_role(self, user_id: UUID, role_id: int) -> UserRole:
        stmt = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        existing = await self.session.execute(stmt)
        user_role = existing.scalar_one_or_none()
        if user_role is not None:
            return user_role

        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        await self.session.flush()
        return user_role

    async def remove_role(self, user_id: UUID, role_id: int) -> bool:
        stmt = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        user_role = result.scalar_one_or_none()
        if user_role is None:
            return False

        await self.session.delete(user_role)
        await self.session.flush()
        return True

    async def get_user_roles(self, user_id: UUID) -> list[Role]:
        stmt = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(Role.name.asc())
        )
        return await self.scalars_all(stmt)
