from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.security.token_models import TokenPair, TokenPayload


class TokenService(Protocol):
    """Contract for JWT token utility services."""

    def generate_access_token(
        self,
        *,
        subject: str,
        email: str,
        roles: list[str],
        permissions: list[str],
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        ...

    def generate_refresh_token(
        self,
        *,
        subject: str,
        email: str,
        roles: list[str],
        permissions: list[str],
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        ...

    def verify_token(self, *, token: str, expected_token_type: str | None = None) -> bool:
        ...

    def decode_token(self, *, token: str, expected_token_type: str | None = None) -> TokenPayload:
        ...

    def rotate_tokens(self, *, refresh_token: str) -> TokenPair:
        ...

    def revoke_token(self, *, token: str, reason: str = "manual_revocation") -> None:
        ...


class TokenRevocationHook(Protocol):
    """Pluggable token revocation contract for blacklist/stateful revocation stores."""

    def is_revoked(self, *, jti: str) -> bool:
        ...

    def revoke(self, *, jti: str, expires_at: datetime, metadata: dict[str, Any] | None = None) -> None:
        ...
