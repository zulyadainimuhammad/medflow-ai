from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

COMMON_PASSWORD_BLACKLIST: frozenset[str] = frozenset(
    {
        "123456",
        "123456789",
        "12345678",
        "qwerty",
        "password",
        "password123",
        "welcome",
        "letmein",
        "admin",
        "medflow",
        "medflowai",
    }
)


@dataclass(frozen=True, slots=True)
class PasswordPolicyConfig:
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numeric: bool = True
    require_special: bool = True


class PasswordSecurityError(ValueError):
    """Base class for password security domain exceptions."""


class InvalidPasswordError(PasswordSecurityError):
    """Raised when a password fails policy validation."""


class PasswordPolicyViolationError(InvalidPasswordError):
    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__("Password does not meet policy requirements")


class PasswordPolicy:
    def __init__(
        self,
        *,
        config: PasswordPolicyConfig | None = None,
        blacklist: frozenset[str] | None = None,
    ) -> None:
        self._config = config or PasswordPolicyConfig()
        self._blacklist = blacklist or COMMON_PASSWORD_BLACKLIST

    def validate(
        self,
        password: str,
        *,
        password_reuse_checker: Callable[[str], bool] | None = None,
    ) -> None:
        """
        Validate password policy.

        password_reuse_checker is a hook for future persistence-aware reuse checks.
        It should return True when the password was previously used.
        """
        violations: list[str] = []

        if len(password) < self._config.min_length:
            violations.append(f"Password must be at least {self._config.min_length} characters long")

        if self._config.require_uppercase and not re.search(r"[A-Z]", password):
            violations.append("Password must contain at least one uppercase letter")

        if self._config.require_lowercase and not re.search(r"[a-z]", password):
            violations.append("Password must contain at least one lowercase letter")

        if self._config.require_numeric and not re.search(r"[0-9]", password):
            violations.append("Password must contain at least one numeric character")

        if self._config.require_special and not re.search(r"[^A-Za-z0-9]", password):
            violations.append("Password must contain at least one special character")

        if password.lower() in self._blacklist:
            violations.append("Password is too common and cannot be used")

        if password_reuse_checker is not None and password_reuse_checker(password):
            violations.append("Password reuse is not allowed")

        if violations:
            raise PasswordPolicyViolationError(violations)
