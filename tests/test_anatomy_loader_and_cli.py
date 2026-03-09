from anatomy_graphdb.cli.anatomy import main
from anatomy_graphdb.cli.anatomy import validate_region
from anatomy_graphdb.databases.anatomy.loader import AnatomyLoader, AnatomyRegion, SectionData


def test_loader_discovers_nested_regions() -> None:
    loader = AnatomyLoader()
    regions = loader.available_regions()
    assert "chest" in regions
    assert "quads" in regions


def test_loader_can_load_nested_region() -> None:
    loader = AnatomyLoader()
    region = loader.load_region("chest")
    assert region.region == "chest"
    assert region.require("muscles").items
    assert region.require("bones").items


def test_loader_includes_shared_data_for_all_region_merge() -> None:
    loader = AnatomyLoader()
    region = loader.load_regions(loader.available_regions())
    artery_ids = {item["id"] for item in region.require("arteries").items}
    assert "abdominal_aorta" in artery_ids


def test_loader_merges_duplicate_ids_across_regions() -> None:
    loader = AnatomyLoader()
    region = loader.load_regions(["biceps", "shoulders"])

    nerves_by_id = {item["id"]: item for item in region.require("nerves").items}
    axillary_targets = set(nerves_by_id["axillary"]["innervates"])
    assert "deltoid_middle" in axillary_targets
    assert "teres_minor" in axillary_targets


def test_cli_list_regions(capsys) -> None:
    exit_code = main(["--list-regions"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "chest" in captured.out


def test_cli_validate_only_passes_for_chest(capsys) -> None:
    exit_code = main(["--region", "chest", "--validate-only"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Validation passed." in captured.out


def test_validation_fails_for_orphan_muscle_head() -> None:
    region = AnatomyRegion(
        region="test",
        sections={
            "attachment_points": SectionData(name="attachment_points", items=[{"id": "attach_1", "bone": "bone_1"}]),
            "bones": SectionData(name="bones", items=[{"id": "bone_1", "attachments": ["attach_1"]}]),
            "muscles": SectionData(name="muscles", items=[{"id": "muscle_1", "heads": [], "insertion": ["attach_1"]}]),
            "muscle_heads": SectionData(
                name="muscle_heads",
                items=[
                    {
                        "id": "muscle_1_head",
                        "origin": ["attach_1"],
                        "innervation": ["nerve_1"],
                        "arteries": ["artery_1"],
                    }
                ],
            ),
            "nerves": SectionData(name="nerves", items=[{"id": "nerve_1", "innervates": ["muscle_1_head"]}]),
            "arteries": SectionData(name="arteries", items=[{"id": "artery_1", "supplies": ["muscle_1_head"]}]),
            "actions": SectionData(name="actions", items=[{"id": "action_1", "primary_movers": ["muscle_1"]}]),
        },
    )

    errors = validate_region(region)
    assert any("head 'muscle_1_head' is not linked from expected muscle(s): muscle_1" in error for error in errors)


def test_load_muscle_catalog_returns_list() -> None:
    loader = AnatomyLoader()
    catalog = loader.load_muscle_catalog()
    assert isinstance(catalog, list)
    assert len(catalog) > 100
    slugs = {m["slug"] for m in catalog}
    assert "pectoralis_major" in slugs
    assert "adductor_longus" in slugs


def test_load_muscle_catalog_overlay_fields() -> None:
    from pathlib import Path
    loader = AnatomyLoader()
    catalog = loader.load_muscle_catalog()
    with_overlays = [m for m in catalog if m.get("overlays")]
    assert len(with_overlays) >= 40

    project_root = Path(__file__).resolve().parents[1]
    for muscle in with_overlays:
        for overlay in muscle["overlays"]:
            assert overlay["view"] in ("front", "rear")
            assert "path" in overlay
            svg_path = project_root / overlay["path"]
            assert svg_path.exists(), f"Missing SVG: {overlay['path']} (muscle: {muscle['slug']})"


def test_load_muscle_catalog_multi_overlay() -> None:
    loader = AnatomyLoader()
    catalog = loader.load_muscle_catalog()
    trapezius = next(m for m in catalog if m["slug"] == "trapezius")
    assert len(trapezius["overlays"]) == 3
    views = {o["view"] for o in trapezius["overlays"]}
    assert "front" in views and "rear" in views
