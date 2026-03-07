# Stronger Anatomy (`stronger-anatomy`)

Canonical anatomy domain package for Stronger.

This repository provides:

- structured YAML anatomy data in `config/`
- typed Python loaders/models in `stronger_anatomy`
- canonical catalog exports for downstream domains (`stronger_anatomy.exports`)
- a CLI (`stronger-anatomy`) for validation and Neo4j export/ingestion
- packaged cleaned overlay SVG assets in `stronger_anatomy/assets/`

## Install

### Minimal package (no Neo4j driver)

```bash
pip install "git+https://github.com/Freehily/stronger-domain-graphdb.git"
```

### With Neo4j ingestion support

```bash
pip install "git+https://github.com/Freehily/stronger-domain-graphdb.git#egg=stronger-anatomy[neo4j]"
```

### Local development

```bash
poetry install
```

## Standalone Usage

### Load anatomy regions in Python

```python
from stronger_anatomy.databases.anatomy.loader import AnatomyLoader
from stronger_anatomy.domain import build_anatomy_model

loader = AnatomyLoader()
region = loader.load_region("chest")
model = build_anatomy_model(region)

print(model.region)
print(len(model.muscles))
```

### Access packaged overlay assets

```python
from stronger_anatomy.assets import load_overlay_manifest, asset_absolute_path

version, assets = load_overlay_manifest()
front_outline = assets["__base__"]["front"]
path = asset_absolute_path(front_outline)
print(version, path)
```

### CLI

List available regions:

```bash
poetry run stronger-anatomy --list-regions
```

Validate a region:

```bash
poetry run stronger-anatomy --region chest --validate-only
```

Export CSV artifacts:

```bash
poetry run stronger-anatomy --region all --output data/neo4j --validate
```

Export canonical anatomy catalog JSON:

```bash
poetry run stronger-anatomy --export-catalog --region all --catalog-output data/catalog/anatomy_catalog.json
```

Direct Bolt ingestion (requires `neo4j` extra):

```bash
poetry run stronger-anatomy --region all --mode bolt --validate
```

## Integration Pattern (Your Multi-Repo Setup)

Recommended layering:

1. `stronger-domain-postgres`: relational exercise/workout domain.
2. `stronger-anatomy` (this repo): anatomy graph domain + canonical overlay assets.
3. `stronger-api`: composition layer that imports both domain packages.
4. `stronger-frontend`: consumes API JSON + SVG asset URLs.

In your current setup, `stronger-api` imports this package and serves:

- anatomy graph data from YAML-derived models
- overlay manifest and SVG files from `stronger_anatomy/assets`
- catalog/version metadata for drift debugging

`stronger-domain-postgres` can consume `--export-catalog` output (or import exports directly) to seed canonical `muscle_groups` and `muscles` without duplicating anatomy configs.

The frontend should consume those API routes instead of maintaining duplicated anatomy SVG sources.

## Asset Layout

Canonical packaged assets:

- Manifest: `stronger_anatomy/assets/overlay_manifest.json`
- SVG files: `stronger_anatomy/assets/anatomy/*.svg`

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
poetry run stronger-anatomy --region all --mode bolt --validate
```

## Tests

```bash
poetry run pytest
```

## Release Notes

- Package name: `stronger-anatomy`
- Python: 3.12+
- License: MIT
