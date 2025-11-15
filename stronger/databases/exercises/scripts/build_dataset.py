"""
Convert the raw exercise CSV into normalised YAML configs that match the new
folder structure (`configs/index.yaml`).

Example:
    poetry run python stronger/databases/exercises/scripts/build_dataset.py \
        --csv data/exercise_data_raw.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence

import yaml

from stronger.databases.anatomy.loader import AnatomyLoader

CUSTOM_ALIAS_TARGETS: Dict[str, List[str]] = {
    "anterior_deltoids": ["deltoid_anterior"],
    "lateral_deltoids": ["deltoid_middle"],
    "medial_deltoids": ["deltoid_middle"],
    "posterior_deltoids": ["deltoid_posterior"],
    "erector_spinae": ["erector_spinae_spinalis", "erector_spinae_longissimus", "erector_spinae_iliocostalis"],
    "iliopsoas": ["hip_flexor_group"],
    "obliques": ["external_oblique", "internal_oblique"],
    "quadriceps_femoris": ["rectus_femoris", "vastus_lateralis", "vastus_medialis", "vastus_intermedius"],
    "rhomboids": ["rhomboid_major", "rhomboid_minor"],
    "transverse_abdominis": ["transversus_abdominis"],
    "upper_trapezius": ["trapezius"],
    "vastus_mediais": ["vastus_medialis"],
}

CONFIG_ROOT = Path(__file__).resolve().parents[1] / "configs"


def slugify(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or None


def load_taxonomy_map(path: Path) -> Dict[str, str]:
    with path.open() as handle:
        data = yaml.safe_load(handle) or {}
    # taxonomies store a single top-level key (e.g., movement_patterns)
    key = next(iter(data))
    mapping: Dict[str, str] = {}
    for entry in data[key]:
        entry_id = entry["id"]
        mapping[entry["name"]] = entry_id
        for alias in entry.get("aliases", []) or []:
            mapping[alias] = entry_id
    return mapping


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_yaml(path: Path, payload: MutableMapping[str, object]) -> None:
    ensure_dir(path)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def read_rows(csv_path: Path, limit: int | None) -> List[Mapping[str, str]]:
    rows: List[Mapping[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            rows.append(row)
            if limit and idx + 1 >= limit:
                break
    return rows


def normalise_value(value: str | None, mapping: Dict[str, str], *, default: str | None = None) -> str | None:
    value = (value or "").strip()
    if not value:
        return default
    if value in mapping:
        return mapping[value]
    slug = slugify(value)
    return slug or default


def build_dataset(rows: Sequence[Mapping[str, str]], args: argparse.Namespace) -> None:
    index_path = CONFIG_ROOT / "index.yaml"
    index = yaml.safe_load(index_path.read_text())

    tax_paths = index["taxonomies"]

    taxonomy_maps = {
        "difficulty": load_taxonomy_map(CONFIG_ROOT / tax_paths["difficulty_levels"]),
        "body_region": load_taxonomy_map(CONFIG_ROOT / tax_paths["body_regions"]),
        "force_type": load_taxonomy_map(CONFIG_ROOT / tax_paths["force_types"]),
        "mechanics": load_taxonomy_map(CONFIG_ROOT / tax_paths["mechanics"]),
        "laterality": load_taxonomy_map(CONFIG_ROOT / tax_paths["laterality"]),
        "classification": load_taxonomy_map(CONFIG_ROOT / tax_paths["classifications"]),
        "posture": load_taxonomy_map(CONFIG_ROOT / tax_paths["postures"]),
        "combination": load_taxonomy_map(CONFIG_ROOT / tax_paths["combination_types"]),
        "load_position": load_taxonomy_map(CONFIG_ROOT / tax_paths["load_positions"]),
        "grip": load_taxonomy_map(CONFIG_ROOT / tax_paths["grips"]),
        "arm_usage": load_taxonomy_map(CONFIG_ROOT / tax_paths["arm_usage"]),
        "limb_cadence": load_taxonomy_map(CONFIG_ROOT / tax_paths["limb_cadence"]),
        "foot_elevation": load_taxonomy_map(CONFIG_ROOT / tax_paths["foot_elevations"]),
        "movement_patterns": load_taxonomy_map(CONFIG_ROOT / tax_paths["movement_patterns"]),
        "planes": load_taxonomy_map(CONFIG_ROOT / tax_paths["planes"]),
    }

    muscle_group_map = load_taxonomy_map(CONFIG_ROOT / index["muscle_groups"]["definitions"])

    equipment_items = yaml.safe_load((CONFIG_ROOT / index["equipment"]["items"]).read_text())["equipment"]
    equipment_map = {item["name"]: item["id"] for item in equipment_items}
    for item in equipment_items:
        for alias in item.get("aliases", []) or []:
            equipment_map[alias] = item["id"]

    anatomy_loader = AnatomyLoader()
    all_regions = anatomy_loader.available_regions()
    anatomy_region = anatomy_loader.load_regions(all_regions)
    muscle_ids = {item["id"] for item in anatomy_region.require("muscles").items}
    muscle_head_ids = {item["id"] for item in anatomy_region.require("muscle_heads").items}

    templates: Dict[str, Dict[str, object]] = {}
    region_buckets: Dict[str, List[dict]] = defaultdict(list)
    muscle_aliases: Dict[str, str] = {}

    def template_id(name: str) -> str:
        base = name.strip()
        if base.endswith(")") and "(" in base:
            base = base[: base.rfind("(")].strip()
        return slugify(base) or slugify(name) or "exercise"

    for row in rows:
        name = row["exercise"].strip()
        if not name:
            continue

        ex_id = slugify(name)
        template_slug = template_id(name)
        template_entry = templates.setdefault(
            template_slug,
            {"id": template_slug, "name": re.sub(r"\s+", " ", template_slug.replace("_", " ")).title(), "aliases": set(), "variants": []},
        )
        template_entry["aliases"].add(name)
        template_entry["variants"].append(ex_id)

        def map_value(key: str, mapping_name: str, default: str | None = None) -> str | None:
            mapping = taxonomy_maps[mapping_name]
            return normalise_value(row.get(key), mapping, default=default)

        level = map_value("difficulty_level", "difficulty")
        body_region = map_value("body_region", "body_region")
        force_type = map_value("force_type", "force_type")
        mechanics = map_value("mechanics", "mechanics")
        laterality = map_value("laterality", "laterality")
        classification = map_value("primary_exercise_classification", "classification")
        posture = map_value("posture", "posture")
        combination = map_value("combination_exercises", "combination")
        load_position = map_value("load_position_ending", "load_position")
        grip = map_value("grip", "grip")
        arms_mode = map_value("single_or_double_arm", "arm_usage")
        arms_cadence = map_value("continuous_or_alternating_arms", "limb_cadence")
        legs_cadence = map_value("continuous_or_alternating_legs", "limb_cadence")
        foot_elevation = map_value("foot_elevation", "foot_elevation")

        def collect_patterns(prefix: str, mapping_name: str) -> List[str]:
            values: List[str] = []
            for idx in (1, 2, 3):
                raw_value = row.get(f"{prefix}_{idx}")
                if not raw_value:
                    continue
                mapped = normalise_value(raw_value, taxonomy_maps[mapping_name])
                if mapped:
                    values.append(mapped)
            return values

        movement_patterns = collect_patterns("movement_pattern", "movement_patterns")
        planes = collect_patterns("plane_of_motion", "planes")

        def normalise_equipment(raw_value: str) -> str | None:
            raw_value = (raw_value or "").strip()
            if not raw_value:
                return None
            if raw_value in equipment_map:
                return equipment_map[raw_value]
            slug = slugify(raw_value)
            return slug

        primary_equipment = [
            eq for eq in (normalise_equipment(value) for value in row["primary_equipment"].split("/")) if eq
        ]
        secondary_equipment = [
            eq for eq in (normalise_equipment(value) for value in row["secondary_equipment"].split("/")) if eq
        ]

        target_group = normalise_value(row.get("target_muscle_group"), muscle_group_map)

        def capture_muscle(field: str) -> List[str]:
            value = (row.get(field) or "").strip()
            if not value:
                return []
            slug = slugify(value)
            if slug:
                muscle_aliases[slug] = value
                return [slug]
            return []

        muscles = {
            "prime": capture_muscle("prime_mover_muscle"),
            "secondary": capture_muscle("secondary_muscle"),
            "tertiary": capture_muscle("tertiary_muscle"),
        }

        entry = {
            "id": ex_id,
            "name": name,
            "template": template_slug,
            "level": level,
            "body_region": body_region,
            "force_type": force_type,
            "mechanics": mechanics,
            "laterality": laterality,
            "classification": classification,
            "posture": posture,
            "combination_type": combination,
            "load_position": load_position,
            "grip": grip,
            "limb_usage": {
                "arms": {"mode": arms_mode, "cadence": arms_cadence},
                "legs": {"cadence": legs_cadence, "foot_elevation": foot_elevation},
            },
            "movement_patterns": movement_patterns,
            "planes_of_motion": planes,
            "target_muscle_group": target_group,
            "muscles": muscles,
            "equipment": {
                "primary": primary_equipment,
                "secondary": secondary_equipment,
                "primary_count": int(row.get("_primary_items") or 0),
                "secondary_count": int(row.get("_secondary_items") or 0),
            },
            "media": {
                "short_demo": (row.get("short_youtube_demonstration") or "").strip() or None,
                "long_demo": (row.get("in_depth_youtube_explanation") or "").strip() or None,
            },
        }

        bucket = body_region or "full_body"
        region_buckets[bucket].append(entry)

    template_payload = []
    for data in sorted(templates.values(), key=lambda item: item["id"]):
        template_payload.append(
            {
                "id": data["id"],
                "name": data["aliases"] and sorted(data["aliases"])[0] or data["id"],
                "aliases": sorted(data["aliases"]),
                "variants": sorted(data["variants"]),
            }
        )

    write_yaml(CONFIG_ROOT / index["exercises"]["templates"], {"templates": template_payload})

    for region, entries in region_buckets.items():
        path = CONFIG_ROOT / f"exercises/{region}.yaml"
        entries.sort(key=lambda item: item["name"])
        write_yaml(path, {"exercises": entries})

    alias_entries = []
    for alias, display in sorted(muscle_aliases.items()):
        alias_lower = alias.lower()
        candidate_ids = CUSTOM_ALIAS_TARGETS.get(alias_lower, [alias_lower])
        resolved_targets = []
        for candidate in candidate_ids:
            if candidate in muscle_ids:
                resolved_targets.append({"id": candidate, "label": "Muscle"})
            elif candidate in muscle_head_ids:
                resolved_targets.append({"id": candidate, "label": "MuscleHead"})
            else:
                raise SystemExit(f"Alias '{alias}' references unknown anatomy id '{candidate}'.")
        alias_entries.append(
            {"alias": alias_lower, "name": display, "targets": resolved_targets}
        )

    write_yaml(CONFIG_ROOT / "anatomy/muscle_aliases.yaml", {"muscles": alias_entries})

    print(f"Wrote templates and {len(region_buckets)} region files to {CONFIG_ROOT / 'exercises'}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build exercise configs from the raw CSV.")
    parser.add_argument("--csv", type=Path, default=Path("data/exercise_data_raw.csv"))
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    rows = read_rows(args.csv, args.limit)
    if not rows:
        raise SystemExit("No rows found in CSV.")
    build_dataset(rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
