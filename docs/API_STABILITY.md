# API Stability

This project exposes a stable public API for downstream packages and services.

## Stable Surface (Minor-Version Compatible)

- `anatomy_graphdb.__version__`
- `anatomy_graphdb.AnatomyLoader`
- `anatomy_graphdb.AnatomyRegion`
- `anatomy_graphdb.AnatomyConfigError`
- `anatomy_graphdb.build_anatomy_model`
- `anatomy_graphdb.AnatomyModel`
- `anatomy_graphdb.Bone`
- `anatomy_graphdb.AttachmentPoint`
- `anatomy_graphdb.Muscle`
- `anatomy_graphdb.MuscleHead`
- `anatomy_graphdb.Nerve`
- `anatomy_graphdb.Artery`
- `anatomy_graphdb.Action`
- `anatomy_graphdb.load_overlay_manifest`
- `anatomy_graphdb.asset_absolute_path`
- `anatomy_graphdb.export_catalog`
- `anatomy_graphdb.write_catalog_json`
- CLI command `anatomy-graphdb` and existing documented flags

## Stability Rules

- No breaking changes to the stable surface in patch/minor releases.
- Breaking changes require a major version bump.
- Data IDs in `config/**/*.yaml` are treated as stable once released.
- New fields may be added, but existing keys should not be renamed/removed without a major release and migration note.

## Internal/Unstable

- Modules or functions not exported through `anatomy_graphdb/__init__.py`.
- Internal YAML layout details outside documented contract.
- Neo4j artifact internal CSV column ordering unless explicitly documented.

## Deprecation Policy

- Mark deprecated APIs in docs and release notes.
- Keep deprecated APIs for at least one minor release before removal.
