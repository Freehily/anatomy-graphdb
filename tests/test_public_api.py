import anatomy_graphdb as sa


def test_public_api_exports_are_available() -> None:
    assert hasattr(sa, "__version__")
    assert sa.AnatomyLoader is not None
    assert sa.build_anatomy_model is not None
    assert sa.load_overlay_manifest is not None
    assert sa.export_catalog is not None
