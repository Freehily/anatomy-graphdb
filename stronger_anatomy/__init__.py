"""
Public package API for stronger-anatomy.

Keep this surface stable across minor releases.
"""

from importlib.metadata import PackageNotFoundError, version

from stronger_anatomy.assets import OverlayAssetManifestError, asset_absolute_path, load_overlay_manifest
from stronger_anatomy.databases.anatomy.loader import AnatomyConfigError, AnatomyLoader, AnatomyRegion
from stronger_anatomy.domain import (
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
from stronger_anatomy.exports import export_catalog, write_catalog_json

try:
    __version__ = version("stronger-anatomy")
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
