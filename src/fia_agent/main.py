"""CLI entry point for launching the FastAPI application."""

from __future__ import annotations

import uvicorn

from fia_agent.config import get_settings
from fia_agent.app import build_app


def run() -> None:
    settings = get_settings()
    app = build_app(settings)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level=settings.log_level.lower())


if __name__ == "__main__":
    run()
