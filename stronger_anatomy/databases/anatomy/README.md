# Anatomy Database Toolkit

This package contains YAML configs that describe anatomical structures, a validation helper, and tooling to export the data into a Neo4j property graph.

## Validation

Use the unified CLI to check referential integrity for any region:

```
poetry run stronger-anatomy --region chest --validate-only
```

Pass a comma-separated list (`--region chest,shoulders`) or `--region all` to cover multiple muscle groups. Add `--list-regions` to discover which directories under `config/<category>/` are available. The validator loads all of the YAML files and ensures every attachment, muscle head, muscle, nerve, artery, and action reference resolves correctly. A non-zero exit code highlights missing or misspelled IDs so the command can run in CI.

## Neo4j Export Workflow

1. Generate artifacts with the unified graph builder:
   ```
   # CSV export (default mode)
   poetry run stronger-anatomy --region chest --output data/neo4j

   # Direct Bolt ingestion (requires `neo4j` extras)
   poetry run stronger-anatomy --region chest --mode bolt \
       --neo4j-uri bolt://localhost:7687 --neo4j-user neo4j --neo4j-password password
   ```

   Output defaults to `data/neo4j/<region>` unless `--output` is provided.

   Add `--validate` to enforce referential checks before exporting, and `--list-regions`
   to discover available directories under `config/<category>/<region>`. Set
   `--region all` / pass a comma-separated list (e.g., `--region chest,shoulders`) to aggregate multiple
   anatomy folders into a single export.

   The script automatically reads `.env` from the repo root (if present) and applies any `NEO4J_*` variables before parsing CLI flags, so stash your Aura/local credentials there to avoid repeating them.

2. Import into a local Neo4j instance (example commands):
   ```
   neo4j-admin database import full chest \
     --nodes=data/neo4j/chest/nodes_bones.csv \
     --nodes=data/neo4j/chest/nodes_attachment_points.csv \
     --nodes=data/neo4j/chest/nodes_muscles.csv \
     --nodes=data/neo4j/chest/nodes_muscle_heads.csv \
     --nodes=data/neo4j/chest/nodes_nerves.csv \
     --nodes=data/neo4j/chest/nodes_arteries.csv \
     --nodes=data/neo4j/chest/nodes_actions.csv \
     --relationships=data/neo4j/chest/rels_bone_attachment.csv \
     --relationships=data/neo4j/chest/rels_muscle_head.csv \
     --relationships=data/neo4j/chest/rels_muscle_insertion.csv \
     --relationships=data/neo4j/chest/rels_muscle_antagonist_muscle.csv \
     --relationships=data/neo4j/chest/rels_muscle_antagonist_head.csv \
     --relationships=data/neo4j/chest/rels_head_origin.csv \
     --relationships=data/neo4j/chest/rels_head_innervation.csv \
     --relationships=data/neo4j/chest/rels_head_artery.csv \
     --relationships=data/neo4j/chest/rels_nerve_targets_muscle.csv \
     --relationships=data/neo4j/chest/rels_nerve_targets_head.csv \
     --relationships=data/neo4j/chest/rels_artery_supplies_muscle.csv \
     --relationships=data/neo4j/chest/rels_artery_supplies_head.csv \
     --relationships=data/neo4j/chest/rels_artery_branches.csv \
     --relationships=data/neo4j/chest/rels_action_primary_muscle.csv \
     --relationships=data/neo4j/chest/rels_action_primary_head.csv
   ```

   You can also use the repository helper (`scripts/import_neo4j.sh`) which wraps `neo4j-admin database import full`
   via Docker Compose and feeds it all of the CSV artifacts for a given region.

3. Start Neo4j and run sanity checks. Example Cypher:
   ```
   MATCH (m:Muscle {id: 'flexor_digitorum_profundus'})-[:INSERTS_AT]->(ap)
   RETURN m.name, ap.name;
   ```

## Suggested Constraints

In the Neo4j browser or via `cypher-shell`, apply uniqueness and relationship guidance:

```
CREATE CONSTRAINT bone_id IF NOT EXISTS FOR (b:Bone) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT attach_id IF NOT EXISTS FOR (a:AttachmentPoint) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT muscle_id IF NOT EXISTS FOR (m:Muscle) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT head_id IF NOT EXISTS FOR (h:MuscleHead) REQUIRE h.id IS UNIQUE;
CREATE CONSTRAINT nerve_id IF NOT EXISTS FOR (n:Nerve) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT artery_id IF NOT EXISTS FOR (a:Artery) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE;
```

These constraints ensure imports remain idempotent and protect future updates.
