from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.db.models.auth import User
from app.repositories.auth.role_repository import RoleRepository
from app.repositories.auth.user_repository import UserRepository
from app.services.auth.exceptions import (
    AccountDeletedError,
    AccountInactiveError,
    AccountLockedError,
    AccountNotVerifiedError,
    EmployeeIdAlreadyExistsError,
    InvalidCredentialsError,
    PasswordChangeRejectedError,
    RoleNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.services.auth.models import AuthAuditEvent
from app.services.auth.ports import AuthAuditEventPublisher, PasswordHasher


class AuthenticationService:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        password_hasher: PasswordHasher,
        audit_publisher: AuthAuditEventPublisher,
        default_role_name: str = "Doctor",
        max_failed_login_attempts: int = 5,
        account_lock_minutes: int = 30,
        require_verified_for_login: bool = False,
    ) -> None:
        self._user_repository = user_repository
        self._role_repository = role_repository
        self._password_hasher = password_hasher
        self._audit_publisher = audit_publisher
        self._default_role_name = default_role_name
        self._max_failed_login_attempts = max_failed_login_attempts
        self._account_lock_minutes = account_lock_minutes
        self._require_verified_for_login = require_verified_for_login

    async def register_user(self, *, user_data: dict[str, Any]) -> User:
        email = str(user_data["email"]).lower()
        existing_user = await self._user_repository.get_by_email(email)
        if existing_user is not None:
            await self.generate_authentication_audit_event(
                event_type="auth.registration.failed",
                outcome="duplicate_email",
                email=email,
            )
            raise UserAlreadyExistsError(email=email)

        employee_id = user_data.get("employee_id")
        if isinstance(employee_id, str) and employee_id:
            existing_employee = await self._user_repository.get_by_employee_id(employee_id)
            if existing_employee is not None:
                await self.generate_authentication_audit_event(
                    event_type="auth.registration.failed",
                    outcome="duplicate_employee_id",
                    email=email,
                    metadata={"employee_id": employee_id},
                )
                raise EmployeeIdAlreadyExistsError(employee_id=employee_id)

        raw_password = str(user_data.pop("password"))
        user_data["email"] = email
        user_data["password_hash"] = self._password_hasher.hash_password(raw_password)

        user = await self._user_repository.create_user(**user_data)
        await self.assign_default_role(user)

        await self.generate_authentication_audit_event(
            event_type="auth.registration.success",
            outcome="success",
            user=user,
        )
        return user

    async def authenticate_user(self, *, email: str, password: str) -> User:
        normalized_email = email.lower()
        user = await self._user_repository.get_by_email(normalized_email)
        if user is None:
            await self.generate_authentication_audit_event(
                event_type="auth.login.failed",
                outcome="user_not_found",
                email=normalized_email,
            )
            raise InvalidCredentialsError("Invalid email or password")

        self.validate_account_status(user)

        password_valid = self.verify_password(password=password, password_hash=user.password_hash)
        if not password_valid:
            await self._user_repository.increment_failed_login(user)
            await self._user_repository.update_user(user, last_failed_login=datetime.now(tz=UTC))

            if user.failed_login_attempts >= self._max_failed_login_attempts:
                await self.lock_account(user)
                await self.generate_authentication_audit_event(
                    event_type="auth.login.failed",
                    outcome="account_locked",
                    user=user,
                )
                raise AccountLockedError(locked_until=user.account_locked_until)

            await self.generate_authentication_audit_event(
                event_type="auth.login.failed",
                outcome="invalid_credentials",
                user=user,
            )
            raise InvalidCredentialsError("Invalid email or password")

        await self._user_repository.reset_failed_login_attempts(user)
        await self._user_repository.unlock_account(user)
        await self.update_last_login(user)

        await self.generate_authentication_audit_event(
            event_type="auth.login.success",
            outcome="success",
            user=user,
        )
        return user

    def verify_password(self, *, password: str, password_hash: str) -> bool:
        return self._password_hasher.verify_password(password, password_hash)

    async def change_password(
        self,
        *,
        user_id: UUID,
        current_password: str,
        new_password: str,
        actor_user_id: UUID | None = None,
    ) -> User:
        user = await self._get_user_or_raise(user_id)
        self.validate_account_status(user)

        if not self.verify_password(password=current_password, password_hash=user.password_hash):
            await self.generate_authentication_audit_event(
                event_type="auth.password_change.failed",
                outcome="invalid_current_password",
                user=user,
            )
            raise PasswordChangeRejectedError("Current password is invalid")

        password_hash = self._password_hasher.hash_password(new_password)
        updated_user = await self._user_repository.update_user(
            user,
            password_hash=password_hash,
            password_changed_at=datetime.now(tz=UTC),
            must_change_password=False,
            refresh_token_version=user.refresh_token_version + 1,
            updated_by=actor_user_id,
        )

        await self.generate_authentication_audit_event(
            event_type="auth.password_change.success",
            outcome="success",
            user=updated_user,
        )
        return updated_user

    async def reset_password_request(self, *, email: str) -> User | None:
        normalized_email = email.lower()
        user = await self._user_repository.get_by_email(normalized_email)
        if user is None:
            await self.generate_authentication_audit_event(
                event_type="auth.password_reset.request",
                outcome="accepted",
                email=normalized_email,
            )
            return None

        await self.generate_authentication_audit_event(
            event_type="auth.password_reset.request",
            outcome="accepted",
            user=user,
        )
        return user

    async def reset_password(
        self,
        *,
        user_id: UUID,
        new_password: str,
        actor_user_id: UUID | None = None,
    ) -> User:
        user = await self._get_user_or_raise(user_id)

        password_hash = self._password_hasher.hash_password(new_password)
        updated_user = await self._user_repository.update_user(
            user,
            password_hash=password_hash,
            password_changed_at=datetime.now(tz=UTC),
            must_change_password=False,
            refresh_token_version=user.refresh_token_version + 1,
            updated_by=actor_user_id,
        )
        await self._user_repository.reset_failed_login_attempts(updated_user)
        await self._user_repository.unlock_account(updated_user)

        await self.generate_authentication_audit_event(
            event_type="auth.password_reset.success",
            outcome="success",
            user=updated_user,
        )
        return updated_user

    async def assign_default_role(self, user: User) -> User:
        role = await self._role_repository.get_role_by_name(self._default_role_name)
        if role is None:
            raise RoleNotFoundError(role_name=self._default_role_name)

        await self._role_repository.assign_role(user_id=user.id, role_id=role.id)
        return user

    async def verify_account(self, *, user_id: UUID, actor_user_id: UUID | None = None) -> User:
        user = await self._get_user_or_raise(user_id)
        updated_user = await self._user_repository.verify_user(user)

        if actor_user_id is not None:
            updated_user = await self._user_repository.update_user(
                updated_user, updated_by=actor_user_id
            )

        await self.generate_authentication_audit_event(
            event_type="auth.account_verification.success",
            outcome="success",
            user=updated_user,
        )
        return updated_user

    async def lock_account(self, user: User) -> User:
        locked_until = datetime.now(tz=UTC) + timedelta(minutes=self._account_lock_minutes)
        updated_user = await self._user_repository.lock_account(user, locked_until=locked_until)
        await self.generate_authentication_audit_event(
            event_type="auth.account.locked",
            outcome="success",
            user=updated_user,
            metadata={"locked_until": locked_until.isoformat()},
        )
        return updated_user

    async def unlock_account(self, *, user_id: UUID, actor_user_id: UUID | None = None) -> User:
        user = await self._get_user_or_raise(user_id)
        updated_user = await self._user_repository.unlock_account(user)
        updated_user = await self._user_repository.reset_failed_login_attempts(updated_user)

        if actor_user_id is not None:
            updated_user = await self._user_repository.update_user(
                updated_user, updated_by=actor_user_id
            )

        await self.generate_authentication_audit_event(
            event_type="auth.account.unlocked",
            outcome="success",
            user=updated_user,
        )
        return updated_user

    async def update_last_login(self, user: User) -> User:
        return await self._user_repository.update_last_login(user)

    def validate_account_status(self, user: User) -> None:
        if user.deleted_at is not None:
            raise AccountDeletedError("Account has been deleted")

        if not user.is_active:
            raise AccountInactiveError("Account is inactive")

        if self._require_verified_for_login and not user.is_verified:
            raise AccountNotVerifiedError("Account is not verified")

        now = datetime.now(tz=UTC)
        if user.account_locked_until is not None and user.account_locked_until > now:
            raise AccountLockedError(locked_until=user.account_locked_until)

    async def generate_authentication_audit_event(
        self,
        *,
        event_type: str,
        outcome: str,
        user: User | None = None,
        email: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuthAuditEvent:
        event = AuthAuditEvent(
            event_type=event_type,
            occurred_at=datetime.now(tz=UTC),
            outcome=outcome,
            user_id=user.id if user is not None else None,
            email=user.email if user is not None else email,
            metadata=metadata,
        )

        await self._audit_publisher.publish(
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            email=event.email,
            outcome=event.outcome,
            metadata=event.metadata,
        )
        return event

    async def _get_user_or_raise(self, user_id: UUID) -> User:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id=user_id)
        return user
