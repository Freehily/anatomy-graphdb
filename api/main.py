"""FastAPI application that exposes exercise data backed by Neo4j."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple

from fastapi import Depends, FastAPI, HTTPException, Query
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic import BaseModel


class ExerciseRecord(BaseModel):
    """Payload returned for a single exercise node."""

    id: str
    name: str
    body_region: str | None = None
    level: str | None = None
    target_muscle_group: str | None = None
    data: Dict[str, Any]


class ExerciseListResponse(BaseModel):
    """Standard response for paginated exercise queries."""

    items: Sequence[ExerciseRecord]
    total: int
    offset: int
    limit: int


class ExerciseRepository(Protocol):
    """Abstraction for querying exercises."""

    def list_exercises(
        self,
        *,
        search: Optional[str],
        body_region: Optional[str],
        template: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[int, Sequence[ExerciseRecord]]:
        ...

    def get_exercise(self, exercise_id: str) -> ExerciseRecord:
        ...


@dataclass
class Settings:
    """Runtime configuration sourced from environment variables."""

    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "stronger")
    neo4j_database: str | None = os.getenv("NEO4J_DATABASE") or None


class Neo4jExerciseRepository:
    """Neo4j-backed repository implementation."""

    def __init__(self, driver: Driver, database: str | None = None) -> None:
        self._driver = driver
        self._database = database

    def list_exercises(
        self,
        *,
        search: Optional[str],
        body_region: Optional[str],
        template: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[int, Sequence[ExerciseRecord]]:
        params = {
            "search": search.lower() if search else None,
            "body_region": body_region,
            "template": template,
            "limit": limit,
            "offset": offset,
        }
        where = """
            ($search IS NULL OR toLower(e.name) CONTAINS $search)
            AND ($body_region IS NULL OR e.body_region = $body_region)
            AND ($template IS NULL OR e.templateId = $template)
        """
        count_query = f"""
            MATCH (e:Exercise)
            WHERE {where}
            RETURN count(e) AS total
        """
        list_query = f"""
            MATCH (e:Exercise)
            WHERE {where}
            RETURN e
            ORDER BY e.name
            SKIP $offset
            LIMIT $limit
        """
        with self._driver.session(database=self._database) as session:
            total = session.run(count_query, **params).single()["total"]
            result = session.run(list_query, **params)
            items = [self._to_record(record["e"]) for record in result]
        return total, items

    def get_exercise(self, exercise_id: str) -> ExerciseRecord:
        query = """
            MATCH (e:Exercise {exerciseId: $exercise_id})
            RETURN e
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, exercise_id=exercise_id).single()
            if not record:
                raise KeyError(exercise_id)
            return self._to_record(record["e"])

    def _to_record(self, node) -> ExerciseRecord:
        props = dict(node)
        exercise_id = props.get("exerciseId") or props.get("id")
        if not exercise_id:
            raise ValueError("Exercise node missing 'exerciseId' property.")
        return ExerciseRecord(
            id=exercise_id,
            name=props.get("name", ""),
            body_region=props.get("body_region"),
            level=props.get("level"),
            target_muscle_group=props.get("target_muscle_group"),
            data=props,
        )


def create_app(
    *,
    settings: Settings | None = None,
    repository: ExerciseRepository | None = None,
) -> FastAPI:
    """Instantiate the FastAPI application."""

    settings = settings or Settings()
    app = FastAPI(title="Stronger API", version="0.2.0")

    if repository is None:

        @app.on_event("startup")
        def _startup() -> None:
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            app.state.neo4j_driver = driver
            app.state.repository = Neo4jExerciseRepository(driver, settings.neo4j_database)

        @app.on_event("shutdown")
        def _shutdown() -> None:
            driver = getattr(app.state, "neo4j_driver", None)
            if driver:
                driver.close()
    else:
        app.state.repository = repository

    def get_repository() -> ExerciseRepository:
        repo = getattr(app.state, "repository", None)
        if not repo:
            raise RuntimeError("Repository not initialized.")
        return repo

    @app.get("/health", tags=["meta"])
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/exercises", response_model=ExerciseListResponse, tags=["exercise"])
    def list_exercises(
        search: Optional[str] = Query(
            None,
            description="Case-insensitive substring filter applied to the exercise name.",
        ),
        body_region: Optional[str] = Query(
            None,
            description="Filter by the body_region property (e.g., 'upper_body').",
        ),
        template: Optional[str] = Query(
            None,
            description="Filter by template id.",
        ),
        limit: int = Query(
            50,
            ge=1,
            le=200,
            description="Maximum number of records to return.",
        ),
        offset: int = Query(
            0,
            ge=0,
            description="Number of matching records to skip.",
        ),
        repo: ExerciseRepository = Depends(get_repository),
    ) -> ExerciseListResponse:
        try:
            total, items = repo.list_exercises(
                search=search,
                body_region=body_region,
                template=template,
                limit=limit,
                offset=offset,
            )
        except Neo4jError as exc:  # pragma: no cover - defensive guard
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return ExerciseListResponse(items=items, total=total, offset=offset, limit=limit)

    @app.get("/exercises/{exercise_id}", response_model=ExerciseRecord, tags=["exercise"])
    def get_exercise(
        exercise_id: str,
        repo: ExerciseRepository = Depends(get_repository),
    ) -> ExerciseRecord:
        try:
            return repo.get_exercise(exercise_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Exercise '{exercise_id}' not found.") from exc

    return app


app = create_app()
