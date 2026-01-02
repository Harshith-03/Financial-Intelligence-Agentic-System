"""Model Context Protocol tool wrappers."""

from __future__ import annotations

from fia_agent.models import QueryRequest
from fia_agent.services.schema_discovery import SchemaDiscoveryService
from fia_agent.agents.conductor import ConductorGraph


class SchemaTool:
    name = "list_financial_tables"

    def __init__(self, schema_service: SchemaDiscoveryService) -> None:
        self._schema_service = schema_service

    async def __call__(self, *_args, **_kwargs) -> dict:
        schema = await self._schema_service.get_schema()
        return {"tables": [table.model_dump() for table in schema]}


class QueryTool:
    name = "run_financial_query"

    def __init__(self, orchestrator: ConductorGraph) -> None:
        self._orchestrator = orchestrator

    async def __call__(self, *, question: str, user_id: str, role: str) -> dict:
        request = QueryRequest(question=question, user_id=user_id, role=role)
        response = await self._orchestrator.run(request)
        return response.model_dump()
