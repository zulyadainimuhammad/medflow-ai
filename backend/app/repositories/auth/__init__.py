from app.repositories.auth.base import BaseRepository
from app.repositories.auth.dependencies import (
    get_permission_repository,
    get_role_repository,
    get_user_repository,
)
from app.repositories.auth.permission_repository import PermissionRepository
from app.repositories.auth.role_repository import RoleRepository
from app.repositories.auth.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "get_user_repository",
    "get_role_repository",
    "get_permission_repository",
]
