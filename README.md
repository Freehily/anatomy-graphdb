# stronger domain graph

This repository is the canonical source of truth for the Stronger anatomy and exercise datasets plus the tooling that turns them into a Neo4j property graph. The upcoming API and frontend repos will import the Python package published here or consume the exported CSV artifacts.

## What lives here

- `stronger/databases/anatomy` – region-sharded YAML describing bones, attachment points, muscles, nerves, arteries, and actions. Includes validators, SVG references, and Neo4j exporters.
- `stronger/databases/exercises` – taxonomy definitions, canonical exercise templates, and the CSV→YAML converter for training movements.
- `stronger/databases/**/scripts` – CLIs for validating configs, regenerating derived files, and building CSV/Bolt payloads for Neo4j.
- `data/neo4j/<region>` – generated artifacts ready for `neo4j-admin database import` (ignored by git).

No web server code lives here anymore—treat this as the domain+data module that other services depend on.

## Getting started

```bash
poetry install
```

All commands below assume the virtual environment created by Poetry.

### Refresh exercise configs

If you have an updated `data/exercise_data_raw.csv`, rebuild the YAML configs:

```bash
poetry run python stronger/databases/exercises/scripts/build_dataset.py --csv data/exercise_data_raw.csv
poetry run python stronger/databases/exercises/scripts/validate_configs.py
```

### Build/validate the anatomy graph

Export anatomy (and, by default, exercise) data for one or more regions:

```bash
poetry run python stronger/databases/anatomy/scripts/build_graph.py \
  --region upper_limb \
  --output data/neo4j \
  --validate
```

Flags worth knowing:

- `--region all` or `--region upper_limb,lower_limb` to stitch multiple regions together.
- `--no-exercises` if you only need the anatomy portion.
- `--mode bolt` plus `--neo4j-uri/--neo4j-user/--neo4j-password` to ingest directly into a running database (requires the `neo4j` Python driver, already listed in `pyproject.toml`).

### End-to-end Neo4j workflow

The Makefile wraps the full export → import → run loop:

```bash
# Export CSVs, import them with neo4j-admin, and boot a dockerized instance
make neo4j-refresh REGION=all

# Or run the helper script (accepts the same flags as make)
scripts/refresh_neo4j.sh REGION=upper_limb
```

Artifacts land in `data/neo4j/<region>`, databases in `neo4j-data/`, and logs in `neo4j-logs/`. Adjust `DB_NAME`, `CONTAINER_NAME`, or ports at the top of the `Makefile`.

### Tests

```bash
poetry run pytest
```

The test suite exercises the unified graph builder via subprocess to ensure CSV generation keeps working.

## Consuming this repo from the API/frontend

The future API repo can either:

1. Declare a dependency on this package (e.g., via a git reference) and call into `stronger.databases.*` to fetch normalized data at runtime, **or**
2. Pull the exported CSV artifacts from `data/neo4j/<region>` and hydrate its own backing store.

The frontend repo would typically talk to the API, but it can also source static metadata (taxonomies, exercise templates) by reading the YAML configs here if needed.

## FAQ: Do we need SQLAlchemy-style tables?

No. The graph layer is modeled as dataclasses/YAML (see `ExerciseLoader`, `AnatomyLoader`, etc.) and ultimately materializes into Neo4j nodes/relationships. If you want strongly-typed helpers, prefer lightweight dataclasses or Pydantic models within this repo and keep relational ORMs such as SQLAlchemy inside the API service where a relational database actually exists.
