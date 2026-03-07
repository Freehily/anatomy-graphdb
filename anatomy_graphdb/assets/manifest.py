from __future__ import annotations

import json
from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parent
_MANIFEST_PATH = _ASSETS_DIR / "overlay_manifest.json"


class OverlayAssetManifestError(RuntimeError):
    """Raised when the overlay manifest is invalid or references missing files."""


def load_overlay_manifest() -> tuple[int, dict[str, dict[str, str]]]:
    """Load and validate the packaged overlay manifest."""
    try:
        payload = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OverlayAssetManifestError(f"Overlay manifest not found: {_MANIFEST_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise OverlayAssetManifestError(f"Overlay manifest is not valid JSON: {_MANIFEST_PATH}") from exc

    if not isinstance(payload, dict):
        raise OverlayAssetManifestError("Overlay manifest root must be a JSON object.")

    version = payload.get("version")
    assets = payload.get("assets")
    if not isinstance(version, int):
        raise OverlayAssetManifestError("Overlay manifest must include integer field 'version'.")
    if not isinstance(assets, dict):
        raise OverlayAssetManifestError("Overlay manifest must include object field 'assets'.")

    validated: dict[str, dict[str, str]] = {}
    for slug, entry in assets.items():
        if not isinstance(slug, str) or not slug.strip():
            raise OverlayAssetManifestError("Overlay manifest contains an empty or non-string key.")
        if not isinstance(entry, dict):
            raise OverlayAssetManifestError(f"Overlay manifest entry for '{slug}' must be an object.")

        cleaned: dict[str, str] = {}
        for view in ("front", "back"):
            value = entry.get(view)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                raise OverlayAssetManifestError(
                    f"Overlay manifest entry '{slug}.{view}' must be a non-empty string."
                )
            asset_absolute_path(value)
            cleaned[view] = value

        if not cleaned:
            raise OverlayAssetManifestError(
                f"Overlay manifest entry for '{slug}' must define at least one of front/back."
            )
        validated[slug] = cleaned

    return version, validated


def asset_absolute_path(relative_path: str) -> Path:
    """Resolve a manifest path into an absolute packaged file path."""
    candidate = (_ASSETS_DIR / relative_path).resolve()
    assets_root = _ASSETS_DIR.resolve()
    if assets_root not in candidate.parents and candidate != assets_root:
        raise OverlayAssetManifestError(f"Overlay asset path escapes assets directory: {relative_path}")
    if not candidate.is_file():
        raise OverlayAssetManifestError(f"Overlay asset file does not exist: {relative_path}")
    return candidate
