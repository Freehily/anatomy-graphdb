from __future__ import annotations

import pytest

from stronger_anatomy.assets import OverlayAssetManifestError, asset_absolute_path, load_overlay_manifest


def test_overlay_manifest_loads_and_contains_base() -> None:
    version, assets = load_overlay_manifest()
    assert isinstance(version, int)
    assert version >= 1
    assert "__base__" in assets
    assert assets["__base__"].get("front")


def test_overlay_manifest_paths_resolve_to_files() -> None:
    _, assets = load_overlay_manifest()
    for entry in assets.values():
        for relative_path in entry.values():
            resolved = asset_absolute_path(relative_path)
            assert resolved.is_file()


def test_overlay_asset_path_rejects_escape_attempts() -> None:
    with pytest.raises(OverlayAssetManifestError):
        asset_absolute_path("../README.md")
