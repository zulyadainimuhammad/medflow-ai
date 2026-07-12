from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
)

from app.security.token_exceptions import (
    TokenDecodeError,
    TokenExpiredError,
    TokenInvalidAudienceError,
    TokenInvalidIssuerError,
    TokenRevokedError,
    TokenTypeError,
)
from app.security.token_interfaces import TokenRevocationHook
from app.security.token_models import TokenPair, TokenPayload


class JWTTokenService:
    def __init__(
        self,
        *,
        secret_key: str,
        issuer: str,
        audience: str,
        algorithm: str = "HS256",
        access_token_ttl: timedelta = timedelta(minutes=15),
        refresh_token_ttl: timedelta = timedelta(days=7),
        revocation_hook: TokenRevocationHook | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._secret_key = secret_key
        self._issuer = issuer
        self._audience = audience
        self._algorithm = algorithm
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl
        self._revocation_hook = revocation_hook
        self._now_provider = now_provider or (lambda: datetime.now(tz=UTC))

    def generate_access_token(
        self,
        *,
        subject: str,
        email: str,
        roles: list[str],
        permissions: list[str],
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        return self._generate_token(
            token_type="access",
            ttl=self._access_token_ttl,
            subject=subject,
            email=email,
            roles=roles,
            permissions=permissions,
            additional_claims=additional_claims,
        )

    def generate_refresh_token(
        self,
        *,
        subject: str,
        email: str,
        roles: list[str],
        permissions: list[str],
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        return self._generate_token(
            token_type="refresh",
            ttl=self._refresh_token_ttl,
            subject=subject,
            email=email,
            roles=roles,
            permissions=permissions,
            additional_claims=additional_claims,
        )

    def verify_token(self, *, token: str, expected_token_type: str | None = None) -> bool:
        payload = self.decode_token(token=token, expected_token_type=expected_token_type)
        return payload is not None

    def decode_token(self, *, token: str, expected_token_type: str | None = None) -> TokenPayload:
        claims = self._decode_claims(token)

        payload = TokenPayload.from_claims(claims)
        if expected_token_type is not None and payload.token_type != expected_token_type:
            raise TokenTypeError(
                f"Expected token_type={expected_token_type}, got token_type={payload.token_type}"
            )

        if self._revocation_hook is not None and self._revocation_hook.is_revoked(jti=payload.jti):
            raise TokenRevokedError("Token has been revoked")

        return payload

    def rotate_tokens(self, *, refresh_token: str) -> TokenPair:
        refresh_payload = self.decode_token(token=refresh_token, expected_token_type="refresh")

        if self._revocation_hook is not None:
            self._revocation_hook.revoke(
                jti=refresh_payload.jti,
                expires_at=refresh_payload.expires_at,
                metadata={"reason": "rotation", "token_type": "refresh"},
            )

        access_token = self.generate_access_token(
            subject=refresh_payload.sub,
            email=refresh_payload.email,
            roles=refresh_payload.roles,
            permissions=refresh_payload.permissions,
        )
        new_refresh_token = self.generate_refresh_token(
            subject=refresh_payload.sub,
            email=refresh_payload.email,
            roles=refresh_payload.roles,
            permissions=refresh_payload.permissions,
        )

        return TokenPair(access_token=access_token, refresh_token=new_refresh_token)

    def revoke_token(self, *, token: str, reason: str = "manual_revocation") -> None:
        if self._revocation_hook is None:
            return

        payload = self.decode_token(token=token)
        self._revocation_hook.revoke(
            jti=payload.jti,
            expires_at=payload.expires_at,
            metadata={"reason": reason, "token_type": payload.token_type},
        )

    def _generate_token(
        self,
        *,
        token_type: str,
        ttl: timedelta,
        subject: str,
        email: str,
        roles: list[str],
        permissions: list[str],
        additional_claims: dict[str, Any] | None,
    ) -> str:
        now = self._now_provider()
        expires_at = now + ttl
        claims: dict[str, Any] = {
            "sub": subject,
            "email": email,
            "roles": roles,
            "permissions": permissions,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": self._issuer,
            "aud": self._audience,
            "jti": str(uuid4()),
            "token_type": token_type,
        }

        if additional_claims:
            claims.update(additional_claims)

        return jwt.encode(claims, self._secret_key, algorithm=self._algorithm)

    def _decode_claims(self, token: str) -> dict[str, Any]:
        try:
            decoded = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
                options={
                    "require": ["sub", "email", "roles", "permissions", "iat", "exp", "iss", "aud", "jti"],
                },
            )
            return dict(decoded)
        except ExpiredSignatureError as exc:
            raise TokenExpiredError("Token has expired") from exc
        except InvalidAudienceError as exc:
            raise TokenInvalidAudienceError("Token audience is invalid") from exc
        except InvalidIssuerError as exc:
            raise TokenInvalidIssuerError("Token issuer is invalid") from exc
        except InvalidTokenError as exc:
            raise TokenDecodeError("Token is invalid") from exc
