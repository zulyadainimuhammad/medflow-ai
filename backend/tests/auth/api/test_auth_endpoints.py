from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.auth import routes as auth_routes
from app.api.dependencies.auth import get_current_active_user
from app.db.models.auth import Permission, Role
from app.main import app
from app.security.token_models import TokenPair, TokenPayload
from app.services.auth.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.services.auth.models import AuthenticatedUser


class StubAuthService:
    def __init__(self):
        self.raise_on_register: Exception | None = None
        self.raise_on_login: Exception | None = None
        self.users = {}

    async def register_user(self, *, user_data):
        if self.raise_on_register:
            raise self.raise_on_register

        user = auth_routes.User(
            id=uuid4(),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"].lower(),
            password_hash="hashed",
            is_active=True,
            is_verified=False,
        )
        self.users[user.id] = user
        return user

    async def authenticate_user(self, *, email, password):
        if self.raise_on_login:
            raise self.raise_on_login
        return auth_routes.User(
            id=uuid4(),
            first_name="Amina",
            last_name="Yusuf",
            email=email.lower(),
            password_hash="hashed",
            is_active=True,
            is_verified=True,
        )

    async def change_password(self, *, user_id, current_password, new_password, actor_user_id=None):
        return None

    async def reset_password_request(self, *, email):
        return None

    async def reset_password(self, *, user_id, new_password, actor_user_id=None):
        return None


class StubTokenService:
    def __init__(self):
        self.revoked: list[str] = []

    def generate_access_token(self, **kwargs):
        return "access-token"

    def generate_refresh_token(self, **kwargs):
        return "refresh-token"

    def verify_token(self, *, token, expected_token_type=None):
        return True

    def decode_token(self, *, token, expected_token_type=None):
        return TokenPayload(
            sub=str(uuid4()),
            email="amina@medflow.ai",
            roles=["Doctor"],
            permissions=["diagnostics:read"],
            iat=1,
            exp=9999999999,
            iss="medflow-ai",
            aud="medflow-api",
            jti="jti-1",
            token_type="refresh",
        )

    def rotate_tokens(self, *, refresh_token):
        return TokenPair(access_token="new-access", refresh_token="new-refresh")

    def revoke_token(self, *, token, reason="manual_revocation"):
        self.revoked.append(token)


class StubRoleRepository:
    async def get_user_roles(self, user_id):
        return [Role(id=2, name="Doctor", description="Clinical")]


class StubPermissionRepository:
    async def get_permissions_for_role(self, role_id):
        return [Permission(id=1, role_id=role_id, name="diagnostics:read", description="Read access")]


@pytest.fixture
def client():
    auth_service = StubAuthService()
    token_service = StubTokenService()
    role_repo = StubRoleRepository()
    permission_repo = StubPermissionRepository()

    app.dependency_overrides[auth_routes.get_authentication_service_dependency] = lambda: auth_service
    app.dependency_overrides[auth_routes.get_token_service_dependency] = lambda: token_service
    app.dependency_overrides[auth_routes.get_role_repository_dependency] = lambda: role_repo
    app.dependency_overrides[auth_routes.get_permission_repository_dependency] = lambda: permission_repo
    app.dependency_overrides[get_current_active_user] = lambda: AuthenticatedUser(
        sub=str(uuid4()),
        email="doctor@medflow.ai",
        roles=("Doctor",),
        permissions=("diagnostics:read",),
        is_active=True,
        is_verified=True,
        claims={},
    )

    with TestClient(app) as test_client:
        test_client.auth_service = auth_service
        test_client.token_service = token_service
        yield test_client

    app.dependency_overrides.clear()


def test_register_endpoint_returns_user_summary(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Amina",
            "last_name": "Yusuf",
            "email": "AMINA.YUSUF@medflow.ai",
            "phone_number": "+2348012345678",
            "password": "StrongPassw0rd!",
            "is_active": True,
            "is_verified": False,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "amina.yusuf@medflow.ai"
    assert body["first_name"] == "Amina"


def test_register_endpoint_maps_domain_conflict(client: TestClient) -> None:
    client.auth_service.raise_on_register = UserAlreadyExistsError(email="amina@medflow.ai")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Amina",
            "last_name": "Yusuf",
            "email": "amina@medflow.ai",
            "phone_number": "+2348012345678",
            "password": "StrongPassw0rd!",
            "is_active": True,
            "is_verified": False,
        },
    )

    assert response.status_code == 409


def test_login_endpoint_returns_tokens_and_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@medflow.ai", "password": "StrongPassw0rd!"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token"]["access_token"] == "access-token"
    assert payload["token"]["refresh_token"] == "refresh-token"
    assert payload["user"]["email"] == "doctor@medflow.ai"


def test_login_endpoint_maps_invalid_credentials(client: TestClient) -> None:
    client.auth_service.raise_on_login = InvalidCredentialsError("Invalid email or password")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@medflow.ai", "password": "WrongPassw0rd!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_and_logout_endpoints(client: TestClient) -> None:
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "old-refresh-token"},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"] == "new-access"

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "old-refresh-token"},
        headers={"Authorization": "Bearer access-token"},
    )
    assert logout_response.status_code == 200
    assert set(client.token_service.revoked) == {"old-refresh-token", "access-token"}


def test_change_forgot_reset_me_and_roles_endpoints(client: TestClient) -> None:
    change_response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "CurrentPassw0rd!", "new_password": "NewPassw0rd!"},
    )
    assert change_response.status_code == 200

    forgot_response = client.post("/api/v1/auth/forgot-password", json={"email": "doctor@medflow.ai"})
    assert forgot_response.status_code == 200

    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": "valid-reset-token", "new_password": "ResetPassw0rd!"},
    )
    assert reset_response.status_code == 200

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "doctor@medflow.ai"

    roles_response = client.get("/api/v1/auth/roles")
    assert roles_response.status_code == 200
    roles_payload = roles_response.json()
    assert roles_payload[0]["name"] == "Doctor"
    assert roles_payload[0]["permissions"][0]["name"] == "diagnostics:read"
