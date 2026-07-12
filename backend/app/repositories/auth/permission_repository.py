from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.auth import Permission, Role, UserRole
from app.repositories.auth.base import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Permission)

    async def list_permissions(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.name.asc())
        return await self.scalars_all(stmt)

    async def get_permissions_for_role(self, role_id: int) -> list[Permission]:
        stmt = select(Permission).where(Permission.role_id == role_id).order_by(Permission.name.asc())
        return await self.scalars_all(stmt)

    async def get_permissions_for_user(self, user_id: UUID) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(Role, Role.id == Permission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(Permission.name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())
