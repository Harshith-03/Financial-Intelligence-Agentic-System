"""Agent responsible for summarizing and visualizing query output."""

from __future__ import annotations

from fia_agent.models import QueryExecutionResult, VisualizationSpec


class VisualizationAgent:
    def build(self, execution: QueryExecutionResult, output_mode: str) -> VisualizationSpec:
        if output_mode == "chart" and execution.rows:
            spec = {
                "mark": "bar",
                "encoding": {
                    "x": {"field": "segment", "type": "nominal"},
                    "y": {"field": "revenue_usd", "type": "quantitative"},
                    "color": {"field": "segment", "type": "nominal"},
                },
                "data": {"values": execution.rows},
            }
            insight = f"Top segment: {max(execution.rows, key=lambda r: r.get('revenue_usd', 0)).get('segment')}"
            return VisualizationSpec(kind="bar", spec=spec, insight_summary=insight)
        if output_mode == "narrative":
            summary = f"Returned {execution.row_count} rows in {execution.latency_ms} ms from {execution.source}."
            return VisualizationSpec(kind="text", spec={"text": summary}, insight_summary=summary)
        return VisualizationSpec(kind="table", spec={"rows": execution.rows})
