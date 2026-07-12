from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.security.token_exceptions import TokenDecodeError, TokenExpiredError, TokenTypeError
from app.security.token_service import JWTTokenService

TEST_SECRET = "medflow-auth-jwt-test-secret-32bytes"


def _service(now: datetime | None = None) -> JWTTokenService:
    return JWTTokenService(
        secret_key=TEST_SECRET,
        issuer="medflow-ai",
        audience="medflow-api",
        access_token_ttl=timedelta(minutes=15),
        refresh_token_ttl=timedelta(days=7),
        now_provider=(lambda: now) if now is not None else None,
    )


def test_jwt_decode_returns_expected_claims_for_access_token() -> None:
    now = datetime.now(UTC)
    service = _service(now)
    token = service.generate_access_token(
        subject="user-123",
        email="doctor@medflow.ai",
        roles=["Doctor"],
        permissions=["diagnostics:read"],
    )

    payload = service.decode_token(token=token, expected_token_type="access")

    assert payload.sub == "user-123"
    assert payload.email == "doctor@medflow.ai"
    assert payload.token_type == "access"


def test_jwt_decode_rejects_wrong_token_type() -> None:
    service = _service(datetime.now(UTC))
    token = service.generate_refresh_token(
        subject="user-123",
        email="doctor@medflow.ai",
        roles=["Doctor"],
        permissions=["diagnostics:read"],
    )

    with pytest.raises(TokenTypeError):
        service.decode_token(token=token, expected_token_type="access")


def test_jwt_decode_rejects_expired_token() -> None:
    issued_at = datetime.now(UTC) - timedelta(minutes=20)
    issue_service = _service(issued_at)
    token = issue_service.generate_access_token(
        subject="user-123",
        email="doctor@medflow.ai",
        roles=["Doctor"],
        permissions=["diagnostics:read"],
    )

    with pytest.raises(TokenExpiredError):
        _service().decode_token(token=token)


def test_jwt_decode_rejects_malformed_token() -> None:
    with pytest.raises(TokenDecodeError):
        _service().decode_token(token="not-a-jwt")
