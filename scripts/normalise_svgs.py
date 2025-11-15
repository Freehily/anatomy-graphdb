"""
normalise legacy SVG muscle assets so their filenames line up with anatomy IDs.

Usage:
    poetry run python scripts/normalise_svgs.py

The script copies every SVG under `svgs/svg_{front,rear}_muscles/` into
`svgs/muscles/<muscle_id>/<view>.svg` (optionally appending `_<variant>` when a
single asset covers a specific subdivision). A manifest (`svgs/manifest.json`)
is written so the API/frontend can discover which orientation(s) exist for each
muscle without guessing filenames.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "svgs"
OUTPUT_DIR = LEGACY_DIR / "muscles"
MANIFEST_PATH = LEGACY_DIR / "manifest.json"


@dataclass(frozen=True)
class Target:
    muscle_id: str
    variant: str | None = None  # e.g., "lower" or "group"


@dataclass(frozen=True)
class SourceEntry:
    filename: str  # relative to LEGACY_DIR
    view: str  # "front" or "rear"
    targets: Sequence[Target]
    notes: str | None = None


FRONT = "front"
REAR = "rear"


SOURCE_MAP: Sequence[SourceEntry] = [
    SourceEntry(
        filename="svg_front_muscles/Adductor Longus and Pectineus.svg",
        view=FRONT,
        targets=[Target("adductor_longus"), Target("pectineus")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Biceps brachii.svg",
        view=FRONT,
        targets=[Target("biceps_brachii")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Brachialis.svg",
        view=FRONT,
        targets=[Target("brachialis")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Brachioradialis.svg",
        view=FRONT,
        targets=[Target("brachioradialis")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Deltoids.svg",
        view=FRONT,
        targets=[Target("deltoid")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Extensor  carpi radialis.svg",
        view=FRONT,
        targets=[Target("extensor_carpi_radialis_longus")],
    ),
    SourceEntry(
        filename="svg_front_muscles/External obliques.svg",
        view=FRONT,
        targets=[Target("external_oblique")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Flexor carpi radialis.svg",
        view=FRONT,
        targets=[Target("flexor_carpi_radialis")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Gastrocnemius (calf).svg",
        view=FRONT,
        targets=[Target("gastrocnemius")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Omohyoid.svg",
        view=FRONT,
        targets=[Target("omohyoid")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Pectoralis Major.svg",
        view=FRONT,
        targets=[Target("pectoralis_major")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Peroneus longus.svg",
        view=FRONT,
        targets=[Target("fibularis_longus")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Rectus Abdominus.svg",
        view=FRONT,
        targets=[Target("rectus_abdominis", variant="full")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Rectus Abdominus_lower.svg",
        view=FRONT,
        targets=[Target("rectus_abdominis", variant="lower")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Rectus femoris.svg",
        view=FRONT,
        targets=[Target("rectus_femoris")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Sartorius.svg",
        view=FRONT,
        targets=[Target("sartorius")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Serratus Anterior.svg",
        view=FRONT,
        targets=[Target("serratus_anterior")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Soleus.svg",
        view=FRONT,
        targets=[Target("soleus")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Sternocleidomastoid.svg",
        view=FRONT,
        targets=[Target("sternocleidomastoid")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Tensor fasciae latae.svg",
        view=FRONT,
        targets=[Target("tensor_fasciae_latae")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Trapezius.svg",
        view=FRONT,
        targets=[Target("trapezius", variant="upper")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Triceps brachii, long head.svg",
        view=FRONT,
        targets=[Target("triceps_brachii_long")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Triceps brachii, medial head.svg",
        view=FRONT,
        targets=[Target("triceps_brachii_medial")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Vastus Lateralis.svg",
        view=FRONT,
        targets=[Target("vastus_lateralis")],
    ),
    SourceEntry(
        filename="svg_front_muscles/Vastus Medialis.svg",
        view=FRONT,
        targets=[Target("vastus_medialis")],
    ),
    # Rear assets
    SourceEntry(
        filename="svg_rear_muscles/Adductor magnus.svg",
        view=REAR,
        targets=[Target("adductor_magnus")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Biceps fermoris.svg",
        view=REAR,
        targets=[Target("biceps_femoris")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Brachioradialis.svg",
        view=REAR,
        targets=[Target("brachioradialis")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Deltoids.svg",
        view=REAR,
        targets=[Target("deltoid")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Extensor carpi radialis.svg",
        view=REAR,
        targets=[Target("extensor_carpi_radialis_longus")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/External obliques.svg",
        view=REAR,
        targets=[Target("external_oblique")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Flexor carpi radialis.svg",
        view=REAR,
        targets=[Target("flexor_carpi_radialis")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Flexor carpi ulnaris.svg",
        view=REAR,
        targets=[Target("flexor_carpi_ulnaris")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Gastrocnemius, lateral head.svg",
        view=REAR,
        targets=[Target("gastrocnemius_lateral_head")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Gastrocnemius, medial head.svg",
        view=REAR,
        targets=[Target("gastrocnemius_medial_head")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Gluteus maximus.svg",
        view=REAR,
        targets=[Target("gluteus_maximus")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Gluteus medius.svg",
        view=REAR,
        targets=[Target("gluteus_medius")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Gracilis.svg",
        view=REAR,
        targets=[Target("gracilis")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Infraspinatus.svg",
        view=REAR,
        targets=[Target("infraspinatus")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Lattisimus dorsi.svg",
        view=REAR,
        targets=[Target("latissimus_dorsi")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Lower Trapezius.svg",
        view=REAR,
        targets=[Target("trapezius", variant="lower")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Peroneus longus.svg",
        view=REAR,
        targets=[Target("fibularis_longus")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Rhomboid major.svg",
        view=REAR,
        targets=[Target("rhomboid_major")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Semitendinosus.svg",
        view=REAR,
        targets=[Target("semitendinosus")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Serratus Anterior.svg",
        view=REAR,
        targets=[Target("serratus_anterior")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Tensor fascie latae.svg",
        view=REAR,
        targets=[Target("tensor_fasciae_latae")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Teres major.svg",
        view=REAR,
        targets=[Target("teres_major")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Thoracolumbar fascia.svg",
        view=REAR,
        targets=[Target("thoracolumbar_fascia_posterior_layer")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Trapezius.svg",
        view=REAR,
        targets=[Target("trapezius")],
    ),
    SourceEntry(
        filename="svg_rear_muscles/Triceps Brachii ( long head, lateral head ).svg",
        view=REAR,
        targets=[Target("triceps_brachii_long"), Target("triceps_brachii_lateral")],
    ),
]

IGNORED_FILES = {
    "svgs/svg_front_muscles/Full_body_muscles.svg",
    "svgs/svg_rear_muscles/Full body with all muscles showing.svg",
}


def _rel_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalise() -> Dict[str, List[Dict[str, str | None]]]:
    manifest: Dict[str, List[Dict[str, str | None]]] = {}
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    for entry in SOURCE_MAP:
        src = LEGACY_DIR / entry.filename
        if not src.exists():
            raise FileNotFoundError(f"Missing source SVG: {entry.filename}")
        for target in entry.targets:
            muscle_dir = OUTPUT_DIR / target.muscle_id
            muscle_dir.mkdir(parents=True, exist_ok=True)
            variant_suffix = f"_{target.variant}" if target.variant else ""
            dest = muscle_dir / f"{entry.view}{variant_suffix}.svg"
            shutil.copyfile(src, dest)
            manifest.setdefault(target.muscle_id, []).append(
                {
                    "view": entry.view,
                    "variant": target.variant,
                    "source": entry.filename,
                    "path": _rel_path(dest),
                }
            )
    return manifest


def ensure_complete(covered: Iterable[str]) -> None:
    normalised = {_rel_path(LEGACY_DIR / path) for path in covered}
    seen = normalised | set(IGNORED_FILES)
    actual = {
        _rel_path(path)
        for folder in ("svg_front_muscles", "svg_rear_muscles")
        for path in (LEGACY_DIR / folder).glob("*.svg")
    }
    missing = sorted(actual - seen)
    if missing:
        raise SystemExit(f"Unmapped SVG files: {missing}")


def main() -> int:
    manifest = normalise()
    ensure_complete(entry.filename for entry in SOURCE_MAP)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} muscle entries to {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
