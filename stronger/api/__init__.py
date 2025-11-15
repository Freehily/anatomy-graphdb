"""
Public FastAPI application entrypoint for Stronger.

Downstream ASGI servers should import `stronger.api.app` or call `create_app()`
to obtain a configured instance (e.g., `uvicorn stronger.api:app`).
"""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stronger.api.routers.anatomy import router as anatomy_router


def _cors_origins() -> list[str]:
    raw = os.environ.get("STRONGER_CORS_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stronger Domain API",
        version="0.1.0",
        description="Read-only endpoints that expose the curated anatomy dataset backed by Neo4j.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(anatomy_router)
    return app


app = create_app()

__all__ = ["app", "create_app"]
