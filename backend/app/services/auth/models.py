from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthAuditEvent:
    event_type: str
    occurred_at: datetime
    outcome: str
    user_id: UUID | None = None
    email: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    sub: str
    email: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    is_active: bool
    is_verified: bool
    claims: dict[str, Any]
