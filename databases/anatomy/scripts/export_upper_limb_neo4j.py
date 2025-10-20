#!/usr/bin/env python3
"""
Export an anatomy region into CSV files suitable for `neo4j-admin database import`
or `LOAD CSV`.

The script produces separate node and relationship files for bones, attachment
points, muscles, muscle-heads, nerves, arteries, and actions. Each CSV already
includes the `:ID`, `:LABEL`, `:START_ID`, `:END_ID`, and `:TYPE` columns
expected by Neo4j bulk import tooling.

Example usage:
    python export_upper_limb_neo4j.py --region upper_limb
    python export_upper_limb_neo4j.py --region thorax --output ../../../data/neo4j/thorax
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, Sequence

import yaml

REGION_FILES = {
    "attachment_points": "attachment_points.yaml",
    "bones": "bones.yaml",
    "muscle_heads": "muscle_heads.yaml",
    "muscles": "muscles.yaml",
    "nerves": "nerves.yaml",
    "arteries": "arteries.yaml",
    "actions": "actions.yaml",
}


def load_configs(config_dir: Path) -> Dict[str, dict]:
    configs: Dict[str, dict] = {}
    for key, filename in REGION_FILES.items():
        path = config_dir / filename
        with path.open() as handle:
            configs[key] = yaml.safe_load(handle)
    return configs


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, headers: Sequence[str], rows: Iterable[Dict[str, str]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def join_list(values: Sequence[str]) -> str:
    return "|".join(str(v) for v in values) if values else ""


def export_nodes(configs: Dict[str, dict], out_dir: Path) -> Dict[str, set]:
    attachment_points = configs["attachment_points"]["attachment_points"]
    bones = configs["bones"]["bones"]
    muscles = configs["muscles"]["muscles"]
    muscle_heads = configs["muscle_heads"]["muscle_heads"]
    nerves = configs["nerves"]["nerves"]
    arteries = configs["arteries"]["arteries"]
    actions = configs["actions"]["actions"]

    ids = {
        "attachment_points": {item["id"] for item in attachment_points},
        "bones": {item["id"] for item in bones},
        "muscles": {item["id"] for item in muscles},
        "muscle_heads": {item["id"] for item in muscle_heads},
        "nerves": {item["id"] for item in nerves},
        "arteries": {item["id"] for item in arteries},
        "actions": {item["id"] for item in actions},
    }

    write_csv(
        out_dir / "nodes_bones.csv",
        ["boneId:ID(Bone)", "name", "region:STRING"],
        (
            {
                "boneId:ID(Bone)": bone["id"],
                "name": bone.get("name", ""),
                "region:STRING": bone.get("region", ""),
            }
            for bone in bones
        ),
    )

    write_csv(
        out_dir / "nodes_attachment_points.csv",
        ["attachId:ID(AttachmentPoint)", "name", "structure:STRING"],
        (
            {
                "attachId:ID(AttachmentPoint)": ap["id"],
                "name": ap.get("name", ""),
                "structure:STRING": ap.get("bone", ""),
            }
            for ap in attachment_points
        ),
    )

    write_csv(
        out_dir / "nodes_muscles.csv",
        ["muscleId:ID(Muscle)", "name", "group", "order"],
        (
            {
                "muscleId:ID(Muscle)": muscle["id"],
                "name": muscle.get("name", ""),
                "group": muscle.get("group", ""),
                "order": muscle.get("order", ""),
            }
            for muscle in muscles
        ),
    )

    write_csv(
        out_dir / "nodes_muscle_heads.csv",
        ["headId:ID(MuscleHead)", "name"],
        (
            {
                "headId:ID(MuscleHead)": head["id"],
                "name": head.get("name", ""),
            }
            for head in muscle_heads
        ),
    )

    write_csv(
        out_dir / "nodes_nerves.csv",
        ["nerveId:ID(Nerve)", "name", "derivations", "types", "pathway", "clinical"],
        (
            {
                "nerveId:ID(Nerve)": nerve["id"],
                "name": nerve.get("name", ""),
                "derivations": join_list(nerve.get("derivations", [])),
                "types": join_list(nerve.get("type", [])),
                "pathway": nerve.get("pathway", ""),
                "clinical": nerve.get("clinical_significance", ""),
            }
            for nerve in nerves
        ),
    )

    write_csv(
        out_dir / "nodes_arteries.csv",
        ["arteryId:ID(Artery)", "name"],
        (
            {
                "arteryId:ID(Artery)": artery["id"],
                "name": artery.get("name", ""),
            }
            for artery in arteries
        ),
    )

    write_csv(
        out_dir / "nodes_actions.csv",
        ["actionId:ID(Action)", "name", "joint", "movement_type"],
        (
            {
                "actionId:ID(Action)": action["id"],
                "name": action.get("name", ""),
                "joint": action.get("joint", ""),
                "movement_type": action.get("type", ""),
            }
            for action in actions
        ),
    )

    return ids


def export_relationships(configs: Dict[str, dict], ids: Dict[str, set], out_dir: Path) -> None:
    attachment_points = configs["attachment_points"]["attachment_points"]
    bones = configs["bones"]["bones"]
    muscles = configs["muscles"]["muscles"]
    muscle_heads = configs["muscle_heads"]["muscle_heads"]
    nerves = configs["nerves"]["nerves"]
    arteries = configs["arteries"]["arteries"]
    actions = configs["actions"]["actions"]

    attachment_ids = ids["attachment_points"]
    muscle_ids = ids["muscles"]
    muscle_head_ids = ids["muscle_heads"]
    artery_ids = ids["arteries"]

    write_csv(
        out_dir / "rels_bone_attachment.csv",
        [":START_ID(Bone)", ":END_ID(AttachmentPoint)", ":TYPE"],
        (
            {
                ":START_ID(Bone)": bone["id"],
                ":END_ID(AttachmentPoint)": attachment,
                ":TYPE": "HAS_ATTACHMENT",
            }
            for bone in bones
            for attachment in bone.get("attachments", [])
            if attachment in attachment_ids
        ),
    )

    write_csv(
        out_dir / "rels_muscle_head.csv",
        [":START_ID(Muscle)", ":END_ID(MuscleHead)", ":TYPE"],
        (
            {
                ":START_ID(Muscle)": muscle["id"],
                ":END_ID(MuscleHead)": head_id,
                ":TYPE": "HAS_HEAD",
            }
            for muscle in muscles
            for head_id in muscle.get("heads", [])
            if head_id in muscle_head_ids
        ),
    )

    write_csv(
        out_dir / "rels_muscle_insertion.csv",
        [":START_ID(Muscle)", ":END_ID(AttachmentPoint)", ":TYPE"],
        (
            {
                ":START_ID(Muscle)": muscle["id"],
                ":END_ID(AttachmentPoint)": attachment_id,
                ":TYPE": "INSERTS_AT",
            }
            for muscle in muscles
            for attachment_id in muscle.get("insertion", [])
            if attachment_id in attachment_ids
        ),
    )

    write_csv(
        out_dir / "rels_muscle_antagonist.csv",
        [":START_ID(Muscle)", ":END_ID", ":TYPE"],
        (
            {
                ":START_ID(Muscle)": muscle["id"],
                ":END_ID": antagonist_id,
                ":TYPE": "ANTAGONIST",
            }
            for muscle in muscles
            for antagonist_id in muscle.get("antagonists", [])
            if antagonist_id in muscle_ids | muscle_head_ids
        ),
    )

    write_csv(
        out_dir / "rels_head_origin.csv",
        [":START_ID(MuscleHead)", ":END_ID(AttachmentPoint)", ":TYPE"],
        (
            {
                ":START_ID(MuscleHead)": head["id"],
                ":END_ID(AttachmentPoint)": origin_id,
                ":TYPE": "ORIGINATES_AT",
            }
            for head in muscle_heads
            for origin_id in head.get("origin", [])
            if origin_id in attachment_ids
        ),
    )

    write_csv(
        out_dir / "rels_head_innervation.csv",
        [":START_ID(MuscleHead)", ":END_ID(Nerve)", ":TYPE"],
        (
            {
                ":START_ID(MuscleHead)": head["id"],
                ":END_ID(Nerve)": nerve_id,
                ":TYPE": "INNERVATED_BY",
            }
            for head in muscle_heads
            for nerve_id in head.get("innervation", [])
        ),
    )

    write_csv(
        out_dir / "rels_head_artery.csv",
        [":START_ID(MuscleHead)", ":END_ID(Artery)", ":TYPE"],
        (
            {
                ":START_ID(MuscleHead)": head["id"],
                ":END_ID(Artery)": artery_id,
                ":TYPE": "SUPPLIED_BY",
            }
            for head in muscle_heads
            for artery_id in head.get("arteries", [])
        ),
    )

    write_csv(
        out_dir / "rels_nerve_targets.csv",
        [":START_ID(Nerve)", ":END_ID", ":TYPE"],
        (
            {
                ":START_ID(Nerve)": nerve["id"],
                ":END_ID": target_id,
                ":TYPE": "INNERVATES",
            }
            for nerve in nerves
            for target_id in nerve.get("innervates", [])
            if target_id in muscle_ids | muscle_head_ids
        ),
    )

    write_csv(
        out_dir / "rels_artery_supplies.csv",
        [":START_ID(Artery)", ":END_ID", ":TYPE"],
        (
            {
                ":START_ID(Artery)": artery["id"],
                ":END_ID": target_id,
                ":TYPE": "SUPPLIES",
            }
            for artery in arteries
            for target_id in artery.get("supplies", [])
            if target_id in muscle_ids | muscle_head_ids
        ),
    )

    write_csv(
        out_dir / "rels_artery_branches.csv",
        [":START_ID(Artery)", ":END_ID(Artery)", ":TYPE"],
        (
            {
                ":START_ID(Artery)": artery["id"],
                ":END_ID(Artery)": artery.get("branches_from"),
                ":TYPE": "BRANCHES_FROM",
            }
            for artery in arteries
            if artery.get("branches_from") in artery_ids
        ),
    )

    write_csv(
        out_dir / "rels_action_primary.csv",
        [":START_ID(Action)", ":END_ID", ":TYPE"],
        (
            {
                ":START_ID(Action)": action["id"],
                ":END_ID": mover_id,
                ":TYPE": "PRIMARY_MOVER",
            }
            for action in actions
            for mover_id in action.get("primary_movers", [])
            if mover_id in muscle_ids | muscle_head_ids
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export anatomy regions to Neo4j CSVs.")
    parser.add_argument(
        "--region",
        "-r",
        default="upper_limb",
        help="Anatomy region to export (expects matching folder under configs/)",
    )
    project_root = Path(__file__).resolve().parents[4]
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Directory where CSV files will be written (default: <repo>/data/neo4j/<region>)",
    )
    args = parser.parse_args()

    config_dir = Path(__file__).resolve().parents[1] / "configs" / args.region
    if not config_dir.exists():
        parser.error(f"Region '{args.region}' not found at {config_dir}")

    output_dir = args.output or (project_root / "data" / "neo4j" / args.region)
    configs = load_configs(config_dir)
    ids = export_nodes(configs, output_dir)
    export_relationships(configs, ids, output_dir)
    print(f"Export complete. CSV files written to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
