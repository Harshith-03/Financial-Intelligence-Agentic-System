"""Dynamic schema discovery utilities."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

import yaml

from fia_agent.models import ColumnDefinition, TableDefinition


class SchemaDiscoveryService:
    """Discovers table metadata from Snowflake, Athena, or fallback files."""

    def __init__(
        self,
        sample_schema_path: Path,
        snowflake_client: "SnowflakeClient | None" = None,
        athena_client: "AthenaClient | None" = None,
    ) -> None:
        self._sample_schema_path = sample_schema_path
        self._snowflake = snowflake_client
        self._athena = athena_client
        self._cache: list[TableDefinition] = []
        self._lock = asyncio.Lock()

    async def get_schema(self, preferred: Literal["snowflake", "athena", "auto"] = "auto") -> list[TableDefinition]:
        async with self._lock:
            if self._cache:
                return self._cache
            if preferred in ("snowflake", "auto") and self._snowflake:
                schema = await self._snowflake.describe()
                if schema:
                    self._cache = schema
                    return schema
            if preferred in ("athena", "auto") and self._athena:
                schema = await self._athena.describe()
                if schema:
                    self._cache = schema
                    return schema
            self._cache = self._load_from_file()
            return self._cache

    def _load_from_file(self) -> list[TableDefinition]:
        data = yaml.safe_load(self._sample_schema_path.read_text(encoding="utf-8"))
        tables: list[TableDefinition] = []
        for table in data.get("tables", []):
            columns = [ColumnDefinition(**column) for column in table.get("columns", [])]
            tables.append(TableDefinition(name=table["name"], description=table.get("description"), columns=columns))
        return tables

    async def refresh(self) -> list[TableDefinition]:
        async with self._lock:
            self._cache = []
        return await self.get_schema()
