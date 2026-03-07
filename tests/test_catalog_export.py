from __future__ import annotations

import json

from anatomy_graphdb.cli.anatomy import main
from anatomy_graphdb.exports import export_catalog


def test_export_catalog_contains_muscles_and_groups() -> None:
    catalog = export_catalog()
    assert catalog["version"] == 1
    assert catalog["muscle_groups"]
    assert catalog["muscles"]
    assert "overlay_assets" in catalog
    assert "muscle_slug_aliases" in catalog
    assert catalog["muscle_slug_aliases"]["anterior_deltoid"] == "deltoid"
    first = catalog["muscles"][0]
    assert "slug" in first
    assert "group_slug" in first


def test_cli_export_catalog_writes_json(tmp_path) -> None:
    output = tmp_path / "catalog.json"
    exit_code = main(["--export-catalog", "--region", "chest", "--catalog-output", str(output)])
    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["regions"] == ["chest"]
