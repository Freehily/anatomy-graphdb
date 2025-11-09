# stronger

## FastAPI Exercise API

Run the read-only API that serves the exercise dataset:

```bash
poetry install
poetry run uvicorn stronger.api.main:app --reload
```

Available routes:

- `GET /health` – lightweight readiness probe.
- `GET /exercises` – list exercises with optional `search`, `body_region`, `template`, `limit`, and `offset` filters.
- `GET /exercises/{exercise_id}` – fetch a specific exercise record (e.g., `ab_wheel_kneeling_rollout`).

The API uses the existing YAML configs under `stronger/databases/exercises/configs/`, so refresh those via the loaders before starting the server if you need the latest data.

## Neo4j via Docker

1. Export the anatomy/exercise graph to CSV (example for upper limb):
   ```bash
   poetry run python stronger/databases/anatomy/scripts/build_graph.py \
     --region upper_limb --output data/neo4j --validate
   ```
2. Import the CSVs into a Neo4j database using the helper (run once per region/database):
   ```bash
   chmod +x scripts/import_neo4j.sh
   scripts/import_neo4j.sh upper_limb stronger_dev
   ```
   - The script wraps `neo4j-admin database import full` via Docker Compose and reads from `data/neo4j/<region>`.
   - Override credentials by exporting `NEO4J_AUTH=user/password` (defaults to `neo4j/stronger`), add flags such as `--verbose`, and pick database names that only contain letters, digits, dots, or dashes (e.g., `stronger-dev`).
   - Make sure your user can talk to Docker (run `sudo usermod -aG docker $USER` and re-login or prefix the script with `sudo`).
3. Start the database:
   ```bash
   docker compose -f docker-compose.neo4j.yml up neo4j
   ```
   Access the browser at http://localhost:7474 and connect over Bolt on `bolt://localhost:7687`.
4. After the initial import, apply the constraints listed in `stronger/databases/anatomy/README.md` so future ingests stay idempotent.

Use `docker compose -f docker-compose.neo4j.yml down` to stop the container, and rerun `scripts/import_neo4j.sh` whenever you regenerate the CSV artifacts.
