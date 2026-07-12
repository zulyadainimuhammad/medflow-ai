from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.security.token_dependencies import get_token_service
from app.security.token_exceptions import (
    TokenExpiredError,
    TokenInvalidAudienceError,
    TokenInvalidIssuerError,
    TokenRevokedError,
    TokenTypeError,
)
from app.security.token_interfaces import TokenRevocationHook
from app.security.token_service import JWTTokenService

TEST_SECRET = "unit-test-secret-key-with-32-bytes!!"


class InMemoryRevocationHook(TokenRevocationHook):
    def __init__(self) -> None:
        self._revoked: dict[str, datetime] = {}

    def is_revoked(self, *, jti: str) -> bool:
        return jti in self._revoked

    def revoke(self, *, jti: str, expires_at: datetime, metadata: dict | None = None) -> None:
        self._revoked[jti] = expires_at


@pytest.fixture
def token_service() -> JWTTokenService:
    now = datetime.now(UTC)
    return JWTTokenService(
        secret_key=TEST_SECRET,
        issuer="medflow-ai",
        audience="medflow-api",
        access_token_ttl=timedelta(minutes=15),
        refresh_token_ttl=timedelta(days=7),
        now_provider=lambda: now,
    )


def _claims_kwargs() -> dict:
    return {
        "subject": "e9d80344-6d93-4331-8bc2-02929fb9ab5d",
        "email": "doctor@medflow.ai",
        "roles": ["Doctor"],
        "permissions": ["diagnostics:read", "diagnostics:create"],
    }


def test_generate_and_decode_access_token_includes_required_claims(
    token_service: JWTTokenService,
) -> None:
    token = token_service.generate_access_token(**_claims_kwargs())

    payload = token_service.decode_token(token=token, expected_token_type="access")

    assert payload.sub == "e9d80344-6d93-4331-8bc2-02929fb9ab5d"
    assert payload.email == "doctor@medflow.ai"
    assert payload.roles == ["Doctor"]
    assert payload.permissions == ["diagnostics:read", "diagnostics:create"]
    assert payload.iss == "medflow-ai"
    assert payload.aud == "medflow-api"
    assert payload.jti
    assert payload.iat > 0
    assert payload.exp > payload.iat


def test_generate_and_decode_refresh_token(token_service: JWTTokenService) -> None:
    token = token_service.generate_refresh_token(**_claims_kwargs())

    payload = token_service.decode_token(token=token, expected_token_type="refresh")

    assert payload.token_type == "refresh"


def test_verify_token_true_for_valid_token(token_service: JWTTokenService) -> None:
    token = token_service.generate_access_token(**_claims_kwargs())

    assert token_service.verify_token(token=token, expected_token_type="access") is True


def test_decode_token_raises_for_wrong_type(token_service: JWTTokenService) -> None:
    token = token_service.generate_access_token(**_claims_kwargs())

    with pytest.raises(TokenTypeError):
        token_service.decode_token(token=token, expected_token_type="refresh")


def test_decode_token_raises_for_invalid_audience(token_service: JWTTokenService) -> None:
    token = token_service.generate_access_token(**_claims_kwargs())
    invalid_audience_service = JWTTokenService(
        secret_key=TEST_SECRET,
        issuer="medflow-ai",
        audience="other-audience",
    )

    with pytest.raises(TokenInvalidAudienceError):
        invalid_audience_service.decode_token(token=token)


def test_decode_token_raises_for_invalid_issuer(token_service: JWTTokenService) -> None:
    token = token_service.generate_access_token(**_claims_kwargs())
    invalid_issuer_service = JWTTokenService(
        secret_key=TEST_SECRET,
        issuer="other-issuer",
        audience="medflow-api",
    )

    with pytest.raises(TokenInvalidIssuerError):
        invalid_issuer_service.decode_token(token=token)


def test_decode_token_raises_for_expired_token() -> None:
    fixed_now = datetime.now(UTC) - timedelta(minutes=5)
    issue_service = JWTTokenService(
        secret_key=TEST_SECRET,
        issuer="medflow-ai",
        audience="medflow-api",
        access_token_ttl=timedelta(minutes=1),
        now_provider=lambda: fixed_now,
    )
    token = issue_service.generate_access_token(**_claims_kwargs())

    with pytest.raises(TokenExpiredError):
        JWTTokenService(
            secret_key=TEST_SECRET,
            issuer="medflow-ai",
            audience="medflow-api",
        ).decode_token(token=token)


def test_token_rotation_revokes_old_refresh_and_issues_new_pair() -> None:
    hook = InMemoryRevocationHook()
    now = datetime.now(UTC)
    service = JWTTokenService(
        secret_key=TEST_SECRET,
        issuer="medflow-ai",
        audience="medflow-api",
        revocation_hook=hook,
        now_provider=lambda: now,
    )

    original_refresh = service.generate_refresh_token(**_claims_kwargs())
    original_payload = service.decode_token(token=original_refresh, expected_token_type="refresh")

    pair = service.rotate_tokens(refresh_token=original_refresh)

    assert pair.access_token
    assert pair.refresh_token
    assert pair.refresh_token != original_refresh
    assert hook.is_revoked(jti=original_payload.jti) is True


def test_decode_token_raises_when_revoked() -> None:
    hook = InMemoryRevocationHook()
    now = datetime.now(UTC)
    service = JWTTokenService(
        secret_key=TEST_SECRET,
        issuer="medflow-ai",
        audience="medflow-api",
        revocation_hook=hook,
        now_provider=lambda: now,
    )

    token = service.generate_access_token(**_claims_kwargs())
    payload = service.decode_token(token=token)

    hook.revoke(jti=payload.jti, expires_at=payload.expires_at)

    with pytest.raises(TokenRevokedError):
        service.decode_token(token=token)


def test_get_token_service_loads_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "env-secret-key-with-32-bytes-value")
    monkeypatch.setenv("JWT_ISSUER", "env-issuer")
    monkeypatch.setenv("JWT_AUDIENCE", "env-audience")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "14")

    service = get_token_service()

    token = service.generate_access_token(**_claims_kwargs())
    payload = service.decode_token(token=token, expected_token_type="access")

    assert payload.iss == "env-issuer"
    assert payload.aud == "env-audience"
