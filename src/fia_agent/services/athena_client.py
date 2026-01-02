"""Athena wrapper used for query execution and schema discovery."""

from __future__ import annotations

import asyncio
from fia_agent.config import Settings
from fia_agent.models import QueryExecutionResult, TableDefinition


class AthenaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.athena_enabled

    async def describe(self) -> list[TableDefinition]:
        if not self.enabled:
            return []
        await asyncio.sleep(0.05)
        return []

    async def execute(self, sql: str) -> QueryExecutionResult:
        if not self.enabled:
            raise RuntimeError("Athena is not configured")
        await asyncio.sleep(0.1)
        return QueryExecutionResult(rows=[{"message": "Not yet implemented"}], row_count=1, latency_ms=105, source="athena")
