from stronger_anatomy.cli.anatomy import main
from stronger_anatomy.databases.anatomy.loader import AnatomyLoader


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


def test_loader_includes_shared_data_for_nested_region() -> None:
    loader = AnatomyLoader()
    region = loader.load_region("chest")
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
