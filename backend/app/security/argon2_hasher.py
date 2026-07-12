from __future__ import annotations

from argon2 import PasswordHasher as Argon2Engine
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.security.interfaces import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Argon2id password hasher aligned with OWASP minimum recommendations."""

    def __init__(
        self,
        *,
        time_cost: int = 2,
        memory_cost_kib: int = 19456,
        parallelism: int = 1,
        hash_len: int = 32,
        salt_len: int = 16,
    ) -> None:
        self._engine = Argon2Engine(
            time_cost=time_cost,
            memory_cost=memory_cost_kib,
            parallelism=parallelism,
            hash_len=hash_len,
            salt_len=salt_len,
        )

    def hash(self, password: str) -> str:
        return self._engine.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        try:
            return self._engine.verify(hashed_password, password)
        except (VerifyMismatchError, InvalidHashError):
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        try:
            return self._engine.check_needs_rehash(hashed_password)
        except InvalidHashError:
            return True
