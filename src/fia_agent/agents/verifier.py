"""Agent responsible for executing and validating SQL."""

from __future__ import annotations

from fia_agent.models import QueryExecutionResult
from fia_agent.services.query_executor import QueryExecutor
from fia_agent.services.security import RBACService


class QueryVerificationAgent:
    def __init__(self, executor: QueryExecutor, security: RBACService) -> None:
        self._executor = executor
        self._security = security

    async def run(self, sql: str, preferred_source: str, role: str) -> QueryExecutionResult:
        self._security.assert_role(role)
        result = await self._executor.execute(sql, preferred_source, role)
        restricted = {"salary", "ssn"}
        result.rows = self._security.redact_columns(result.rows, restricted)
        return result
