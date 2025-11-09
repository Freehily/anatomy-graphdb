"""Pydantic models for exercise endpoints."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class TaxonomyEntryModel(BaseModel):
    id: str
    name: str
    description: str | None = None
    aliases: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaxonomyModel(BaseModel):
    key: str
    entries: List[TaxonomyEntryModel] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaxonomyListResponse(BaseModel):
    taxonomies: List[str]


class MuscleGroupModel(BaseModel):
    id: str
    name: str
    description: str | None = None
    aliases: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MuscleGroupListResponse(BaseModel):
    groups: List[MuscleGroupModel]


class EquipmentItemModel(BaseModel):
    id: str
    name: str
    description: str | None = None
    parent_id: str | None = None
    aliases: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EquipmentResponse(BaseModel):
    equipment: List[EquipmentItemModel]


class ExerciseTemplateModel(BaseModel):
    id: str
    name: str
    description: str | None = None
    aliases: List[str] = Field(default_factory=list)
    variants: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    templates: List[ExerciseTemplateModel]


class LimbUsageModel(BaseModel):
    arms: Dict[str, Any] = Field(default_factory=dict)
    legs: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class MuscleRolesModel(BaseModel):
    prime: List[str] = Field(default_factory=list)
    secondary: List[str] = Field(default_factory=list)
    tertiary: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EquipmentSelectionModel(BaseModel):
    primary: List[str] = Field(default_factory=list)
    secondary: List[str] = Field(default_factory=list)
    primary_count: int | None = None
    secondary_count: int | None = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentSelectionResponse(BaseModel):
    exercise_id: str
    equipment: EquipmentSelectionModel


class MediaLinksModel(BaseModel):
    short_demo: str | None = None
    long_demo: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExerciseVariantModel(BaseModel):
    id: str
    name: str
    description: str | None = None
    template: str
    body_region: str
    level: str | None = None
    force_type: str | None = None
    mechanics: str | None = None
    laterality: str | None = None
    classification: str | None = None
    posture: str | None = None
    combination_type: str | None = None
    load_position: str | None = None
    grip: str | None = None
    limb_usage: LimbUsageModel = Field(default_factory=LimbUsageModel)
    movement_patterns: List[str] = Field(default_factory=list)
    planes_of_motion: List[str] = Field(default_factory=list)
    target_muscle_group: str | None = None
    muscles: MuscleRolesModel = Field(default_factory=MuscleRolesModel)
    equipment: EquipmentSelectionModel = Field(default_factory=EquipmentSelectionModel)
    media: MediaLinksModel = Field(default_factory=MediaLinksModel)
    extra: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ExerciseVariantListResponse(BaseModel):
    items: List[ExerciseVariantModel]
    count: int


class MuscleAliasTargetModel(BaseModel):
    id: str
    label: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MuscleAliasModel(BaseModel):
    alias: str
    name: str | None = None
    targets: List[MuscleAliasTargetModel] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MuscleAliasResponse(BaseModel):
    aliases: List[MuscleAliasModel]


class MuscleListResponse(BaseModel):
    group_id: str
    muscles: List[MuscleAliasModel]
