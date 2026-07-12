from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.auth.permission_repository import PermissionRepository
from app.repositories.auth.role_repository import RoleRepository
from app.repositories.auth.user_repository import UserRepository


def get_user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session=session)


def get_role_repository(session: AsyncSession) -> RoleRepository:
    return RoleRepository(session=session)


def get_permission_repository(session: AsyncSession) -> PermissionRepository:
    return PermissionRepository(session=session)
