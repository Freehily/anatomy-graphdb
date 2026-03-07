# Stronger Anatomy (`anatomy-graphdb`)

Canonical anatomy domain package for Stronger.

This repository provides:

- structured YAML anatomy data in `config/`
- typed Python loaders/models in `anatomy_graphdb`
- canonical catalog exports for downstream domains (`anatomy_graphdb.exports`)
- a CLI (`anatomy-graphdb`) for validation and Neo4j export/ingestion
- packaged cleaned overlay SVG assets in `anatomy_graphdb/assets/`

## Install

### Minimal package (no Neo4j driver)

```bash
pip install anatomy-graphdb
```

### With Neo4j ingestion support

```bash
pip install "anatomy-graphdb[neo4j]"
```

### Local development

```bash
poetry install
```

## Standalone Usage

### Load anatomy regions in Python

```python
from anatomy_graphdb.databases.anatomy.loader import AnatomyLoader
from anatomy_graphdb.domain import build_anatomy_model

loader = AnatomyLoader()
region = loader.load_region("chest")
model = build_anatomy_model(region)

print(model.region)
print(len(model.muscles))
```

### Access packaged overlay assets

```python
from anatomy_graphdb.assets import load_overlay_manifest, asset_absolute_path

version, assets = load_overlay_manifest()
front_outline = assets["__base__"]["front"]
path = asset_absolute_path(front_outline)
print(version, path)
```

### CLI

List available regions:

```bash
poetry run anatomy-graphdb --list-regions
```

Validate a region:

```bash
poetry run anatomy-graphdb --region chest --validate-only
```

Export CSV artifacts:

```bash
poetry run anatomy-graphdb --region all --output data/neo4j --validate
```

Export canonical anatomy catalog JSON:

```bash
poetry run anatomy-graphdb --export-catalog --region all --catalog-output data/catalog/anatomy_catalog.json
```

Direct Bolt ingestion (requires `neo4j` extra):

```bash
poetry run anatomy-graphdb --region all --mode bolt --validate
```

## Integration Pattern (Your Multi-Repo Setup)

Recommended layering:

1. `stronger-domain-postgres`: relational exercise/workout domain.
2. `anatomy-graphdb` (this repo): anatomy graph domain + canonical overlay assets.
3. `stronger-api`: composition layer that imports both domain packages.
4. `stronger-frontend`: consumes API JSON + SVG asset URLs.

In your current setup, `stronger-api` imports this package and serves:

- anatomy graph data from YAML-derived models
- overlay manifest and SVG files from `anatomy_graphdb/assets`
- catalog/version metadata for drift debugging

`stronger-domain-postgres` can consume `--export-catalog` output (or import exports directly) to seed canonical `muscle_groups` and `muscles` without duplicating anatomy configs.

The frontend should consume those API routes instead of maintaining duplicated anatomy SVG sources.

## Asset Layout

Canonical packaged assets:

- Manifest: `anatomy_graphdb/assets/overlay_manifest.json`
- SVG files: `anatomy_graphdb/assets/anatomy/*.svg`

Legacy repo-only assets (not packaged into wheels):

- `svgs/svg_front_muscles`
- `svgs/svg_rear_muscles`
- `svgs/muscles`
- `svgs/manifest.json`

Those `svgs/` folders are retained for historical/reference tooling only.

## Neo4j Configuration

When using bolt mode, configure environment variables:

```dotenv
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

For AuraDB:

```dotenv
NEO4J_URI=neo4j+s://<instance-id>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
NEO4J_DATABASE=neo4j
```

Then run:

```bash
poetry run anatomy-graphdb --region all --mode bolt --validate
```

## Docker Graph Build

You can run Neo4j in Docker and build/populate the graph in one command:

```bash
make neo4j-refresh-docker REGION=all
```

Useful helpers:

```bash
make neo4j-up
make neo4j-logs
make neo4j-down
```

Override defaults when needed:

```bash
make neo4j-refresh-docker REGION=chest NEO4J_AUTH=neo4j/password HTTP_PORT=7475 BOLT_PORT=7688
```

## Tests

```bash
poetry run pytest
```

## Public API and Versioning

- Stable API surface: `docs/API_STABILITY.md`
- Changelog: `CHANGELOG.md`
- Release process: `docs/RELEASING.md`
- Asset attribution policy: `docs/ASSET_ATTRIBUTION.md`

## Package Metadata

- Package name: `anatomy-graphdb`
- Python: 3.12+
- License: MIT
