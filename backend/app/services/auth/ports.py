from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


class PasswordHasher(Protocol):
    def hash_password(self, raw_password: str) -> str:
        ...

    def verify_password(self, raw_password: str, password_hash: str) -> bool:
        ...


class AuthAuditEventPublisher(Protocol):
    async def publish(
        self,
        *,
        event_type: str,
        occurred_at: datetime,
        user_id: UUID | None,
        email: str | None,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...
