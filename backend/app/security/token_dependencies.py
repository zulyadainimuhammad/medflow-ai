from __future__ import annotations

import os
from datetime import timedelta

from app.security.token_interfaces import TokenRevocationHook, TokenService
from app.security.token_service import JWTTokenService


def get_token_service(
    *,
    secret_key: str | None = None,
    issuer: str | None = None,
    audience: str | None = None,
    algorithm: str | None = None,
    access_token_ttl: timedelta | None = None,
    refresh_token_ttl: timedelta | None = None,
    revocation_hook: TokenRevocationHook | None = None,
) -> TokenService:
    resolved_secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    resolved_issuer = issuer or os.getenv("JWT_ISSUER", "medflow-ai")
    resolved_audience = audience or os.getenv("JWT_AUDIENCE", "medflow-api")
    resolved_algorithm = algorithm or os.getenv("JWT_ALGORITHM", "HS256")

    resolved_access_token_ttl = access_token_ttl or timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15"))
    )
    resolved_refresh_token_ttl = refresh_token_ttl or timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
    )

    return JWTTokenService(
        secret_key=resolved_secret_key,
        issuer=resolved_issuer,
        audience=resolved_audience,
        algorithm=resolved_algorithm,
        access_token_ttl=resolved_access_token_ttl,
        refresh_token_ttl=resolved_refresh_token_ttl,
        revocation_hook=revocation_hook,
    )
