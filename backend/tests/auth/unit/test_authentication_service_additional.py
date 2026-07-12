from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.db.models.auth import Role, User
from app.services.auth.authentication_service import AuthenticationService
from app.services.auth.dependencies import get_authentication_service
from app.services.auth.exceptions import (
    EmployeeIdAlreadyExistsError,
    InvalidCredentialsError,
    RoleNotFoundError,
)


def _run(coro):
    return asyncio.run(coro)


def _build_user(**overrides):
    base = {
        "id": uuid4(),
        "first_name": "Amina",
        "last_name": "Yusuf",
        "email": "amina@medflow.ai",
        "password_hash": "stored-hash",
        "is_active": True,
        "is_verified": True,
        "failed_login_attempts": 1,
        "refresh_token_version": 0,
        "account_locked_until": None,
        "deleted_at": None,
    }
    base.update(overrides)
    return User(**base)


def _build_service():
    user_repository = AsyncMock()
    role_repository = AsyncMock()
    password_hasher = MagicMock()
    audit_publisher = AsyncMock()

    service = AuthenticationService(
        user_repository=user_repository,
        role_repository=role_repository,
        password_hasher=password_hasher,
        audit_publisher=audit_publisher,
    )
    return service, user_repository, role_repository, password_hasher


def test_register_user_raises_for_duplicate_employee_id() -> None:
    service, user_repository, _, _, = _build_service()
    user_repository.get_by_email.return_value = None
    user_repository.get_by_employee_id.return_value = _build_user(employee_id="EMP-123")

    with pytest.raises(EmployeeIdAlreadyExistsError):
        _run(
            service.register_user(
                user_data={
                    "first_name": "A",
                    "last_name": "Y",
                    "email": "amina@medflow.ai",
                    "password": "StrongPassw0rd!",
                    "employee_id": "EMP-123",
                }
            )
        )


def test_authenticate_user_raises_for_unknown_email() -> None:
    service, user_repository, _, _, = _build_service()
    user_repository.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        _run(service.authenticate_user(email="unknown@medflow.ai", password="StrongPassw0rd!"))


def test_authenticate_user_raises_invalid_credentials_without_lock() -> None:
    service, user_repository, _, password_hasher = _build_service()
    user = _build_user(failed_login_attempts=1)
    user_repository.get_by_email.return_value = user
    user_repository.increment_failed_login.return_value = user
    password_hasher.verify_password.return_value = False

    with pytest.raises(InvalidCredentialsError):
        _run(service.authenticate_user(email=user.email, password="WrongPassw0rd!"))

    user_repository.lock_account.assert_not_awaited()


def test_change_password_success_updates_refresh_version() -> None:
    service, user_repository, _, password_hasher = _build_service()
    user = _build_user(refresh_token_version=3)
    user_repository.get_by_id.return_value = user
    user_repository.update_user.return_value = user
    password_hasher.verify_password.return_value = True
    password_hasher.hash_password.return_value = "new-hash"

    updated = _run(
        service.change_password(
            user_id=user.id,
            current_password="CurrentPassw0rd!",
            new_password="NewPassw0rd!",
            actor_user_id=user.id,
        )
    )

    assert updated is user
    call_kwargs = user_repository.update_user.await_args.kwargs
    assert call_kwargs["password_hash"] == "new-hash"
    assert call_kwargs["refresh_token_version"] == 4


def test_reset_password_request_returns_existing_user() -> None:
    service, user_repository, _, _ = _build_service()
    user = _build_user()
    user_repository.get_by_email.return_value = user

    resolved = _run(service.reset_password_request(email=user.email))

    assert resolved is user


def test_verify_and_unlock_account_paths() -> None:
    service, user_repository, _, _ = _build_service()
    user = _build_user()
    user_repository.get_by_id.return_value = user
    user_repository.verify_user.return_value = user
    user_repository.update_user.return_value = user
    user_repository.unlock_account.return_value = user
    user_repository.reset_failed_login_attempts.return_value = user

    verified = _run(service.verify_account(user_id=user.id, actor_user_id=user.id))
    unlocked = _run(service.unlock_account(user_id=user.id, actor_user_id=user.id))

    assert verified is user
    assert unlocked is user
    assert user_repository.update_user.await_count >= 2


def test_assign_default_role_raises_when_role_missing() -> None:
    service, _, role_repository, _ = _build_service()
    role_repository.get_role_by_name.return_value = None

    with pytest.raises(RoleNotFoundError):
        _run(service.assign_default_role(_build_user()))


def test_get_authentication_service_dependency_builder_returns_service() -> None:
    user_repository = AsyncMock()
    role_repository = AsyncMock()
    password_hasher = MagicMock()
    audit_publisher = AsyncMock()

    service = get_authentication_service(
        user_repository=user_repository,
        role_repository=role_repository,
        password_hasher=password_hasher,
        audit_publisher=audit_publisher,
    )

    assert isinstance(service, AuthenticationService)


def test_domain_exception_attributes_are_exposed() -> None:
    employee_error = EmployeeIdAlreadyExistsError(employee_id="EMP-123")
    role_error = RoleNotFoundError(role_name="UnknownRole")

    assert employee_error.employee_id == "EMP-123"
    assert role_error.role_name == "UnknownRole"
