"""Security utilities such as RBAC enforcement and encryption helpers."""

from __future__ import annotations

import hashlib
import hmac
from typing import Iterable

from fastapi import HTTPException, status

from fia_agent.config import Settings


class RBACService:
    def __init__(self, settings: Settings) -> None:
        self._allowed_roles = {role.lower() for role in settings.allowed_roles}

    def assert_role(self, role: str) -> None:
        if role.lower() not in self._allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted")

    def sign_payload(self, payload: str, secret: str) -> str:
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def redact_columns(self, rows: Iterable[dict[str, object]], restricted_columns: set[str]) -> list[dict[str, object]]:
        sanitized: list[dict[str, object]] = []
        for row in rows:
            sanitized.append({key: ("***" if key in restricted_columns else value) for key, value in row.items()})
        return sanitized
