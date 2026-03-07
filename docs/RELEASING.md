# Releasing

## Preconditions

1. CI is green on `main`.
2. `CHANGELOG.md` updated.
3. Package version in `pyproject.toml` bumped.
4. Asset licensing/attribution reviewed (`docs/ASSET_ATTRIBUTION.md`).

## Release Steps

1. Create a release PR with version + changelog updates.
2. Merge to `main`.
3. Tag the release:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`
4. GitHub Actions `Release` workflow will:
   - build wheel/sdist
   - publish to PyPI (on tag)

## Verify

1. `pip install anatomy-graphdb==X.Y.Z`
2. `anatomy-graphdb --list-regions`
3. `anatomy-graphdb --region chest --validate-only`

## Rollback

- If package data is incorrect, publish a new patch release.
- Do not delete published versions from PyPI unless absolutely necessary.
