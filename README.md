# anatomy-graphdb

`anatomy-graphdb` is a Python package for loading, validating, and exporting a structured human anatomy graph from YAML configuration.

It provides:

- canonical anatomy config data under `config/`
- typed Python loaders and domain models in `anatomy_graphdb/`
- a CLI (`anatomy-graphdb`) for validation, catalog export, and Neo4j ingestion
- packaged overlay SVG assets (`anatomy_graphdb/assets/`)

## What You Can Do With It

- Validate cross-references across anatomy entities (muscles, heads, bones, nerves, arteries, actions)
- Load region-scoped or multi-region anatomy models in Python
- Export canonical catalog JSON for downstream systems
- Export Neo4j CSV artifacts or ingest directly via Bolt
- Run a local Neo4j graph build using Docker Compose + Make

## Install

```bash
pip install anatomy-graphdb
```

With Neo4j ingestion support:

```bash
pip install "anatomy-graphdb[neo4j]"
```

For development:

```bash
poetry install
```

## Quick Start

### Python API

```python
from anatomy_graphdb.databases.anatomy.loader import AnatomyLoader
from anatomy_graphdb.domain import build_anatomy_model

loader = AnatomyLoader()
region = loader.load_region("chest")
model = build_anatomy_model(region)

print(model.region)
print(len(model.muscles))
```

### CLI

List regions:

```bash
poetry run anatomy-graphdb --list-regions
```

Validate all regions:

```bash
poetry run anatomy-graphdb --region all --validate-only
```

Export Neo4j CSV artifacts:

```bash
poetry run anatomy-graphdb --region all --output data/neo4j --validate
```

Export canonical catalog JSON:

```bash
poetry run anatomy-graphdb --export-catalog --region all --catalog-output data/catalog/anatomy_catalog.json
```

Direct Bolt ingestion (requires `neo4j` extra):

```bash
poetry run anatomy-graphdb --region all --mode bolt --validate
```

## Docker Neo4j Workflow

One command end-to-end graph refresh into local Neo4j:

```bash
make neo4j-refresh-docker REGION=all
```

Useful helpers:

```bash
make neo4j-up
make neo4j-logs
make neo4j-down
```

Override defaults if needed:

```bash
make neo4j-refresh-docker REGION=chest NEO4J_AUTH=neo4j/password HTTP_PORT=7475 BOLT_PORT=7688
```

## Assets

Packaged assets:

- manifest: `anatomy_graphdb/assets/overlay_manifest.json`
- SVG files: `anatomy_graphdb/assets/anatomy/*.svg`

Legacy/reference assets (not packaged):

- `svgs/svg_front_muscles`
- `svgs/svg_rear_muscles`
- `svgs/muscles`
- `svgs/manifest.json`

## Development

Run tests:

```bash
poetry run pytest
```

## Docs

- API stability: `docs/API_STABILITY.md`
- Changelog: `CHANGELOG.md`
- Releasing: `docs/RELEASING.md`
- Asset attribution: `docs/ASSET_ATTRIBUTION.md`

## Package Metadata

- Distribution: `anatomy-graphdb`
- Import namespace: `anatomy_graphdb`
- Python: 3.12+
- License: MIT
