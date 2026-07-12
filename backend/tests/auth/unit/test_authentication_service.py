from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.db.models.auth import Role, User
from app.services.auth.authentication_service import AuthenticationService
from app.services.auth.exceptions import (
    AccountDeletedError,
    AccountInactiveError,
    AccountLockedError,
    AccountNotVerifiedError,
    PasswordChangeRejectedError,
    UserAlreadyExistsError,
    UserNotFoundError,
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
        "failed_login_attempts": 0,
        "refresh_token_version": 0,
        "account_locked_until": None,
        "deleted_at": None,
    }
    base.update(overrides)
    return User(**base)


def _build_service(*, require_verified_for_login: bool = False):
    user_repository = AsyncMock()
    role_repository = AsyncMock()
    password_hasher = MagicMock()
    audit_publisher = AsyncMock()

    service = AuthenticationService(
        user_repository=user_repository,
        role_repository=role_repository,
        password_hasher=password_hasher,
        audit_publisher=audit_publisher,
        require_verified_for_login=require_verified_for_login,
    )
    return service, user_repository, role_repository, password_hasher, audit_publisher


def test_register_user_success_normalizes_email_hashes_password_and_assigns_default_role() -> None:
    service, user_repository, role_repository, password_hasher, _ = _build_service()
    user = _build_user(email="amina.yusuf@medflow.ai")
    role_repository.get_role_by_name.return_value = Role(id=2, name="Doctor", description="Clinical")
    user_repository.get_by_email.return_value = None
    user_repository.get_by_employee_id.return_value = None
    user_repository.create_user.return_value = user
    password_hasher.hash_password.return_value = "hashed-value"

    created = _run(
        service.register_user(
            user_data={
                "first_name": "Amina",
                "last_name": "Yusuf",
                "email": "AMINA.YUSUF@MEDFLOW.AI",
                "password": "StrongPassw0rd!",
                "employee_id": "EMP-001",
            }
        )
    )

    assert created is user
    user_repository.create_user.assert_awaited_once()
    payload = user_repository.create_user.await_args.kwargs
    assert payload["email"] == "amina.yusuf@medflow.ai"
    assert payload["password_hash"] == "hashed-value"
    password_hasher.hash_password.assert_called_once_with("StrongPassw0rd!")


def test_register_user_raises_for_duplicate_email() -> None:
    service, user_repository, _, _, _ = _build_service()
    user_repository.get_by_email.return_value = _build_user(email="exists@medflow.ai")

    with pytest.raises(UserAlreadyExistsError):
        _run(
            service.register_user(
                user_data={
                    "first_name": "A",
                    "last_name": "Y",
                    "email": "exists@medflow.ai",
                    "password": "StrongPassw0rd!",
                }
            )
        )


def test_authenticate_user_success_resets_attempts_and_updates_login() -> None:
    service, user_repository, _, password_hasher, _ = _build_service()
    user = _build_user(failed_login_attempts=2)
    user_repository.get_by_email.return_value = user
    password_hasher.verify_password.return_value = True

    authenticated = _run(service.authenticate_user(email=user.email, password="StrongPassw0rd!"))

    assert authenticated is user
    user_repository.reset_failed_login_attempts.assert_awaited_once_with(user)
    user_repository.unlock_account.assert_awaited_once_with(user)
    user_repository.update_last_login.assert_awaited_once_with(user)


def test_authenticate_user_raises_and_locks_when_threshold_reached() -> None:
    service, user_repository, _, password_hasher, _ = _build_service()
    user = _build_user(failed_login_attempts=5)
    user_repository.get_by_email.return_value = user
    password_hasher.verify_password.return_value = False
    user_repository.increment_failed_login.return_value = user
    user_repository.lock_account.return_value = user

    with pytest.raises(AccountLockedError):
        _run(service.authenticate_user(email=user.email, password="WrongPassw0rd!"))

    user_repository.lock_account.assert_awaited_once()


def test_change_password_rejects_wrong_current_password() -> None:
    service, user_repository, _, password_hasher, _ = _build_service()
    user = _build_user()
    user_repository.get_by_id.return_value = user
    password_hasher.verify_password.return_value = False

    with pytest.raises(PasswordChangeRejectedError):
        _run(
            service.change_password(
                user_id=user.id,
                current_password="WrongPassw0rd!",
                new_password="NewPassw0rd!",
            )
        )


def test_change_password_raises_for_missing_user() -> None:
    service, user_repository, _, _, _ = _build_service()
    user_repository.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        _run(
            service.change_password(
                user_id=uuid4(),
                current_password="CurrentPassw0rd!",
                new_password="NewPassw0rd!",
            )
        )


def test_validate_account_status_raises_expected_domain_errors() -> None:
    service, *_ = _build_service(require_verified_for_login=True)

    with pytest.raises(AccountDeletedError):
        service.validate_account_status(_build_user(deleted_at=datetime.now(tz=UTC)))

    with pytest.raises(AccountInactiveError):
        service.validate_account_status(_build_user(is_active=False))

    with pytest.raises(AccountNotVerifiedError):
        service.validate_account_status(_build_user(is_verified=False))

    with pytest.raises(AccountLockedError):
        service.validate_account_status(
            _build_user(account_locked_until=datetime.now(tz=UTC) + timedelta(minutes=5))
        )
