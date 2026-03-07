"""
Public package API for anatomy-graphdb.

Keep this surface stable across minor releases.
"""

from importlib.metadata import PackageNotFoundError, version

from anatomy_graphdb.assets import OverlayAssetManifestError, asset_absolute_path, load_overlay_manifest
from anatomy_graphdb.databases.anatomy.loader import AnatomyConfigError, AnatomyLoader, AnatomyRegion
from anatomy_graphdb.domain import (
    Action,
    AnatomyModel,
    Artery,
    AttachmentPoint,
    Bone,
    Muscle,
    MuscleHead,
    Nerve,
    build_anatomy_model,
)
from anatomy_graphdb.exports import export_catalog, write_catalog_json

try:
    __version__ = version("anatomy-graphdb")
except PackageNotFoundError:
    __version__ = "0.0.0+local"

__all__ = [
    "__version__",
    "Action",
    "AnatomyConfigError",
    "AnatomyLoader",
    "AnatomyModel",
    "AnatomyRegion",
    "Artery",
    "AttachmentPoint",
    "Bone",
    "Muscle",
    "MuscleHead",
    "Nerve",
    "OverlayAssetManifestError",
    "asset_absolute_path",
    "build_anatomy_model",
    "export_catalog",
    "load_overlay_manifest",
    "write_catalog_json",
]
