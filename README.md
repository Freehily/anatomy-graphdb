# Stronger Backend

This repository is the canonical source of truth for the Stronger anatomy and exercise datasets plus the tooling that turns them into a Neo4j property graph. The upcoming API and frontend repos will import the Python package published here or consume the exported CSV artifacts.

## What lives here

- `stronger/databases/anatomy` – region-sharded YAML describing bones, attachment points, muscles, nerves, arteries, and actions. Includes validators, SVG references, and Neo4j exporters.
- `stronger/databases/exercises` – taxonomy definitions, canonical exercise templates, and the CSV→YAML converter for training movements.
- `stronger/domain` – dataclasses that offer a typed view of the YAML configs so downstream services can work with explicit models instead of dictionaries.
- `stronger/api` – a thin FastAPI layer that exposes the domain objects over HTTP for prototyping or lightweight consumers.
- `stronger/databases/**/scripts` – CLIs for validating configs, regenerating derived files, and building CSV/Bolt payloads for Neo4j.
- `data/neo4j/<region>` – generated artifacts ready for `neo4j-admin database import` (ignored by git).

This repository remains the canonical domain+data module; the bundled API is optional and intentionally thin so other services can import and run it without copying code.

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

### Run the optional API

Install the API dependency group and boot uvicorn:

```bash
poetry install --with api
poetry run uvicorn stronger.api:app --reload
```

Endpoints:

- `GET /anatomy/regions` – list available regions on disk.
- `GET /anatomy/regions/{region}` – return the full typed model (bones, muscles, etc.).
- `GET /anatomy/regions/{region}/sections/{section}` – fetch a single section such as `muscles` or `arteries`.
- `GET /exercises/taxonomies` – enumerate taxonomy keys (difficulty, mechanics, etc.) and inspect them via `/{key}`.
- `GET /exercises/templates` – list base exercise templates and their variants.
- `GET /exercises/variants?body_region=upper_body` – stream concrete exercise variants (optionally filter by region) or fetch one via `/variants/{exercise_id}`. Use `/variants/{exercise_id}/equipment` for a focused equipment payload.
- `GET /exercises/equipment` (or `/equipment/{equipment_id}/variants`) – browse available implements and the exercises that use them.
- `GET /exercises/muscle-groups` – list high-level buckets, `/muscle-groups/{group_id}/muscles` to see the contributing aliases, and `/muscle-groups/{group_id}/variants` to see the matching exercises. Prefer `/muscles/{alias}/variants` for alias-level drilldowns.
- `GET /exercises/muscle-aliases` – expose supporting metadata for UI builders.

Anatomy endpoints accept `?include_shared=false` to exclude shared definitions.

### Muscle SVG assets

- Raw vendor art lives under `svgs/svg_front_muscles` and `svgs/svg_rear_muscles`.
- Run `poetry run python scripts/normalize_svgs.py` to copy/rename everything into `svgs/muscles/<muscle_id>/<view>.svg` and emit `svgs/manifest.json`.
- The manifest is keyed by anatomy ID and records the relative path, source filename, and optional variant (e.g., `rectus_abdominis` has both `front.svg` and `front_lower.svg`). This lets the API or frontend inject artwork without guessing filenames.

### Tests

```bash
poetry run pytest
```

The test suite exercises the unified graph builder via subprocess to ensure CSV generation keeps working.


