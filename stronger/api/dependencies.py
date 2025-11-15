"""FastAPI dependency helpers."""

from functools import lru_cache

from stronger.api.neo4j import get_neo4j_client
from stronger.api.services.anatomy import AnatomyService


@lru_cache
def get_anatomy_service() -> AnatomyService:
    """Singleton-style dependency for wiring the anatomy service into routes."""

    return AnatomyService(client=get_neo4j_client())
