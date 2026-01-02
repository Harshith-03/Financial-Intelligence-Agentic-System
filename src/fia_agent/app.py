"""FastAPI entrypoint for the Financial Intelligence Agent."""

from __future__ import annotations

from fastapi import FastAPI

from fia_agent.agents.conductor import ConductorGraph
from fia_agent.agents.query_generator import QueryGenerationAgent
from fia_agent.agents.verifier import QueryVerificationAgent
from fia_agent.agents.visualizer import VisualizationAgent
from fia_agent.config import BASE_DIR, Settings, get_settings
from fia_agent.models import QueryRequest, QueryResponse, TableDefinition
from fia_agent.services.audit import AuditService
from fia_agent.services.memory import MemoryManager
from fia_agent.services.query_executor import QueryExecutor
from fia_agent.services.schema_discovery import SchemaDiscoveryService
from fia_agent.services.security import RBACService
from fia_agent.services.text2sql import Text2SQLTranslator
from fia_agent.services.athena_client import AthenaClient
from fia_agent.services.snowflake_client import SnowflakeClient


def build_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    memory = MemoryManager()
    translator = Text2SQLTranslator()
    snowflake = SnowflakeClient(settings) if settings.snowflake_enabled else None
    athena = AthenaClient(settings) if settings.athena_enabled else None
    schema_service = SchemaDiscoveryService(
        sample_schema_path=BASE_DIR / "src" / "fia_agent" / "data" / "sample_schema.yaml",
        snowflake_client=snowflake,
        athena_client=athena,
    )
    generator = QueryGenerationAgent(translator=translator, memory=memory)
    executor = QueryExecutor(snowflake=snowflake, athena=athena)
    security = RBACService(settings)
    verifier = QueryVerificationAgent(executor=executor, security=security)
    visualizer = VisualizationAgent()
    audit = AuditService()
    orchestrator = ConductorGraph(
        schema_service=schema_service,
        generator=generator,
        verifier=verifier,
        visualizer=visualizer,
        memory=memory,
        audit=audit,
    )

    app = FastAPI(title="Financial Intelligence Agent", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.get("/schemas", response_model=list[TableDefinition])
    async def schema() -> list[TableDefinition]:
        return await schema_service.get_schema()

    @app.post("/query", response_model=QueryResponse)
    async def query(request: QueryRequest) -> QueryResponse:
        memory.capture_turn(request.session_id or request.user_id, "user", request.question)
        response = await orchestrator.run(request)
        return response

    @app.get("/audit")
    async def audit_feed(limit: int = 20):
        return [record.model_dump() for record in audit.recent(limit=limit)]

    return app


app = build_app()
