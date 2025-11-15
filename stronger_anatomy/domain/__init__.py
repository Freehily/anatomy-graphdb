"""
Domain-level abstractions that sit above the raw YAML configs.

Downstream consumers should import dataclasses or factory helpers from here
instead of reaching into the low-level loaders.
"""

from .models import (
    AnatomyModel,
    AttachmentPoint,
    Bone,
    Muscle,
    MuscleHead,
    Nerve,
    Artery,
    Action,
    build_anatomy_model,
)
__all__ = [
    "Action",
    "AnatomyModel",
    "Artery",
    "AttachmentPoint",
    "Bone",
    "Muscle",
    "MuscleHead",
    "Nerve",
    "build_anatomy_model",
]
