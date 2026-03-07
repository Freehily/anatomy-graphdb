# Changelog

All notable changes to `anatomy-graphdb` will be documented in this file.

The format is inspired by Keep a Changelog and follows semantic versioning.

## [Unreleased]

### Migration Notes
- PyPI distribution name changed from `stronger-anatomy` to `anatomy-graphdb`.
- Install commands should now use `pip install anatomy-graphdb` (or `pip install "anatomy-graphdb[neo4j]"`).
- CLI command is now `anatomy-graphdb`.
- Backward-compatibility alias `stronger-anatomy` is still provided for transition.
- Python import namespace changed from `stronger_anatomy` to `anatomy_graphdb`.
- Update imports in downstream code (for example: `from anatomy_graphdb import AnatomyLoader`).

### Added
- Top-level public package exports in `anatomy_graphdb/__init__.py`.
- CI matrix for Python 3.12 and 3.13.
- Packaging verification job (wheel + sdist install smoke tests).
- Release workflow for tag-based PyPI publishing.
- Validator coverage for orphan muscle heads.

### Changed
- Loader now merges duplicate IDs across multi-region loads instead of dropping later definitions.
- Loader now includes `config/global/*` shared data for nested regions when `include_shared=True`.
- Linked `latissimus_dorsi_head` to `latissimus_dorsi` in duplicated region files.
- Added missing forearm muscles `abductor_pollicis_brevis` and `flexor_digiti_minimi_brevis`.
- Scoped global forearm artery data to forearm regions and removed unresolved targets.

### Fixed
- `--region all` no longer loses relationship targets from duplicate region-scoped entities.
