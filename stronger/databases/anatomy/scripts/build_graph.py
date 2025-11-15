"""
Unified CLI for turning anatomy YAML configs into a Neo4j graph.

Features:
  * loads region data via the shared loader (supports shared entities)
  * optional integrity validation before export/import
  * CSV export compatible with `neo4j-admin database import`
  * direct Bolt ingestion using the official Neo4j Python driver
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from stronger.databases.anatomy.loader import (
    AnatomyConfigError,
    AnatomyLoader,
    AnatomyRegion,
)
from stronger.databases.anatomy.neo4j_artifacts import (
    CsvArtifact,
    NodePayload,
    RelationshipPayload,
    build_all_artifacts,
    build_node_payloads,
    build_relationship_payloads,
)


def load_env_file(path: Path | None = None) -> None:
    """
    Populate os.environ with key/value pairs from a .env-style file if present.
    Existing environment variables always win so callers can override secrets.
    """

    candidate = path or Path(".env")
    if not candidate.exists():
        return

    try:
        lines = candidate.read_text(encoding="utf-8").splitlines()
    except OSError as exc:  # pragma: no cover - file system edge cases
        print(f"Warning: unable to read {candidate}: {exc}", file=sys.stderr)
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] in {"'", '"'} and value[-1] == value[0]:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def list_regions(loader: AnatomyLoader) -> None:
    regions = loader.available_regions()
    if not regions:
        print("No regions discovered.", file=sys.stderr)
        return
    print("Available regions:")
    for region in regions:
        print(f"  - {region}")


def _collect_ids(items: Iterable[dict], key: str = "id") -> set[str]:
    return {item[key] for item in items if key in item}


def validate_region(region: AnatomyRegion) -> List[str]:
    """
    Re-implements the validation logic used by the bespoke scripts so it can run
    on any region delivered by the loader.
    """

    errors: List[str] = []

    attachment_points = region.require("attachment_points").items
    bones = region.require("bones").items
    muscles = region.require("muscles").items
    muscle_heads = region.require("muscle_heads").items
    nerves = region.require("nerves").items
    arteries = region.require("arteries").items
    actions = region.require("actions").items

    attachment_ids = _collect_ids(attachment_points)
    bone_ids = _collect_ids(bones)
    muscle_ids = _collect_ids(muscles)
    muscle_head_ids = _collect_ids(muscle_heads)
    nerve_ids = _collect_ids(nerves)
    artery_ids = _collect_ids(arteries)

    contractile_ids = muscle_ids | muscle_head_ids

    # Attachment points -> bone IDs
    for point in attachment_points:
        bone_id = point.get("bone")
        if bone_id and bone_id not in bone_ids:
            errors.append(
                f"[attachment_points] attachment '{point['id']}' references unknown bone '{bone_id}'"
            )

    # Bones -> attachments
    for bone in bones:
        missing = [
            attachment
            for attachment in bone.get("attachments", [])
            if attachment not in attachment_ids
        ]
        if missing:
            missing_list = ", ".join(missing)
            errors.append(f"[bones] bone '{bone['id']}' references missing attachment(s): {missing_list}")

    # Muscle heads -> origin attachments and innervation/arteries
    for head in muscle_heads:
        missing_origins = [
            origin for origin in head.get("origin", []) if origin not in attachment_ids
        ]
        if missing_origins:
            missing_list = ", ".join(missing_origins)
            errors.append(
                f"[muscle_heads] head '{head['id']}' has unknown origin attachment(s): {missing_list}"
            )

        missing_nerves = [
            nerve for nerve in head.get("innervation", []) if nerve not in nerve_ids
        ]
        if missing_nerves:
            missing_list = ", ".join(missing_nerves)
            errors.append(
                f"[muscle_heads] head '{head['id']}' references missing nerve(s): {missing_list}"
            )

        missing_arteries = [
            artery for artery in head.get("arteries", []) if artery not in artery_ids
        ]
        if missing_arteries:
            missing_list = ", ".join(missing_arteries)
            errors.append(
                f"[muscle_heads] head '{head['id']}' references missing artery(ies): {missing_list}"
            )

    # Muscles -> insertions, heads, antagonists
    for muscle in muscles:
        missing_insertions = [
            insertion
            for insertion in muscle.get("insertion", [])
            if insertion not in attachment_ids
        ]
        if missing_insertions:
            missing_list = ", ".join(missing_insertions)
            errors.append(
                f"[muscles] muscle '{muscle['id']}' has unknown insertion attachment(s): {missing_list}"
            )

        missing_heads = [
            head_id
            for head_id in muscle.get("heads", [])
            if head_id not in muscle_head_ids
        ]
        if missing_heads:
            missing_list = ", ".join(missing_heads)
            errors.append(f"[muscles] muscle '{muscle['id']}' lists undefined head(s): {missing_list}")

        missing_antagonists = [
            antagonist
            for antagonist in muscle.get("antagonists", [])
            if antagonist not in contractile_ids
        ]
        if missing_antagonists:
            missing_list = ", ".join(missing_antagonists)
            errors.append(
                f"[muscles] muscle '{muscle['id']}' lists unknown antagonist(s): {missing_list}"
            )

    # Actions -> contractile elements
    for action in actions:
        missing = [
            mover for mover in action.get("primary_movers", []) if mover not in contractile_ids
        ]
        if missing:
            missing_list = ", ".join(missing)
            errors.append(
                f"[actions] action '{action['id']}' references unknown primary mover(s): {missing_list}"
            )

    # Nerves -> contractile targets
    for nerve in nerves:
        missing = [
            target for target in nerve.get("innervates", []) if target not in contractile_ids
        ]
        if missing:
            missing_list = ", ".join(missing)
            errors.append(
                f"[nerves] nerve '{nerve['id']}' references unknown muscle/muscle_head target(s): {missing_list}"
            )

    # Arteries -> contractile targets & branches
    for artery in arteries:
        ancestor = artery.get("branches_from")
        if ancestor and ancestor not in artery_ids:
            errors.append(
                f"[arteries] artery '{artery['id']}' branches from unknown artery '{ancestor}'"
            )

        missing = [
            target for target in artery.get("supplies", []) if target not in contractile_ids
        ]
        if missing:
            missing_list = ", ".join(missing)
            errors.append(
                f"[arteries] artery '{artery['id']}' supplies unknown muscle/muscle_head target(s): {missing_list}"
            )

    return errors


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_artifact(artifact: CsvArtifact, base_dir: Path) -> Path:
    target = base_dir / artifact.filename
    ensure_dir(target.parent)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=artifact.headers)
        writer.writeheader()
        for row in artifact.rows:
            writer.writerow(row)
    return target


def export_csv(region: AnatomyRegion, output_dir: Path) -> None:
    artifacts = build_all_artifacts(region)
    for artifact in artifacts:
        write_artifact(artifact, output_dir)
    print(f"CSV export complete. {len(artifacts)} files written to {output_dir.resolve()}")


def _chunk(sequence: Sequence, size: int = 500) -> Iterable[Sequence]:
    for idx in range(0, len(sequence), size):
        yield sequence[idx : idx + size]


def ingest_via_neo4j(
    region: AnatomyRegion,
    args: argparse.Namespace,
) -> None:
    try:
        from neo4j import GraphDatabase
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise SystemExit(
            "The neo4j Python driver is required for bolt ingestion. Install with `pip install neo4j`."
        ) from exc

    uri = args.neo4j_uri
    auth = None
    if args.neo4j_user or args.neo4j_password:
        auth = (args.neo4j_user or "", args.neo4j_password or "")

    driver = GraphDatabase.driver(uri, auth=auth)

    node_payloads = build_node_payloads(region)
    relationship_payloads = build_relationship_payloads(region)

    def _sanitize_props(props: Dict[str, object]) -> Dict[str, object]:
        return {key: value for key, value in props.items() if value not in (None, "", [])}

    def _merge_nodes(tx, label: str, batch: Sequence[NodePayload]) -> None:
        tx.run(
            f"""
            UNWIND $batch AS row
            MERGE (node:{label} {{id: row.id}})
            SET node += row.props
            """,
            batch=[{"id": item.id, "props": _sanitize_props(item.properties)} for item in batch],
        )

    def _merge_relationships(tx, rel_type: str, start_label: str, end_label: str, batch: Sequence[RelationshipPayload]) -> None:
        tx.run(
            f"""
            UNWIND $batch AS row
            MATCH (start:{start_label} {{id: row.start_id}})
            MATCH (end:{end_label} {{id: row.end_id}})
            MERGE (start)-[rel:{rel_type}]->(end)
            SET rel += row.props
            """,
            batch=[
                {
                    "start_id": item.start_id,
                    "end_id": item.end_id,
                    "props": _sanitize_props(item.properties),
                }
                for item in batch
            ],
        )

    with driver.session(database=args.neo4j_database) as session:
        if args.wipe_database:
            session.run("MATCH (n) DETACH DELETE n")
            print("Existing graph deleted (MATCH (n) DETACH DELETE n).")

        # Merge nodes grouped by label
        grouped_nodes: Dict[str, List[NodePayload]] = defaultdict(list)
        for node in node_payloads:
            grouped_nodes[node.label].append(node)

        for label, payloads in grouped_nodes.items():
            if not payloads:
                continue
            for batch in _chunk(payloads, size=args.batch_size):
                session.execute_write(_merge_nodes, label, list(batch))
            print(f"Upserted {len(payloads)} {label} node(s).")

        # Merge relationships grouped by type, start/end label tuple
        grouped_rel: Dict[tuple[str, str, str], List[RelationshipPayload]] = defaultdict(list)
        for rel in relationship_payloads:
            grouped_rel[(rel.type, rel.start_label, rel.end_label)].append(rel)

        for (rel_type, start_label, end_label), payloads in grouped_rel.items():
            if not payloads:
                continue
            for batch in _chunk(payloads, size=args.batch_size):
                session.execute_write(_merge_relationships, rel_type, start_label, end_label, list(batch))
            print(f"Upserted {len(payloads)} {rel_type} relationship(s) ({start_label}->{end_label}).")

    driver.close()
    print(f"Bolt ingestion complete against {uri}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load anatomy YAML configs and export to Neo4j artifacts or a live database."
    )
    parser.add_argument(
        "--region",
        "-r",
        default="upper_limb",
        help="Region to load (folder under config/anatomy/<region>).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("data/neo4j"),
        help="Base directory for CSV exports (ignored when using bolt ingestion).",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["csv", "bolt"],
        default="csv",
        help="Export mode: csv writes Neo4j import files, bolt pushes directly to a Neo4j server.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run referential integrity validation before executing the requested action.",
    )
    parser.add_argument(
        "--list-regions",
        action="store_true",
        help="List discoverable regions and exit.",
    )
    parser.add_argument(
        "--neo4j-uri",
        default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j Bolt URI (bolt mode only).",
    )
    parser.add_argument(
        "--neo4j-user",
        default=os.environ.get("NEO4J_USER"),
        help="Neo4j username (bolt mode).",
    )
    parser.add_argument(
        "--neo4j-password",
        default=os.environ.get("NEO4J_PASSWORD"),
        help="Neo4j password (bolt mode).",
    )
    parser.add_argument(
        "--neo4j-database",
        default=os.environ.get("NEO4J_DB"),
        help="Neo4j database name (defaults to the server default).",
    )
    parser.add_argument(
        "--wipe-database",
        action="store_true",
        help="Before ingestion, run `MATCH (n) DETACH DELETE n` to clear the database.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of records per write transaction when ingesting via bolt.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_env_file()
    parser = build_parser()
    args = parser.parse_args(argv)

    loader = AnatomyLoader()

    if args.list_regions:
        list_regions(loader)
        return 0

    region_arg = args.region.strip()
    if region_arg.lower() == "all":
        target_regions = loader.available_regions()
    else:
        target_regions = [value.strip() for value in region_arg.split(",") if value.strip()]

    if not target_regions:
        parser.error("No region specified.")

    try:
        if len(target_regions) == 1:
            region = loader.load_region(target_regions[0])
        else:
            region = loader.load_regions(target_regions)
    except AnatomyConfigError as exc:
        parser.error(str(exc))

    muscle_labels: Dict[str, str] = {}
    if "muscles" in region.sections:
        for item in region.require("muscles").items:
            muscle_labels[item["id"]] = "Muscle"
    if "muscle_heads" in region.sections:
        for item in region.require("muscle_heads").items:
            muscle_labels[item["id"]] = "MuscleHead"

    if args.validate:
        failures = validate_region(region)
        if failures:
            print("Validation failed:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("Validation passed.")

    if args.mode == "csv":
        if args.output.is_dir():
            output_dir = args.output / region.region
        else:
            output_dir = args.output
        export_csv(region, output_dir)
    else:
        ingest_via_neo4j(region, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
