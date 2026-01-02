"""LangGraph conductor wiring specialized agents together."""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from fia_agent.agents.query_generator import QueryGenerationAgent
from fia_agent.agents.verifier import QueryVerificationAgent
from fia_agent.agents.visualizer import VisualizationAgent
from fia_agent.models import (
    AuditRecord,
    QueryExecutionResult,
    QueryRequest,
    QueryResponse,
    TableDefinition,
    VisualizationSpec,
)
from fia_agent.services.audit import AuditService
from fia_agent.services.memory import MemoryManager
from fia_agent.services.schema_discovery import SchemaDiscoveryService


class AgentState(TypedDict, total=False):
    request: QueryRequest
    schema: list[TableDefinition]
    sql_query: str | None
    execution: QueryExecutionResult | None
    visual: object | None
    self_corrections: list[str]
    rationales: list[str]
    last_error: str | None
    attempts: int


class ConductorGraph:
    def __init__(
        self,
        schema_service: SchemaDiscoveryService,
        generator: QueryGenerationAgent,
        verifier: QueryVerificationAgent,
        visualizer: VisualizationAgent,
        memory: MemoryManager,
        audit: AuditService,
    ) -> None:
        self._schema_service = schema_service
        self._generator = generator
        self._verifier = verifier
        self._visualizer = visualizer
        self._memory = memory
        self._audit = audit
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("generate_sql", self._node_generate)
        graph.add_node("execute_sql", self._node_execute)
        graph.add_node("repair_sql", self._node_repair)
        graph.add_node("visualize", self._node_visualize)
        graph.add_node("finalize", self._node_finalize)

        graph.set_entry_point("generate_sql")
        graph.add_edge("generate_sql", "execute_sql")
        graph.add_conditional_edges(
            "execute_sql",
            self._needs_repair,
            {
                "retry": "repair_sql",
                "visualize": "visualize",
            },
        )
        graph.add_edge("repair_sql", "execute_sql")
        graph.add_edge("visualize", "finalize")
        graph.add_edge("finalize", END)
        return graph.compile()

    async def run(self, request: QueryRequest) -> QueryResponse:
        schema = await self._schema_service.get_schema(request.preferred_source)
        state: AgentState = {
            "request": request,
            "schema": schema,
            "self_corrections": [],
            "rationales": [],
            "attempts": 0,
        }
        try:
            final_state: AgentState = await self._graph.ainvoke(state)
        except Exception as exc:  # pragma: no cover - defensive logging
            failure_response = QueryResponse(
                sql_query="",
                execution=QueryExecutionResult(),
                visualization=VisualizationSpec(kind="text", spec={"text": "Pipeline failure"}),
            )
            self._audit.record(
                response_to_audit(failure_response, request, status="failed", error=str(exc))
            )
            raise
        execution = final_state.get("execution") or QueryExecutionResult()
        visual = final_state.get("visual") or VisualizationSpec(kind="text", spec={"text": "No data"})
        sql = final_state.get("sql_query") or ""
        response = QueryResponse(
            sql_query=sql,
            execution=execution,
            visualization=visual,
            self_corrections=final_state.get("self_corrections", []),
            schema_used=schema,
        )
        self._memory.record_success(request.user_id, sql)
        self._audit.record(
            response_to_audit(
                response,
                request,
                status="success",
                error=final_state.get("last_error"),
            )
        )
        return response

    async def _node_generate(self, state: AgentState) -> AgentState:
        request = state["request"]
        sql, rationale = await self._generator.run(
            question=request.question,
            schema=state["schema"],
            session_id=request.session_id,
            user_id=request.user_id,
        )
        state["sql_query"] = sql
        state.setdefault("rationales", []).append(rationale)
        return state

    async def _node_execute(self, state: AgentState) -> AgentState:
        request = state["request"]
        try:
            state["execution"] = await self._verifier.run(
                sql=state["sql_query"],
                preferred_source=request.preferred_source,
                role=request.role,
            )
            state["last_error"] = None
        except Exception as exc:  # pragma: no cover - orchestrated at runtime
            state["last_error"] = str(exc)
            state["execution"] = None
        return state

    async def _node_repair(self, state: AgentState) -> AgentState:
        request = state["request"]
        sql, rationale = await self._generator.repair(
            question=request.question,
            schema=state["schema"],
            previous_sql=state.get("sql_query", ""),
            error=state.get("last_error", "engine failure"),
        )
        state["sql_query"] = sql
        state.setdefault("self_corrections", []).append(rationale)
        state["attempts"] = state.get("attempts", 0) + 1
        return state

    async def _node_visualize(self, state: AgentState) -> AgentState:
        request = state["request"]
        execution = state.get("execution")
        visual = self._visualizer.build(execution, request.output_format) if execution else None
        state["visual"] = visual
        return state

    async def _node_finalize(self, state: AgentState) -> AgentState:
        return state

    def _needs_repair(self, state: AgentState) -> Literal["retry", "visualize"]:
        if state.get("last_error") and state.get("attempts", 0) < 2:
            return "retry"
        return "visualize"


def response_to_audit(
    response: QueryResponse,
    request: QueryRequest,
    status: Literal["success", "failed"],
    error: str | None,
) -> AuditRecord:
    return AuditRecord(
        user_id=request.user_id,
        role=request.role,
        question=request.question,
        sql_query=response.sql_query,
        status=status,  # type: ignore[arg-type]
        latency_ms=response.execution.latency_ms if response.execution else 0,
        error=error,
    )
