"""Pydantic models shared across the service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ColumnDefinition(BaseModel):
    name: str
    type: str
    description: str | None = None


class TableDefinition(BaseModel):
    name: str
    description: str | None = None
    columns: list[ColumnDefinition] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str
    user_id: str
    role: str = Field(..., description="Role required for RBAC checks")
    session_id: str | None = Field(None, description="Conversation session identifier")
    output_format: Literal["table", "chart", "narrative"] = "table"
    preferred_source: Literal["snowflake", "athena", "auto"] = "auto"


class QueryExecutionResult(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    latency_ms: int = 0
    source: Literal["snowflake", "athena", "mock"] = "mock"


class VisualizationSpec(BaseModel):
    kind: Literal["table", "bar", "line", "text"] = "table"
    spec: dict[str, Any] = Field(default_factory=dict)
    insight_summary: str | None = None


class QueryResponse(BaseModel):
    sql_query: str
    execution: QueryExecutionResult
    visualization: VisualizationSpec
    self_corrections: list[str] = Field(default_factory=list)
    schema_used: list[TableDefinition] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditRecord(BaseModel):
    user_id: str
    role: str
    question: str
    sql_query: str
    status: Literal["success", "failed"]
    latency_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None
