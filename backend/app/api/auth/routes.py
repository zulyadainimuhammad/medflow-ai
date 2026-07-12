from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import AuthenticatedUser, get_current_active_user
from app.db.models.auth import User
from app.db.session import get_async_session
from app.repositories.auth.permission_repository import PermissionRepository
from app.repositories.auth.role_repository import RoleRepository
from app.repositories.auth.user_repository import UserRepository
from app.schemas.auth import (
    AuthenticatedUserRead,
    AuthMessageResponse,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RoleRead,
    Token,
    UserCreate,
    UserSummary,
)
from app.security import Argon2PasswordHasher
from app.security.token_dependencies import get_token_service
from app.security.token_exceptions import (
    TokenDecodeError,
    TokenExpiredError,
    TokenServiceError,
    TokenTypeError,
)
from app.security.token_interfaces import TokenService
from app.security.token_models import TokenPair
from app.services.auth import (
    AccountDeletedError,
    AccountInactiveError,
    AccountLockedError,
    AccountNotVerifiedError,
    EmployeeIdAlreadyExistsError,
    InvalidCredentialsError,
    PasswordChangeRejectedError,
    RoleNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.services.auth.authentication_service import AuthenticationService
from app.services.auth.dependencies import get_authentication_service
from app.services.auth.ports import AuthAuditEventPublisher, PasswordHasher

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


class NoOpAuthAuditPublisher(AuthAuditEventPublisher):
    async def publish(
        self,
        *,
        event_type: str,
        occurred_at,
        user_id,
        email,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        return None


class PasswordHasherAdapter(PasswordHasher):
    def __init__(self, hasher: Argon2PasswordHasher) -> None:
        self._hasher = hasher

    def hash_password(self, raw_password: str) -> str:
        return self._hasher.hash(raw_password)

    def verify_password(self, raw_password: str, password_hash: str) -> bool:
        return self._hasher.verify(raw_password, password_hash)


def get_token_service_dependency() -> TokenService:
    return get_token_service()


def get_password_hasher_dependency() -> PasswordHasher:
    return PasswordHasherAdapter(Argon2PasswordHasher())


def get_audit_publisher_dependency() -> AuthAuditEventPublisher:
    return NoOpAuthAuditPublisher()


def get_user_repository_dependency(
    session: AsyncSession = Depends(get_async_session),
) -> UserRepository:
    return UserRepository(session=session)


def get_role_repository_dependency(
    session: AsyncSession = Depends(get_async_session),
) -> RoleRepository:
    return RoleRepository(session=session)


def get_permission_repository_dependency(
    session: AsyncSession = Depends(get_async_session),
) -> PermissionRepository:
    return PermissionRepository(session=session)


def get_authentication_service_dependency(
    user_repository: UserRepository = Depends(get_user_repository_dependency),
    role_repository: RoleRepository = Depends(get_role_repository_dependency),
    password_hasher: PasswordHasher = Depends(get_password_hasher_dependency),
    audit_publisher: AuthAuditEventPublisher = Depends(get_audit_publisher_dependency),
) -> AuthenticationService:
    return get_authentication_service(
        user_repository=user_repository,
        role_repository=role_repository,
        password_hasher=password_hasher,
        audit_publisher=audit_publisher,
    )


def _map_auth_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (UserAlreadyExistsError, EmployeeIdAlreadyExistsError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, InvalidCredentialsError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if isinstance(exc, (AccountInactiveError, AccountDeletedError, AccountNotVerifiedError)):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, AccountLockedError):
        return HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc))
    if isinstance(exc, (UserNotFoundError, RoleNotFoundError)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PasswordChangeRejectedError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, TokenExpiredError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    if isinstance(exc, (TokenDecodeError, TokenTypeError, TokenServiceError)):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication error")


def _build_user_summary(user: User) -> UserSummary:
    return UserSummary.model_validate(
        {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }
    )


async def _build_roles_for_user(
    *,
    user_id: UUID,
    role_repository: RoleRepository,
    permission_repository: PermissionRepository,
) -> list[RoleRead]:
    roles = await role_repository.get_user_roles(user_id)
    role_payloads: list[dict[str, Any]] = []
    for role in roles:
        permissions = await permission_repository.get_permissions_for_role(role.id)
        role_payloads.append(
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": [
                    {
                        "id": permission.id,
                        "name": permission.name,
                        "description": permission.description,
                    }
                    for permission in permissions
                ],
            }
        )
    return [RoleRead.model_validate(item) for item in role_payloads]


async def _build_login_response(
    *,
    user: User,
    token_service: TokenService,
    role_repository: RoleRepository,
    permission_repository: PermissionRepository,
) -> LoginResponse:
    roles = await _build_roles_for_user(
        user_id=user.id,
        role_repository=role_repository,
        permission_repository=permission_repository,
    )
    role_names = [role.name for role in roles]
    permission_names = [permission.name for role in roles for permission in role.permissions]

    access_token = token_service.generate_access_token(
        subject=str(user.id),
        email=user.email,
        roles=role_names,
        permissions=permission_names,
        additional_claims={
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        },
    )
    refresh_token = token_service.generate_refresh_token(
        subject=str(user.id),
        email=user.email,
        roles=role_names,
        permissions=permission_names,
        additional_claims={
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        },
    )

    return LoginResponse(
        token=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15")) * 60,
        ),
        user=_build_user_summary(user),
    )


