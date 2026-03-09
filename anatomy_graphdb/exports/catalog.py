from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Sequence

import yaml

from anatomy_graphdb.databases.anatomy.loader import AnatomyLoader
from anatomy_graphdb.domain import build_anatomy_model

LEGACY_MUSCLE_SLUG_ALIASES: dict[str, str] = {
    "anterior_deltoid": "deltoid",
    "posterior_deltoid": "deltoid",
    "lateral_deltoid": "deltoid",
    "deltoideus_anterior": "deltoid",
    "deltoideus_lateralis": "deltoid",
    "deltoideus_posterior": "deltoid",
    "upper_trapezius": "trapezius",
    "trapezius_upper": "trapezius",
    "trapezius_middle": "trapezius",
    "trapezius_lower": "trapezius",
    "quadriceps_femoris": "quadriceps_group",
    "quads": "quadriceps_group",
    "hamstrings": "hamstring_group",
    "hip_flexors": "hip_flexor_group",
    "adductors": "adductor_group",
    "forearm_flexors": "flexor_digitorum_superficialis",
    "pectoralis_minor": "pectoralis_major",
}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_")


def _package_version() -> str:
    try:
        return version("anatomy-graphdb")
    except PackageNotFoundError:
        return "0.0.0+local"


def _group_entries(loader: AnatomyLoader, group_slugs: set[str]) -> list[dict[str, str]]:
    path = loader.root / "body" / "muscle_groups.yaml"
    if not path.exists():
        return [{"slug": slug, "name": slug.replace("_", " ").title()} for slug in sorted(group_slugs)]

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    # Support flat list format: [{slug, name}, ...] or legacy mapping format.
    if isinstance(payload, list):
        entries = payload
    else:
        entries = payload.get("muscle_groups", {}).get("entries", [])
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in entries:
        slug = _slugify(str(item.get("slug", "")).strip())
        name = str(item.get("name", "")).strip()
        if not slug or slug not in group_slugs:
            continue
        rows.append({"slug": slug, "name": name or slug.replace("_", " ").title()})
        seen.add(slug)

    for slug in sorted(group_slugs - seen):
        rows.append({"slug": slug, "name": slug.replace("_", " ").title()})

    rows.sort(key=lambda item: item["slug"])
    return rows


def export_catalog(
    *, root: Path | None = None, regions: Sequence[str] | None = None
) -> dict[str, Any]:
    """Export canonical anatomy catalog for downstream domain packages."""
    loader = AnatomyLoader(root=root)
    selected_regions = list(regions or loader.available_regions())
    region = loader.load_regions(selected_regions)
    model = build_anatomy_model(region)

    # Build lookup from slug → catalog entry (group_slug + overlays).
    muscle_catalog = loader.load_muscle_catalog()
    catalog_by_slug = {m["slug"]: m for m in muscle_catalog}

    muscles: list[dict[str, Any]] = []
    group_slugs: set[str] = set()
    for muscle in model.muscles:
        cat = catalog_by_slug.get(muscle.id, {})
        group_slug = cat.get("group_slug") or _slugify(muscle.group or "")
        if group_slug:
            group_slugs.add(group_slug)
        muscles.append(
            {
                "slug": muscle.id,
                "name": muscle.name,
                "group_slug": group_slug or None,
                "description": muscle.description,
                "order": muscle.order,
            }
        )

    muscles.sort(key=lambda item: item["slug"])
    groups = _group_entries(loader, group_slugs)

    # Build per-muscle overlay map from the body catalog.
    muscle_overlays: dict[str, list[dict]] = {
        m["slug"]: m["overlays"]
        for m in muscle_catalog
        if m.get("overlays")
    }

    return {
        "version": 1,
        "package_version": _package_version(),
        "generated_at": datetime.now(UTC).isoformat(),
        "regions": selected_regions,
        "muscle_groups": groups,
        "muscles": muscles,
        "muscle_slug_aliases": LEGACY_MUSCLE_SLUG_ALIASES,
        "muscle_overlays": muscle_overlays,
    }


def write_catalog_json(catalog: dict[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
