# Contributing

Thanks for contributing to `stronger-domain-graphdb`.

## Scope

This repository is the canonical source for:

- anatomy YAML data under `config/`
- Python loaders/domain models under `anatomy_graphdb/`
- Neo4j export/ingest tooling

## Local setup

```bash
poetry install
```

Useful commands:

```bash
poetry run anatomy-graphdb --list-regions
poetry run anatomy-graphdb --region chest --validate-only
poetry run pytest
```

## Contribution workflow

1. Create a branch from `main`.
2. Make focused changes (data, code, or docs).
3. Validate affected regions:
   - `poetry run anatomy-graphdb --region <region> --validate-only`
   - for broad changes: `poetry run anatomy-graphdb --region all --validate-only`
4. Run tests: `poetry run pytest`.
5. Open a PR with:
   - summary of changes
   - affected regions/sections
   - validation/test output
6. For release-impacting changes:
   - update `CHANGELOG.md`
   - note API changes against `docs/API_STABILITY.md`

## Data change guidance

When editing YAML in `config/`:

- Keep IDs stable once published.
- Prefer additive changes over renames/removals.
- Ensure references resolve across sections:
  - muscles <-> muscle_heads
  - attachment_points <-> bones
  - actions/nerves/arteries -> muscle or muscle_head IDs
- Run validation before submitting.

## Code style

- Keep public API changes explicit in PR descriptions.
- Add tests for behavior changes, especially loader and CLI behavior.
- Keep README docs in sync with CLI flags and workflows.

## Commit/PR quality

- One logical change per PR where possible.
- Include migration notes if IDs or schema fields change.
- Do not commit secrets (`.env`, credentials, tokens).
- For publish prep, follow `docs/RELEASING.md`.
