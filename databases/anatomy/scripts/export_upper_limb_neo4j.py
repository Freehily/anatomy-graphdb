#!/usr/bin/env python3
"""
Legacy-friendly wrapper that exports anatomy regions into Neo4j-compatible CSVs.

The script now delegates to the shared graph loader and artifact builder so that
all tooling uses the same parsing logic.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence

from stronger.databases.anatomy.loader import AnatomyConfigError, AnatomyLoader
from stronger.databases.anatomy.neo4j_artifacts import CsvArtifact, build_all_artifacts


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_artifact(artifact: CsvArtifact, destination: Path) -> None:
    ensure_dir(destination.parent)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=artifact.headers)
        writer.writeheader()
        for row in artifact.rows:
            writer.writerow(row)


def export_region(region_name: str, output_dir: Path) -> None:
    loader = AnatomyLoader()
    region = loader.load_region(region_name)

    artifacts = build_all_artifacts(region)
    for artifact in artifacts:
        target = output_dir / artifact.filename
        write_artifact(artifact, target)

    print(f"Export complete. {len(artifacts)} files written to {output_dir.resolve()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export anatomy regions to Neo4j CSV files (wrapper for the shared build_graph tooling)."
    )
    parser.add_argument(
        "--region",
        "-r",
        default="upper_limb",
        help="Anatomy region to export (expects matching folder under configs/).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Directory for CSV output (default: <repo>/data/neo4j/<region>).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[4]
    target_dir = args.output or (project_root / "data" / "neo4j" / args.region)

    try:
        export_region(args.region, target_dir)
    except AnatomyConfigError as exc:
        parser.error(str(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

