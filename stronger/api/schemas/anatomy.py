"""Pydantic response models for anatomy endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Type

from pydantic import BaseModel, ConfigDict, Field


class SectionName(str, Enum):
    bones = "bones"
    attachment_points = "attachment_points"
    muscle_heads = "muscle_heads"
    muscles = "muscles"
    nerves = "nerves"
    arteries = "arteries"
    actions = "actions"


class EntityModel(BaseModel):
    id: str
    name: str
    description: str | None = None
    extra: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class BoneModel(EntityModel):
    region: str | None = None
    attachments: List[str] = Field(default_factory=list)


class AttachmentPointModel(EntityModel):
    bone: str | None = None


class MuscleHeadModel(EntityModel):
    origin: List[str] = Field(default_factory=list)
    innervation: List[str] = Field(default_factory=list)
    arteries: List[str] = Field(default_factory=list)


class MuscleModel(EntityModel):
    group: str | None = None
    order: str | None = None
    heads: List[str] = Field(default_factory=list)
    insertion: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    antagonists: List[str] = Field(default_factory=list)


class NerveModel(EntityModel):
    derivations: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    pathway: str | None = None
    clinical_significance: str | None = None
    innervates: List[str] = Field(default_factory=list)


class ArteryModel(EntityModel):
    branches_from: str | None = None
    supplies: List[str] = Field(default_factory=list)


class ActionModel(EntityModel):
    joint: str | None = None
    action_type: str | None = None
    primary_movers: List[str] = Field(default_factory=list)


class AnatomyModelResponse(BaseModel):
    region: str
    bones: List[BoneModel] = Field(default_factory=list)
    attachment_points: List[AttachmentPointModel] = Field(default_factory=list)
    muscle_heads: List[MuscleHeadModel] = Field(default_factory=list)
    muscles: List[MuscleModel] = Field(default_factory=list)
    nerves: List[NerveModel] = Field(default_factory=list)
    arteries: List[ArteryModel] = Field(default_factory=list)
    actions: List[ActionModel] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RegionsResponse(BaseModel):
    regions: List[str]


class SectionResponse(BaseModel):
    region: str
    section: SectionName
    items: List[EntityModel]


SECTION_MODEL_MAP: Dict[SectionName, Type[EntityModel]] = {
    SectionName.bones: BoneModel,
    SectionName.attachment_points: AttachmentPointModel,
    SectionName.muscle_heads: MuscleHeadModel,
    SectionName.muscles: MuscleModel,
    SectionName.nerves: NerveModel,
    SectionName.arteries: ArteryModel,
    SectionName.actions: ActionModel,
}
