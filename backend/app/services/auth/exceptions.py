from __future__ import annotations

from datetime import datetime
from uuid import UUID


class AuthenticationDomainError(Exception):
    """Base class for authentication service domain errors."""


class UserNotFoundError(AuthenticationDomainError):
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User not found for id={user_id}")


class UserAlreadyExistsError(AuthenticationDomainError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User already exists for email={email}")


class EmployeeIdAlreadyExistsError(AuthenticationDomainError):
    def __init__(self, employee_id: str) -> None:
        self.employee_id = employee_id
        super().__init__(f"User already exists for employee_id={employee_id}")


class InvalidCredentialsError(AuthenticationDomainError):
    pass


class AccountInactiveError(AuthenticationDomainError):
    pass


class AccountDeletedError(AuthenticationDomainError):
    pass


class AccountNotVerifiedError(AuthenticationDomainError):
    pass


class AccountLockedError(AuthenticationDomainError):
    def __init__(self, locked_until: datetime | None) -> None:
        self.locked_until = locked_until
        if locked_until is None:
            super().__init__("Account is locked")
        else:
            super().__init__(f"Account is locked until {locked_until.isoformat()}")


class RoleNotFoundError(AuthenticationDomainError):
    def __init__(self, role_name: str) -> None:
        self.role_name = role_name
        super().__init__(f"Role not found: {role_name}")


class PasswordChangeRejectedError(AuthenticationDomainError):
    pass
