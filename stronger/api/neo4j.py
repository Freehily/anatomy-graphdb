"""
Utility helpers for interacting with the Neo4j driver.

The FastAPI layer shares a single driver instance across requests so every
service can run lightweight queries against AuraDB instead of re-parsing YAML.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping

from neo4j import Driver, GraphDatabase

ListDict = list[Dict[str, Any]]


def _load_env_file(path: Path | None = None) -> None:
    """
    Populate os.environ with key/value pairs from a .env-style file if present.
    Existing environment variables always win so callers can override secrets.
    """

    candidate = path or Path(".env")
    if not candidate.exists():
        return
    try:
        lines = candidate.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] in {"'", '"'} and value[-1] == value[0]:
            value = value[1:-1]
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    user: str | None
    password: str | None
    database: str | None

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        _load_env_file()
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER")
        password = os.environ.get("NEO4J_PASSWORD")
        database = os.environ.get("NEO4J_DB")
        return cls(uri=uri, user=user, password=password, database=database)


class Neo4jClient:
    """Thin wrapper around the official driver that exposes simple query helpers."""

    def __init__(self, config: Neo4jConfig | None = None) -> None:
        cfg = config or Neo4jConfig.from_env()
        auth = None
        if cfg.user or cfg.password:
            auth = (cfg.user or "", cfg.password or "")
        self._config = cfg
        self._driver: Driver = GraphDatabase.driver(cfg.uri, auth=auth)

    def close(self) -> None:
        self._driver.close()

    def query(self, cypher: str, parameters: Mapping[str, Any] | None = None) -> ListDict:
        with self._driver.session(database=self._config.database) as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def query_single(self, cypher: str, parameters: Mapping[str, Any] | None = None) -> Dict[str, Any] | None:
        rows = self.query(cypher, parameters)
        return rows[0] if rows else None


@lru_cache
def get_neo4j_client() -> Neo4jClient:
    """Global client shared across FastAPI dependency instances."""

    return Neo4jClient()
