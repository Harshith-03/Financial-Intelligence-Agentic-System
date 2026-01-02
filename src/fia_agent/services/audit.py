"""Audit logging utilities."""

from __future__ import annotations

from collections import deque
from typing import Deque

from fia_agent.models import AuditRecord


class AuditService:
    def __init__(self, max_records: int = 500) -> None:
        self._records: Deque[AuditRecord] = deque(maxlen=max_records)

    def record(self, entry: AuditRecord) -> None:
        self._records.appendleft(entry)

    def recent(self, limit: int = 50) -> list[AuditRecord]:
        return list(list(self._records)[:limit])
