from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


class SchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PermissionRead(SchemaBase):
    id: int
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "manage_users",
                "description": "Can create and update user accounts",
            }
        },
    )


class RoleRead(SchemaBase):
    id: int
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    permissions: list[PermissionRead] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Administrator",
                "description": "Full platform administration for MedFlow AI.",
                "permissions": [
                    {
                        "id": 1,
                        "name": "manage_users",
                        "description": "Can create and update user accounts",
                    }
                ],
            }
        },
    )


class UserBase(SchemaBase):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone_number: str | None = Field(default=None, min_length=8, max_length=16)
    is_active: bool = True
    is_verified: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not PHONE_REGEX.fullmatch(value):
            raise ValueError(
                "phone_number must be in international format, e.g. +2348012345678"
            )
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "first_name": "Amina",
                "last_name": "Yusuf",
                "email": "amina.yusuf@medflow.ai",
                "phone_number": "+2348012345678",
                "is_active": True,
                "is_verified": False,
            }
        },
    )


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_upper = any(char.isupper() for char in value)
        has_lower = any(char.islower() for char in value)
        has_digit = any(char.isdigit() for char in value)
        has_special = any(not char.isalnum() for char in value)

        if not all((has_upper, has_lower, has_digit, has_special)):
            raise ValueError(
                "password must contain uppercase, lowercase, number, and special character"
            )
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "first_name": "Amina",
                "last_name": "Yusuf",
                "email": "amina.yusuf@medflow.ai",
                "phone_number": "+2348012345678",
                "password": "StrongPassw0rd!",
                "is_active": True,
                "is_verified": False,
            }
        },
    )


class UserUpdate(SchemaBase):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=8, max_length=16)
    is_active: bool | None = None
    is_verified: bool | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not PHONE_REGEX.fullmatch(value):
            raise ValueError(
                "phone_number must be in international format, e.g. +2348012345678"
            )
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "phone_number": "+2348098765432",
                "is_verified": True,
            }
        },
    )


class UserSummary(SchemaBase):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "d1f0c2e1-b6d3-4e56-a70e-0f4f8cb851ae",
                "first_name": "Amina",
                "last_name": "Yusuf",
                "email": "amina.yusuf@medflow.ai",
                "is_active": True,
                "is_verified": True,
            }
        },
    )


class UserRead(UserSummary):
    phone_number: str | None = None
    last_login: datetime | None = None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleRead] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "d1f0c2e1-b6d3-4e56-a70e-0f4f8cb851ae",
                "first_name": "Amina",
                "last_name": "Yusuf",
                "email": "amina.yusuf@medflow.ai",
                "phone_number": "+2348012345678",
                "is_active": True,
                "is_verified": True,
                "last_login": "2026-07-12T10:02:43Z",
                "created_at": "2026-07-01T08:00:00Z",
                "updated_at": "2026-07-12T10:02:43Z",
                "roles": [
                    {
                        "id": 2,
                        "name": "Doctor",
                        "description": "Clinical requester for diagnostic workflows.",
                        "permissions": [],
                    }
                ],
            }
        },
    )


class LoginRequest(SchemaBase):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "amina.yusuf@medflow.ai",
                "password": "StrongPassw0rd!",
            }
        },
    )


class Token(SchemaBase):
    access_token: str = Field(min_length=1)
    refresh_token: str = Field(min_length=1)
    token_type: str = Field(default="bearer", min_length=3, max_length=20)
    expires_in: int = Field(ge=1, description="Access token TTL in seconds")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "access_token": "<opaque-or-jwt-access-token>",
                "refresh_token": "<opaque-or-jwt-refresh-token>",
                "token_type": "bearer",
                "expires_in": 900,
            }
        },
    )


class LoginResponse(SchemaBase):
    token: Token
    user: UserSummary

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "token": {
                    "access_token": "<opaque-or-jwt-access-token>",
                    "refresh_token": "<opaque-or-jwt-refresh-token>",
                    "token_type": "bearer",
                    "expires_in": 900,
                },
                "user": {
                    "id": "d1f0c2e1-b6d3-4e56-a70e-0f4f8cb851ae",
                    "first_name": "Amina",
                    "last_name": "Yusuf",
                    "email": "amina.yusuf@medflow.ai",
                    "is_active": True,
                    "is_verified": True,
                },
            }
        },
    )


class RefreshTokenRequest(SchemaBase):
    refresh_token: str = Field(min_length=1)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"refresh_token": "<opaque-or-jwt-refresh-token>"}},
    )


class PasswordChangeRequest(SchemaBase):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        has_upper = any(char.isupper() for char in value)
        has_lower = any(char.islower() for char in value)
        has_digit = any(char.isdigit() for char in value)
        has_special = any(not char.isalnum() for char in value)

        if not all((has_upper, has_lower, has_digit, has_special)):
            raise ValueError(
                "new_password must contain uppercase, lowercase, number, and special character"
            )
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "current_password": "CurrentPassw0rd!",
                "new_password": "NewPassw0rd!",
            }
        },
    )


class PasswordResetRequest(SchemaBase):
    email: EmailStr

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"email": "amina.yusuf@medflow.ai"}},
    )


class PasswordResetConfirm(SchemaBase):
    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        has_upper = any(char.isupper() for char in value)
        has_lower = any(char.islower() for char in value)
        has_digit = any(char.isdigit() for char in value)
        has_special = any(not char.isalnum() for char in value)

        if not all((has_upper, has_lower, has_digit, has_special)):
            raise ValueError(
                "new_password must contain uppercase, lowercase, number, and special character"
            )
        return value

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "reset_token": "<password-reset-token>",
                "new_password": "ResetPassw0rd!",
            }
        },
    )


class AuthMessageResponse(SchemaBase):
    message: str = Field(min_length=1, max_length=500)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully.",
            }
        },
    )


class AuthenticatedUserRead(SchemaBase):
    sub: str = Field(min_length=1)
    email: EmailStr
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = True

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "sub": "d1f0c2e1-b6d3-4e56-a70e-0f4f8cb851ae",
                "email": "amina.yusuf@medflow.ai",
                "roles": ["Doctor"],
                "permissions": ["diagnostics:read", "diagnostics:create"],
                "is_active": True,
                "is_verified": True,
            }
        },
    )
