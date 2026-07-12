from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_active_user, require_permission, require_role
from app.services.auth.models import AuthenticatedUser


def _app_with_overrides(user: AuthenticatedUser) -> FastAPI:
    test_app = FastAPI()

    @test_app.get("/rbac/role", dependencies=[Depends(require_role("Admin"))])
    def role_guarded() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.get("/rbac/permission", dependencies=[Depends(require_permission("users:write"))])
    def permission_guarded() -> dict[str, str]:
        return {"status": "ok"}

    test_app.dependency_overrides[get_current_active_user] = lambda: user
    return test_app


def test_require_role_allows_authorized_user() -> None:
    app = _app_with_overrides(
        AuthenticatedUser(
            sub="u-1",
            email="admin@medflow.ai",
            roles=("Admin",),
            permissions=("users:read",),
            is_active=True,
            is_verified=True,
            claims={},
        )
    )
    with TestClient(app) as client:
        response = client.get("/rbac/role")

    assert response.status_code == 200


def test_require_role_blocks_unauthorized_user() -> None:
    app = _app_with_overrides(
        AuthenticatedUser(
            sub="u-2",
            email="doctor@medflow.ai",
            roles=("Doctor",),
            permissions=("users:read",),
            is_active=True,
            is_verified=True,
            claims={},
        )
    )
    with TestClient(app) as client:
        response = client.get("/rbac/role")

    assert response.status_code == 403


def test_require_permission_allows_authorized_user() -> None:
    app = _app_with_overrides(
        AuthenticatedUser(
            sub="u-3",
            email="manager@medflow.ai",
            roles=("Manager",),
            permissions=("users:write", "users:read"),
            is_active=True,
            is_verified=True,
            claims={},
        )
    )
    with TestClient(app) as client:
        response = client.get("/rbac/permission")

    assert response.status_code == 200


def test_require_permission_blocks_unauthorized_user() -> None:
    app = _app_with_overrides(
        AuthenticatedUser(
            sub="u-4",
            email="nurse@medflow.ai",
            roles=("Nurse",),
            permissions=("users:read",),
            is_active=True,
            is_verified=True,
            claims={},
        )
    )
    with TestClient(app) as client:
        response = client.get("/rbac/permission")

    assert response.status_code == 403
