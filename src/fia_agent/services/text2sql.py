"""Lightweight Text2SQL translator abstractions."""

from __future__ import annotations

import re
from typing import Iterable

from langchain_core.language_models import BaseLanguageModel

from fia_agent.models import TableDefinition


class Text2SQLTranslator:
    """Translates natural language questions into SQL with light heuristics."""

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        self._llm = llm

    async def generate_sql(
        self,
        question: str,
        schema: list[TableDefinition],
        history: Iterable[str] | None = None,
    ) -> tuple[str, str]:
        """Return SQL plus rationale string."""

        reasoning = [f"Question: {question}"]
        table = self._pick_table(question, schema)
        reasoning.append(f"Target table: {table}")
        sql = self._fallback_sql(question, table)
        if history:
            reasoning.append("Context:" + " | ".join(history))
        return sql, "\n".join(reasoning)

    async def repair_sql(
        self,
        question: str,
        schema: list[TableDefinition],
        error: str,
        previous_sql: str,
    ) -> tuple[str, str]:
        """Attempt to repair SQL based on engine feedback."""

        reasoning = ["Repair triggered", f"Engine error: {error}"]
        if "syntax" in error.lower() and "SELECT" not in previous_sql.upper():
            repaired = previous_sql.strip()
            if not repaired.endswith(";"):
                repaired += ";"
            reasoning.append("Ensured statement termination.")
            return repaired, "\n".join(reasoning)
        table = self._pick_table(question, schema)
        heuristics = self._fallback_sql(question, table)
        reasoning.append("Re-generated via fallback heuristics.")
        return heuristics, "\n".join(reasoning)

    def _fallback_sql(self, question: str, table: str) -> str:
        lowered = question.lower()
        select_cols = "segment, SUM(revenue_usd) AS revenue" if "segment" in lowered else "*"
        metric = "ebitda_usd" if "ebitda" in lowered else "revenue_usd"
        filters = []
        quarter_match = re.search(r"(20\d{2})\s*(q[1-4])", lowered)
        if quarter_match:
            filters.append(f"fiscal_quarter = '{quarter_match.group(1)}-{quarter_match.group(2).upper()}'")
        if "guidance" in lowered:
            table = "guidance"
        where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""
        group_clause = " GROUP BY segment" if "segment" in lowered else ""
        sql = f"SELECT {select_cols}, AVG({metric}) AS metric FROM {table}{where_clause}{group_clause} LIMIT 200"
        return sql

    def _pick_table(self, question: str, schema: list[TableDefinition]) -> str:
        default = schema[0].name if schema else "financials_quarterly"
        for table in schema:
            if table.name in question.lower():
                return table.name
            if table.description and any(keyword in question.lower() for keyword in table.description.lower().split()):
                return table.name
        return default
