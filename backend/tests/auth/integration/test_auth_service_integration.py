from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.db.models.auth import Role, User
from app.services.auth.authentication_service import AuthenticationService


def _run(coro):
    return asyncio.run(coro)


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    async def create_user(self, **user_data):
        user = User(id=uuid4(), failed_login_attempts=0, refresh_token_version=0, **user_data)
        self.users[user.id] = user
        return user

    async def get_by_id(self, user_id: UUID):
        return self.users.get(user_id)

    async def get_by_email(self, email: str):
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_by_employee_id(self, employee_id: str):
        for user in self.users.values():
            if user.employee_id == employee_id:
                return user
        return None

    async def increment_failed_login(self, user: User):
        user.failed_login_attempts += 1
        return user

    async def update_user(self, user: User, **updates):
        for key, value in updates.items():
            setattr(user, key, value)
        return user

    async def reset_failed_login_attempts(self, user: User):
        user.failed_login_attempts = 0
        return user

    async def unlock_account(self, user: User):
        user.account_locked_until = None
        return user

    async def update_last_login(self, user: User):
        user.last_login = datetime.now(tz=UTC)
        return user

    async def verify_user(self, user: User):
        user.is_verified = True
        return user

    async def lock_account(self, user: User, *, locked_until):
        user.account_locked_until = locked_until
        return user


class InMemoryRoleRepository:
    def __init__(self):
        self.role = Role(id=2, name="Doctor", description="Clinical")
        self.assignments: list[tuple[UUID, int]] = []

    async def get_role_by_name(self, name: str):
        if name == self.role.name:
            return self.role
        return None

    async def assign_role(self, user_id: UUID, role_id: int):
        self.assignments.append((user_id, role_id))
        return None


class PlainPasswordHasher:
    def hash_password(self, raw_password: str) -> str:
        return f"hashed::{raw_password}"

    def verify_password(self, raw_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed::{raw_password}"


class InMemoryAuditPublisher:
    def __init__(self):
        self.events: list[dict] = []

    async def publish(self, **event):
        self.events.append(event)


def test_integration_register_then_authenticate_success() -> None:
    user_repo = InMemoryUserRepository()
    role_repo = InMemoryRoleRepository()
    audit = InMemoryAuditPublisher()
    service = AuthenticationService(
        user_repository=user_repo,
        role_repository=role_repo,
        password_hasher=PlainPasswordHasher(),
        audit_publisher=audit,
    )

    registered = _run(
        service.register_user(
            user_data={
                "first_name": "Amina",
                "last_name": "Yusuf",
                "email": "amina@medflow.ai",
                "password": "StrongPassw0rd!",
                "is_active": True,
                "is_verified": True,
            }
        )
    )
    authenticated = _run(service.authenticate_user(email="amina@medflow.ai", password="StrongPassw0rd!"))

    assert registered.id == authenticated.id
    assert role_repo.assignments == [(registered.id, role_repo.role.id)]
    assert any(event["event_type"] == "auth.registration.success" for event in audit.events)
    assert any(event["event_type"] == "auth.login.success" for event in audit.events)


def test_integration_reset_password_updates_hash_and_version() -> None:
    user_repo = InMemoryUserRepository()
    role_repo = InMemoryRoleRepository()
    audit = InMemoryAuditPublisher()
    service = AuthenticationService(
        user_repository=user_repo,
        role_repository=role_repo,
        password_hasher=PlainPasswordHasher(),
        audit_publisher=audit,
    )

    user = _run(
        user_repo.create_user(
            first_name="Amina",
            last_name="Yusuf",
            email="amina@medflow.ai",
            password_hash="hashed::OldPassw0rd!",
            is_active=True,
            is_verified=True,
        )
    )

    updated = _run(service.reset_password(user_id=user.id, new_password="ResetPassw0rd!"))

    assert updated.password_hash == "hashed::ResetPassw0rd!"
    assert updated.refresh_token_version == 1
    assert any(event["event_type"] == "auth.password_reset.success" for event in audit.events)
