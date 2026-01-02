"""Thin async wrapper around the Snowflake connector."""

from __future__ import annotations

import asyncio
from fia_agent.config import Settings
from fia_agent.models import QueryExecutionResult, TableDefinition


class SnowflakeClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.snowflake_enabled

    async def describe(self) -> list[TableDefinition]:
        if not self.enabled:
            return []
        # Placeholder: integrate SHOW TABLES queries with snowflake-connector.
        await asyncio.sleep(0.05)
        return []

    async def execute(self, sql: str) -> QueryExecutionResult:
        if not self.enabled:
            raise RuntimeError("Snowflake is not configured")
        # Real implementation should use snowflake.connector.connect and fetch result sets.
        await asyncio.sleep(0.1)
        return QueryExecutionResult(rows=[{"message": "Not yet implemented"}], row_count=1, latency_ms=100, source="snowflake")

    async def close(self) -> None:
        await asyncio.sleep(0)
