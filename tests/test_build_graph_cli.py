import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "stronger" / "databases" / "anatomy" / "scripts" / "build_graph.py"


def run_build(args: list[str]) -> None:
    cmd = [sys.executable, str(SCRIPT), *args]
    subprocess.run(cmd, cwd=ROOT, check=True)


def test_build_graph_anatomy_only(tmp_path):
    output_dir = tmp_path / "anatomy_only"
    run_build(
        [
            "--region",
            "all",
            "--no-exercises",
            "--validate",
            "--output",
            str(output_dir),
        ],
    )


def test_build_graph_full(tmp_path):
    output_dir = tmp_path / "full_graph"
    run_build(
        [
            "--region",
            "all",
            "--validate",
            "--output",
            str(output_dir),
        ],
    )
