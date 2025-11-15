#!/usr/bin/env python3
"""
Validation utility for the upper limb anatomy configuration.

Checks cross-file referential integrity between bones, attachment points,
muscles, muscle heads, nerves, arteries, and actions. Raises a non-zero exit
code when inconsistencies are detected so the script can be used in CI.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set

import yaml


@dataclass
class ValidationError:
    section: str
    context: str
    missing: Sequence[str]

    def __str__(self) -> str:
        values = ", ".join(self.missing)
        return f"[{self.section}] {self.context}: {values}"


CONFIG_DIR = (
    Path(__file__).resolve().parents[4] / "config" / "anatomy" / "upper_limb"
)
FILES = {
    "attachment_points": "attachment_points.yaml",
    "bones": "bones.yaml",
    "muscle_heads": "muscle_heads.yaml",
    "muscles": "muscles.yaml",
    "nerves": "nerves.yaml",
    "arteries": "arteries.yaml",
    "actions": "actions.yaml",
}


def load_configs() -> Dict[str, dict]:
    configs: Dict[str, dict] = {}
    for key, filename in FILES.items():
        path = CONFIG_DIR / filename
        with path.open() as handle:
            configs[key] = yaml.safe_load(handle)
    return configs


def _collect_ids(items: Iterable[dict], key: str = "id") -> Set[str]:
    return {item[key] for item in items if key in item}


def validate(configs: Dict[str, dict]) -> List[ValidationError]:
    errors: List[ValidationError] = []

    attachment_points = configs["attachment_points"]["attachment_points"]
    bones = configs["bones"]["bones"]
    muscles = configs["muscles"]["muscles"]
    muscle_heads = configs["muscle_heads"]["muscle_heads"]
    nerves = configs["nerves"]["nerves"]
    arteries = configs["arteries"]["arteries"]
    actions = configs["actions"]["actions"]

    attachment_ids = _collect_ids(attachment_points)
    bone_ids = _collect_ids(bones)
    muscle_ids = _collect_ids(muscles)
    muscle_head_ids = _collect_ids(muscle_heads)
    contractile_ids = muscle_ids | muscle_head_ids

    # Attachment points -> bone IDs
    for point in attachment_points:
        bone_id = point.get("bone")
        if bone_id and bone_id not in bone_ids:
            errors.append(
                ValidationError(
                    section="attachment_points",
                    context=f"unknown bone '{bone_id}' for attachment '{point['id']}'",
                    missing=[bone_id],
                )
            )

    # Bones -> attachments
    for bone in bones:
        missing = [
            attachment
            for attachment in bone.get("attachments", [])
            if attachment not in attachment_ids
        ]
        if missing:
            errors.append(
                ValidationError(
                    section="bones",
                    context=f"bone '{bone['id']}' references missing attachment(s)",
                    missing=missing,
                )
            )

    # Muscle heads -> attachment points and nerves/arteries
    for head in muscle_heads:
        missing_origins = [
            origin for origin in head.get("origin", []) if origin not in attachment_ids
        ]
        if missing_origins:
            errors.append(
                ValidationError(
                    section="muscle_heads",
                    context=f"head '{head['id']}' has unknown origin attachment(s)",
                    missing=missing_origins,
                )
            )

    # Muscles -> attachment points, heads, and antagonists
    for muscle in muscles:
        missing_insertions = [
            insertion
            for insertion in muscle.get("insertion", [])
            if insertion not in attachment_ids
        ]
        if missing_insertions:
            errors.append(
                ValidationError(
                    section="muscles",
                    context=f"muscle '{muscle['id']}' has unknown insertion attachment(s)",
                    missing=missing_insertions,
                )
            )

        missing_heads = [
            head_id
            for head_id in muscle.get("heads", [])
            if head_id and head_id not in muscle_head_ids
        ]
        if missing_heads:
            errors.append(
                ValidationError(
                    section="muscles",
                    context=f"muscle '{muscle['id']}' lists undefined head(s)",
                    missing=missing_heads,
                )
            )

        missing_antagonists = [
            antagonist
            for antagonist in muscle.get("antagonists", [])
            if antagonist not in contractile_ids
        ]
        if missing_antagonists:
            errors.append(
                ValidationError(
                    section="muscles",
                    context=f"muscle '{muscle['id']}' lists unknown antagonist(s)",
                    missing=missing_antagonists,
                )
            )

    # Actions -> contractile elements
    for action in actions:
        missing = [
            mover
            for mover in action.get("primary_movers", [])
            if mover not in contractile_ids
        ]
        if missing:
            errors.append(
                ValidationError(
                    section="actions",
                    context=f"action '{action['id']}' references unknown primary mover(s)",
                    missing=missing,
                )
            )

    # Nerves -> contractile elements
    for nerve in nerves:
        missing = [
            target
            for target in nerve.get("innervates", [])
            if target not in contractile_ids
        ]
        if missing:
            errors.append(
                ValidationError(
                    section="nerves",
                    context=f"nerve '{nerve['id']}' references unknown muscle/muscle_head(s)",
                    missing=missing,
                )
            )

    # Arteries -> contractile elements
    for artery in arteries:
        missing = [
            supply
            for supply in artery.get("supplies", [])
            if supply not in contractile_ids
        ]
        if missing:
            errors.append(
                ValidationError(
                    section="arteries",
                    context=f"artery '{artery['id']}' supplies unknown muscle/muscle_head(s)",
                    missing=missing,
                )
            )

    return errors


def main(argv: Sequence[str]) -> int:
    configs = load_configs()
    errors = validate(configs)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Upper limb anatomy configuration is consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
