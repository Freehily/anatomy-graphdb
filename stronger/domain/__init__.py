"""
Domain-level abstractions that sit above the raw YAML/CSV configs.

The API package (and any downstream consumer) should import dataclasses or
factory helpers from here instead of reaching into the low-level loaders.
"""

from .anatomy import (
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
from .exercises import (
    ExerciseDataset,
    ExerciseVariant,
    ExerciseTemplate,
    EquipmentItem,
    Taxonomy,
    TaxonomyEntry,
    MuscleAlias,
    MuscleAliasTarget,
    build_exercise_dataset,
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
    "ExerciseDataset",
    "ExerciseVariant",
    "ExerciseTemplate",
    "EquipmentItem",
    "Taxonomy",
    "TaxonomyEntry",
    "MuscleAlias",
    "MuscleAliasTarget",
    "build_exercise_dataset",
]
