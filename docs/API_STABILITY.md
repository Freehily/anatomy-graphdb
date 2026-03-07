# API Stability

This project exposes a stable public API for downstream packages and services.

## Stable Surface (Minor-Version Compatible)

- `stronger_anatomy.__version__`
- `stronger_anatomy.AnatomyLoader`
- `stronger_anatomy.AnatomyRegion`
- `stronger_anatomy.AnatomyConfigError`
- `stronger_anatomy.build_anatomy_model`
- `stronger_anatomy.AnatomyModel`
- `stronger_anatomy.Bone`
- `stronger_anatomy.AttachmentPoint`
- `stronger_anatomy.Muscle`
- `stronger_anatomy.MuscleHead`
- `stronger_anatomy.Nerve`
- `stronger_anatomy.Artery`
- `stronger_anatomy.Action`
- `stronger_anatomy.load_overlay_manifest`
- `stronger_anatomy.asset_absolute_path`
- `stronger_anatomy.export_catalog`
- `stronger_anatomy.write_catalog_json`
- CLI command `stronger-anatomy` and existing documented flags

## Stability Rules

- No breaking changes to the stable surface in patch/minor releases.
- Breaking changes require a major version bump.
- Data IDs in `config/**/*.yaml` are treated as stable once released.
- New fields may be added, but existing keys should not be renamed/removed without a major release and migration note.

## Internal/Unstable

- Modules or functions not exported through `stronger_anatomy/__init__.py`.
- Internal YAML layout details outside documented contract.
- Neo4j artifact internal CSV column ordering unless explicitly documented.

## Deprecation Policy

- Mark deprecated APIs in docs and release notes.
- Keep deprecated APIs for at least one minor release before removal.
