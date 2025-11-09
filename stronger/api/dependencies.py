"""FastAPI dependency helpers."""

from functools import lru_cache

from stronger.api.services.anatomy import AnatomyService
from stronger.api.services.exercises import ExerciseService


@lru_cache
def get_anatomy_service() -> AnatomyService:
    """Singleton-style dependency for wiring the anatomy service into routes."""

    return AnatomyService()


@lru_cache
def get_exercise_service() -> ExerciseService:
    """Shared ExerciseService instance for FastAPI dependency injection."""

    return ExerciseService()
