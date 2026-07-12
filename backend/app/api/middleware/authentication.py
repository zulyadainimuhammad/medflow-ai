from __future__ import annotations

from collections.abc import Iterable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.security import TokenService
from app.security.token_exceptions import TokenServiceError


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        token_service: TokenService,
        skip_paths: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._token_service = token_service
        self._skip_paths = tuple(skip_paths or ())

    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.jwt_claims = None

        if self._is_skipped_path(request.url.path):
            return await call_next(request)

        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            return await call_next(request)

        scheme, token = self._parse_authorization_header(authorization_header)
        if scheme.lower() != "bearer" or not token:
            return await call_next(request)

        try:
            payload = self._token_service.decode_token(token=token)
            request.state.jwt_claims = {
                "sub": payload.sub,
                "email": payload.email,
                "roles": list(payload.roles),
                "permissions": list(payload.permissions),
                "iat": payload.iat,
                "exp": payload.exp,
                "iss": payload.iss,
                "aud": payload.aud,
                "jti": payload.jti,
                "token_type": payload.token_type,
            }
        except TokenServiceError:
            # Leave request unauthenticated; route dependencies will enforce access.
            request.state.jwt_claims = None

        return await call_next(request)

    def _is_skipped_path(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self._skip_paths)

    @staticmethod
    def _parse_authorization_header(header_value: str) -> tuple[str, str]:
        parts = header_value.split(" ", 1)
        if len(parts) != 2:
            return "", ""
        return parts[0], parts[1].strip()
