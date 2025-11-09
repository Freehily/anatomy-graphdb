"""
Public FastAPI application entrypoint for Stronger.

Downstream ASGI servers should import `stronger.api.app` or call `create_app()`
to obtain a configured instance (e.g., `uvicorn stronger.api:app`).
"""

from fastapi import FastAPI

from stronger.api.routers.anatomy import router as anatomy_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Stronger Domain API",
        version="0.1.0",
        description="Read-only endpoints that expose the curated anatomy dataset.",
    )
    app.include_router(anatomy_router)
    return app


app = create_app()

__all__ = ["app", "create_app"]
