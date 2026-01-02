"""Route SQL execution to configured data sources with retries and fallbacks."""

from __future__ import annotations

import random
import time
from typing import Literal

from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from fia_agent.models import QueryExecutionResult
from fia_agent.services.athena_client import AthenaClient
from fia_agent.services.snowflake_client import SnowflakeClient


class QueryExecutor:
    def __init__(self, snowflake: SnowflakeClient | None, athena: AthenaClient | None) -> None:
        self._snowflake = snowflake
        self._athena = athena

    async def execute(self, sql: str, preferred: Literal["snowflake", "athena", "auto"], role: str) -> QueryExecutionResult:
        start = time.perf_counter()
        for attempt in AsyncRetrying(wait=wait_fixed(0.2), stop=stop_after_attempt(2)):
            with attempt:
                result = await self._execute_once(sql, preferred)
                result.latency_ms = int((time.perf_counter() - start) * 1000)
                return result
        return QueryExecutionResult(rows=[], row_count=0, latency_ms=0)

    async def _execute_once(self, sql: str, preferred: Literal["snowflake", "athena", "auto"]) -> QueryExecutionResult:
        if preferred in ("snowflake", "auto") and self._snowflake and self._snowflake.enabled:
            return await self._snowflake.execute(sql)
        if preferred in ("athena", "auto") and self._athena and self._athena.enabled:
            return await self._athena.execute(sql)
        return self._mock(sql)

    def _mock(self, sql: str) -> QueryExecutionResult:
        rows = [
            {"fiscal_quarter": "2024-Q1", "revenue_usd": 1250 + random.randint(-50, 50), "segment": "Cloud"},
            {"fiscal_quarter": "2024-Q1", "revenue_usd": 890 + random.randint(-40, 40), "segment": "Payments"},
        ]
        return QueryExecutionResult(rows=rows, row_count=len(rows), latency_ms=random.randint(80, 120), source="mock")
