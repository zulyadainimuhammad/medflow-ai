from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.auth import User
from app.repositories.auth.base import BaseRepository


class UserRepository(BaseRepository[User]):
    _FAILED_LOGIN_FIELDS: tuple[str, ...] = ("failed_login_attempts", "failed_login_count")
    _LOCK_FLAG_FIELDS: tuple[str, ...] = ("is_locked", "is_account_locked")
    _LOCK_UNTIL_FIELDS: tuple[str, ...] = ("locked_until", "account_locked_until")
    _EMPLOYEE_ID_FIELDS: tuple[str, ...] = ("employee_id", "staff_id")

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=User)

    async def create_user(self, **user_data: Any) -> User:
        user = User(**user_data)
        return await self.create(user, flush=True, refresh=False)

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return await self.scalar_one_or_none(stmt)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return await self.scalar_one_or_none(stmt)

    async def get_by_employee_id(self, employee_id: str) -> User | None:
        employee_field = self._first_existing_field(User, self._EMPLOYEE_ID_FIELDS)
        if employee_field is None:
            return None

        stmt = select(User).where(getattr(User, employee_field) == employee_id)
        return await self.scalar_one_or_none(stmt)

    async def list_users(
        self,
        *,
        include_inactive: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        stmt = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        if not include_inactive:
            stmt = stmt.where(User.is_active.is_(True))
        return await self.scalars_all(stmt)

    async def update_user(self, user: User, **updates: Any) -> User:
        return await self.update_fields(user, **updates)

    async def soft_delete_user(self, user: User) -> User:
        updates: dict[str, Any] = {"is_active": False}
        if hasattr(User, "deleted_at"):
            updates["deleted_at"] = datetime.now(tz=UTC)
        if hasattr(User, "is_deleted"):
            updates["is_deleted"] = True
        return await self.update_fields(user, **updates)

    async def activate_user(self, user: User) -> User:
        return await self.update_fields(user, is_active=True)

    async def deactivate_user(self, user: User) -> User:
        return await self.update_fields(user, is_active=False)

    async def verify_user(self, user: User) -> User:
        return await self.update_fields(user, is_verified=True)

    async def update_last_login(self, user: User, *, login_time: datetime | None = None) -> User:
        timestamp = login_time or datetime.now(tz=UTC)
        return await self.update_fields(user, last_login=timestamp)

    async def increment_failed_login(self, user: User) -> User:
        field_name = self._first_existing_field(User, self._FAILED_LOGIN_FIELDS)
        if field_name is None:
            await self.session.flush()
            return user

        current_value = getattr(user, field_name, 0) or 0
        return await self.update_fields(user, **{field_name: current_value + 1})

    async def reset_failed_login_attempts(self, user: User) -> User:
        field_name = self._first_existing_field(User, self._FAILED_LOGIN_FIELDS)
        if field_name is None:
            await self.session.flush()
            return user

        return await self.update_fields(user, **{field_name: 0})

    async def lock_account(self, user: User, *, locked_until: datetime | None = None) -> User:
        updates: dict[str, Any] = {}

        lock_flag_field = self._first_existing_field(User, self._LOCK_FLAG_FIELDS)
        if lock_flag_field is not None:
            updates[lock_flag_field] = True

        lock_until_field = self._first_existing_field(User, self._LOCK_UNTIL_FIELDS)
        if lock_until_field is not None:
            updates[lock_until_field] = locked_until or datetime.now(tz=UTC)

        if not updates:
            await self.session.flush()
            return user

        return await self.update_fields(user, **updates)

    async def unlock_account(self, user: User) -> User:
        updates: dict[str, Any] = {}

        lock_flag_field = self._first_existing_field(User, self._LOCK_FLAG_FIELDS)
        if lock_flag_field is not None:
            updates[lock_flag_field] = False

        lock_until_field = self._first_existing_field(User, self._LOCK_UNTIL_FIELDS)
        if lock_until_field is not None:
            updates[lock_until_field] = None

        if not updates:
            await self.session.flush()
            return user

        return await self.update_fields(user, **updates)

    @staticmethod
    def _first_existing_field(model: type[User], candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if hasattr(model, candidate):
                return candidate
        return None
