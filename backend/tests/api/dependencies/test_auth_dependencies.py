from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.dependencies.auth import (
    get_current_active_user,
    get_current_user,
    get_current_verified_user,
    require_permission,
    require_role,
)
from app.services.auth.models import AuthenticatedUser


def _request_with_claims(claims: dict) -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace(jwt_claims=claims))


def _claims(**overrides: object) -> dict:
    base = {
        "sub": "4c65656a-f3be-4622-a22f-e6996cc48967",
        "email": "nurse@medflow.ai",
        "roles": ["Nurse", "Staff"],
        "permissions": ["records:read", "vitals:update"],
        "is_active": True,
        "is_verified": True,
    }
    base.update(overrides)
    return base


def test_get_current_user_returns_domain_authenticated_user() -> None:
    request = _request_with_claims(_claims())

    user = get_current_user(request)

    assert isinstance(user, AuthenticatedUser)
    assert user.sub == "4c65656a-f3be-4622-a22f-e6996cc48967"
    assert user.email == "nurse@medflow.ai"
    assert user.roles == ("Nurse", "Staff")


def test_get_current_user_raises_when_claims_missing() -> None:
    request = SimpleNamespace(state=SimpleNamespace())

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request)

    assert exc_info.value.status_code == 401


def test_get_current_active_user_raises_for_inactive_account() -> None:
    inactive_user = AuthenticatedUser(
        sub="u1",
        email="u1@medflow.ai",
        roles=("Nurse",),
        permissions=("records:read",),
        is_active=False,
        is_verified=True,
        claims={},
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(inactive_user)

    assert exc_info.value.status_code == 403


def test_get_current_verified_user_raises_for_unverified_account() -> None:
    unverified_user = AuthenticatedUser(
        sub="u1",
        email="u1@medflow.ai",
        roles=("Nurse",),
        permissions=("records:read",),
        is_active=True,
        is_verified=False,
        claims={},
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_verified_user(unverified_user)

    assert exc_info.value.status_code == 403


def test_require_role_allows_user_with_one_required_role() -> None:
    dependency = require_role("Doctor", "Nurse")
    user = AuthenticatedUser(
        sub="u1",
        email="u1@medflow.ai",
        roles=("Nurse",),
        permissions=("records:read",),
        is_active=True,
        is_verified=True,
        claims={},
    )

    result = dependency(user)

    assert result is user


def test_require_role_raises_when_user_lacks_required_roles() -> None:
    dependency = require_role("Admin")
    user = AuthenticatedUser(
        sub="u1",
        email="u1@medflow.ai",
        roles=("Nurse",),
        permissions=("records:read",),
        is_active=True,
        is_verified=True,
        claims={},
    )

    with pytest.raises(HTTPException) as exc_info:
        dependency(user)

    assert exc_info.value.status_code == 403


def test_require_permission_allows_user_with_all_permissions() -> None:
    dependency = require_permission("records:read", "vitals:update")
    user = AuthenticatedUser(
        sub="u1",
        email="u1@medflow.ai",
        roles=("Nurse",),
        permissions=("records:read", "vitals:update", "notes:create"),
        is_active=True,
        is_verified=True,
        claims={},
    )

    result = dependency(user)

    assert result is user


def test_require_permission_raises_when_user_lacks_permissions() -> None:
    dependency = require_permission("records:read", "labs:write")
    user = AuthenticatedUser(
        sub="u1",
        email="u1@medflow.ai",
        roles=("Nurse",),
        permissions=("records:read",),
        is_active=True,
        is_verified=True,
        claims={},
    )

    with pytest.raises(HTTPException) as exc_info:
        dependency(user)

    assert exc_info.value.status_code == 403