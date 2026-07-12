from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class TokenPayload:
    sub: str
    email: str
    roles: list[str]
    permissions: list[str]
    iat: int
    exp: int
    iss: str
    aud: str
    jti: str
    token_type: str

    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> TokenPayload:
        return cls(
            sub=str(claims["sub"]),
            email=str(claims["email"]),
            roles=[str(role) for role in claims.get("roles", [])],
            permissions=[str(permission) for permission in claims.get("permissions", [])],
            iat=int(claims["iat"]),
            exp=int(claims["exp"]),
            iss=str(claims["iss"]),
            aud=str(claims["aud"]),
            jti=str(claims["jti"]),
            token_type=str(claims.get("token_type", "access")),
        )

    @property
    def expires_at(self) -> datetime:
        return datetime.fromtimestamp(self.exp)


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
