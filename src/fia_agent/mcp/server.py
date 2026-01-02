"""Placeholder MCP server wiring tools for external LLMs."""

from __future__ import annotations

from typing import Sequence

from fia_agent.mcp.tools import QueryTool, SchemaTool


class MCPServer:
    def __init__(self, schema_tool: SchemaTool, query_tool: QueryTool) -> None:
        self._schema_tool = schema_tool
        self._query_tool = query_tool

    async def register(self) -> Sequence[dict[str, str]]:
        return [
            {"name": self._schema_tool.name, "description": "List tables with columns"},
            {"name": self._query_tool.name, "description": "Execute NL query"},
        ]

    async def handle(self, tool_name: str, payload: dict) -> dict:
        if tool_name == self._schema_tool.name:
            return await self._schema_tool()
        if tool_name == self._query_tool.name:
            return await self._query_tool(**payload)
        raise ValueError(f"Unknown MCP tool: {tool_name}")
