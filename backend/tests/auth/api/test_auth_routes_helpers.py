from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth import routes as auth_routes
from app.api.dependencies.auth import get_current_active_user
from app.db.models.auth import Permission, Role, User
from app.main import app
from app.services.auth.exceptions import (
    AccountDeletedError,
    AccountInactiveError,
    AccountLockedError,
    AccountNotVerifiedError,
    InvalidCredentialsError,
    PasswordChangeRejectedError,
    RoleNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.services.auth.models import AuthenticatedUser


def _run(coro):
    return asyncio.run(coro)


class RoleRepo:
    async def get_user_roles(self, user_id):
        return [Role(id=2, name="Doctor", description="Clinical")]


class PermissionRepo:
    async def get_permissions_for_role(self, role_id):
        return [Permission(id=1, role_id=role_id, name="diagnostics:read", description="Read")]


class TokenSvc:
    def generate_access_token(self, **kwargs):
        return "access-token"

    def generate_refresh_token(self, **kwargs):
        return "refresh-token"


def test_map_auth_error_translates_expected_http_statuses() -> None:
    cases = [
        (UserAlreadyExistsError(email="a@b.com"), 409),
        (InvalidCredentialsError("bad"), 401),
        (AccountInactiveError("inactive"), 403),
        (AccountDeletedError("deleted"), 403),
        (AccountNotVerifiedError("unverified"), 403),
        (AccountLockedError(locked_until=None), 423),
        (UserNotFoundError(user_id=uuid4()), 404),
        (RoleNotFoundError(role_name="Unknown"), 404),
        (PasswordChangeRejectedError("bad"), 400),
        (Exception("other"), 500),
    ]

    for error, expected_status in cases:
        http_error = auth_routes._map_auth_error(error)
        assert isinstance(http_error, HTTPException)
        assert http_error.status_code == expected_status


def test_dependency_builders_return_expected_types() -> None:
    assert isinstance(auth_routes.get_password_hasher_dependency(), auth_routes.PasswordHasherAdapter)
    assert isinstance(auth_routes.get_audit_publisher_dependency(), auth_routes.NoOpAuthAuditPublisher)
    assert auth_routes.get_token_service_dependency() is not None


def test_repository_dependency_builders_wrap_session() -> None:
    session = object()

    user_repo = auth_routes.get_user_repository_dependency(session=session)
    role_repo = auth_routes.get_role_repository_dependency(session=session)
    permission_repo = auth_routes.get_permission_repository_dependency(session=session)

    assert user_repo.session is session
    assert role_repo.session is session
    assert permission_repo.session is session


def test_build_user_summary_and_login_response() -> None:
    user = User(
        id=uuid4(),
        first_name="Amina",
        last_name="Yusuf",
        email="amina@medflow.ai",
        password_hash="hashed",
        is_active=True,
        is_verified=True,
    )
    summary = auth_routes._build_user_summary(user)
    assert summary.email == "amina@medflow.ai"

    response = _run(
        auth_routes._build_login_response(
            user=user,
            token_service=TokenSvc(),
            role_repository=RoleRepo(),
            permission_repository=PermissionRepo(),
        )
    )
    assert response.token.access_token == "access-token"
    assert response.user.id == user.id


def test_roles_endpoint_and_password_routes_handle_invalid_subjects() -> None:
    class AuthService:
        async def change_password(self, **kwargs):
            return None

    class TokenService:
        def decode_token(self, *, token, expected_token_type=None):
            class Payload:
                sub = "not-a-uuid"

            return Payload()

    app.dependency_overrides[auth_routes.get_authentication_service_dependency] = lambda: AuthService()
    app.dependency_overrides[auth_routes.get_token_service_dependency] = lambda: TokenService()
    app.dependency_overrides[auth_routes.get_role_repository_dependency] = lambda: RoleRepo()
    app.dependency_overrides[auth_routes.get_permission_repository_dependency] = lambda: PermissionRepo()
    app.dependency_overrides[get_current_active_user] = lambda: AuthenticatedUser(
        sub="not-a-uuid",
        email="doctor@medflow.ai",
        roles=("Doctor",),
        permissions=("diagnostics:read",),
        is_active=True,
        is_verified=True,
        claims={},
    )

    with TestClient(app) as client:
        change_response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "CurrentPassw0rd!", "new_password": "NewPassw0rd!"},
        )
        roles_response = client.get("/api/v1/auth/roles")
        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={"reset_token": "anything", "new_password": "ResetPassw0rd!"},
        )

    app.dependency_overrides.clear()

    assert change_response.status_code == 401
    assert roles_response.status_code == 401
    assert reset_response.status_code == 400
