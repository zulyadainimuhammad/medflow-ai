from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request, status
from app.services.auth.models import AuthenticatedUser


def _build_authenticated_user_from_claims(claims: dict[str, Any]) -> AuthenticatedUser:
    return AuthenticatedUser(
        sub=str(claims.get("sub", "")),
        email=str(claims.get("email", "")),
        roles=tuple(str(role) for role in claims.get("roles", [])),
        permissions=tuple(str(permission) for permission in claims.get("permissions", [])),
        is_active=bool(claims.get("is_active", True)),
        is_verified=bool(claims.get("is_verified", True)),
        claims=claims,
    )


def get_current_user(request: Request) -> AuthenticatedUser:
    claims = getattr(request.state, "jwt_claims", None)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return _build_authenticated_user_from_claims(claims)


def get_current_active_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account",
        )
    return current_user


def get_current_verified_user(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> AuthenticatedUser:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not verified",
        )
    return current_user


def require_role(*required_roles: str):
    required = {role.strip() for role in required_roles if role.strip()}

    def dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
        if not required:
            return current_user

        user_roles = set(current_user.roles)
        if user_roles.isdisjoint(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions",
            )
        return current_user

    return dependency


def require_permission(*required_permissions: str):
    required = {permission.strip() for permission in required_permissions if permission.strip()}

    def dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
        if not required:
            return current_user

        user_permissions = set(current_user.permissions)
        if not required.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission scope",
            )
        return current_user

    return dependency


# Backward-compatible aliases for existing imports.
role_checker = require_role
permission_checker = require_permission
