from app.repositories.auth.role_repository import RoleRepository
from app.repositories.auth.user_repository import UserRepository
from app.services.auth.authentication_service import AuthenticationService
from app.services.auth.ports import AuthAuditEventPublisher, PasswordHasher


def get_authentication_service(
    *,
    user_repository: UserRepository,
    role_repository: RoleRepository,
    password_hasher: PasswordHasher,
    audit_publisher: AuthAuditEventPublisher,
    default_role_name: str = "Doctor",
    max_failed_login_attempts: int = 5,
    account_lock_minutes: int = 30,
    require_verified_for_login: bool = False,
) -> AuthenticationService:
    return AuthenticationService(
        user_repository=user_repository,
        role_repository=role_repository,
        password_hasher=password_hasher,
        audit_publisher=audit_publisher,
        default_role_name=default_role_name,
        max_failed_login_attempts=max_failed_login_attempts,
        account_lock_minutes=account_lock_minutes,
        require_verified_for_login=require_verified_for_login,
    )
