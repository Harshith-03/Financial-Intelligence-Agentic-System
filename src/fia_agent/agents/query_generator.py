"""Agent responsible for Text2SQL generation."""

from __future__ import annotations

from fia_agent.models import TableDefinition
from fia_agent.services.memory import MemoryManager
from fia_agent.services.text2sql import Text2SQLTranslator


class QueryGenerationAgent:
    def __init__(self, translator: Text2SQLTranslator, memory: MemoryManager) -> None:
        self._translator = translator
        self._memory = memory

    async def run(
        self,
        question: str,
        schema: list[TableDefinition],
        session_id: str | None,
        user_id: str,
    ) -> tuple[str, str]:
        short_context = self._memory.recall_short_term(session_id or "")
        long_context = list(self._memory.recall_long_term(user_id))
        merged_context = [*short_context, *long_context]
        sql, rationale = await self._translator.generate_sql(question, schema, merged_context)
        if session_id:
            self._memory.capture_turn(session_id, "assistant", sql)
        return sql, rationale

    async def repair(
        self,
        question: str,
        schema: list[TableDefinition],
        previous_sql: str,
        error: str,
    ) -> tuple[str, str]:
        return await self._translator.repair_sql(question, schema, error, previous_sql)