@router.post(
    "/register",
    response_model=UserSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    description="Create a new user account via AuthenticationService.",
    responses={
        201: {"description": "User registered successfully."},
        409: {
            "description": "User or employee ID already exists.",
            "content": {
                "application/json": {
                    "example": {"detail": "User already exists for email=amina.yusuf@medflow.ai"}
                }
            },
        },
    },
)
async def register(
    payload: UserCreate,
    auth_service: AuthenticationService = Depends(get_authentication_service_dependency),
) -> UserSummary:
    try:
        user = await auth_service.register_user(user_data=payload.model_dump())
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc
    return _build_user_summary(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate user",
    description="Validate credentials and return access/refresh tokens.",
    responses={
        200: {"description": "Authentication successful."},
        401: {
            "description": "Invalid credentials.",
            "content": {"application/json": {"example": {"detail": "Invalid credentials"}}},
        },
        403: {
            "description": "Account status does not allow login.",
            "content": {"application/json": {"example": {"detail": "Account is inactive"}}},
        },
    },
)
async def login(
    payload: LoginRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service_dependency),
    token_service: TokenService = Depends(get_token_service_dependency),
    role_repository: RoleRepository = Depends(get_role_repository_dependency),
    permission_repository: PermissionRepository = Depends(get_permission_repository_dependency),
) -> LoginResponse:
    try:
        user = await auth_service.authenticate_user(email=payload.email, password=payload.password)
        return await _build_login_response(
            user=user,
            token_service=token_service,
            role_repository=role_repository,
            permission_repository=permission_repository,
        )
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Rotate refresh token and return a fresh token pair.",
    responses={
        200: {"description": "Token refreshed successfully."},
        401: {
            "description": "Refresh token is invalid or expired.",
            "content": {"application/json": {"example": {"detail": "Invalid token"}}},
        },
    },
)
async def refresh(
    payload: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service_dependency),
) -> Token:
    try:
        token_pair: TokenPair = token_service.rotate_tokens(refresh_token=payload.refresh_token)
        return Token(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type="bearer",
            expires_in=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15")) * 60,
        )
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    summary="Logout user",
    description="Revoke provided refresh token and optionally bearer access token.",
)
async def logout(
    payload: RefreshTokenRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token_service: TokenService = Depends(get_token_service_dependency),
) -> AuthMessageResponse:
    try:
        token_service.revoke_token(token=payload.refresh_token, reason="logout")
        if authorization and authorization.lower().startswith("bearer "):
            bearer_token = authorization.split(" ", 1)[1].strip()
            if bearer_token:
                token_service.revoke_token(token=bearer_token, reason="logout")
        return AuthMessageResponse(message="Logout successful")
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc


@router.post(
    "/change-password",
    response_model=AuthMessageResponse,
    summary="Change password",
    description="Change current authenticated user's password via AuthenticationService.",
    responses={
        200: {"description": "Password changed."},
        400: {"description": "Current password is invalid."},
        401: {"description": "Authentication required."},
    },
)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(get_authentication_service_dependency),
) -> AuthMessageResponse:
    try:
        user_id = UUID(current_user.sub)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier") from exc

    try:
        await auth_service.change_password(
            user_id=user_id,
            current_password=payload.current_password,
            new_password=payload.new_password,
            actor_user_id=user_id,
        )
        return AuthMessageResponse(message="Password changed successfully")
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc


@router.post(
    "/forgot-password",
    response_model=AuthMessageResponse,
    summary="Start password reset",
    description="Accept password reset request without disclosing user existence.",
)
async def forgot_password(
    payload: PasswordResetRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service_dependency),
) -> AuthMessageResponse:
    try:
        await auth_service.reset_password_request(email=payload.email)
        return AuthMessageResponse(
            message="If an account exists for this email, a reset instruction has been issued"
        )
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc


@router.post(
    "/reset-password",
    response_model=AuthMessageResponse,
    summary="Confirm password reset",
    description="Validate reset token and set a new password.",
)
async def reset_password(
    payload: PasswordResetConfirm,
    auth_service: AuthenticationService = Depends(get_authentication_service_dependency),
    token_service: TokenService = Depends(get_token_service_dependency),
) -> AuthMessageResponse:
    try:
        token_payload = token_service.decode_token(token=payload.reset_token)
        user_id = UUID(token_payload.sub)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token subject") from exc
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc

    try:
        await auth_service.reset_password(user_id=user_id, new_password=payload.new_password)
        return AuthMessageResponse(message="Password reset successfully")
    except Exception as exc:  # pragma: no cover - routing safety net
        raise _map_auth_error(exc) from exc


@router.get(
    "/me",
    response_model=AuthenticatedUserRead,
    summary="Get current user",
    description="Return the current authenticated user principal extracted from token claims.",
    responses={
        200: {"description": "Current user returned."},
        401: {"description": "Authentication required."},
    },
)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> AuthenticatedUserRead:
    return AuthenticatedUserRead(
        sub=current_user.sub,
        email=current_user.email,
        roles=list(current_user.roles),
        permissions=list(current_user.permissions),
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


@router.get(
    "/roles",
    response_model=list[RoleRead],
    summary="Get current user roles",
    description="Return roles and permissions for the current authenticated user.",
)
async def get_my_roles(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    role_repository: RoleRepository = Depends(get_role_repository_dependency),
    permission_repository: PermissionRepository = Depends(get_permission_repository_dependency),
) -> list[RoleRead]:
    try:
        user_id = UUID(current_user.sub)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier") from exc

    return await _build_roles_for_user(
        user_id=user_id,
        role_repository=role_repository,
        permission_repository=permission_repository,
    )