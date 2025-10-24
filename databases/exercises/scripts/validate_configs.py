#!/usr/bin/env python3
"""Quick validation entrypoint for the exercise configs."""

from __future__ import annotations

import argparse
from pathlib import Path

from stronger.databases.exercises.loader import ExerciseLoader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate exercise YAML configs.")
    parser.add_argument("--root", type=Path, default=None, help="Override config root (defaults to package path).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    loader = ExerciseLoader(root=args.root)
    loader.load()
    errors = loader.validate()
    if errors:
        print("Validation failed:")
        for error in errors:
            print(" -", error)
        return 1
    print(f"Validation passed for {len(loader.exercise_variants)} exercises.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

