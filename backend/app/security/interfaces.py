from __future__ import annotations

from typing import Protocol


class PasswordHasher(Protocol):
    """Security utility contract for password hashing and verification."""

    def hash(self, password: str) -> str:
        """Return a secure hash for a raw password."""

    def verify(self, password: str, hashed_password: str) -> bool:
        """Return True when password matches hashed_password."""

    def needs_rehash(self, hashed_password: str) -> bool:
        """Return True when hash parameters are outdated and should be upgraded."""
