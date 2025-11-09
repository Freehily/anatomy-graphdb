"""Exercise endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from stronger.api.dependencies import get_exercise_service
from stronger.api.schemas.exercises import (
    EquipmentItemModel,
    EquipmentResponse,
    EquipmentSelectionResponse,
    ExerciseTemplateModel,
    ExerciseVariantListResponse,
    ExerciseVariantModel,
    MuscleAliasModel,
    MuscleAliasResponse,
    MuscleGroupListResponse,
    MuscleGroupModel,
    MuscleListResponse,
    TaxonomyListResponse,
    TaxonomyModel,
    TemplateListResponse,
)
from stronger.api.services.exercises import ExerciseService

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/taxonomies", response_model=TaxonomyListResponse)
def list_taxonomies(service: ExerciseService = Depends(get_exercise_service)) -> TaxonomyListResponse:
    return TaxonomyListResponse(taxonomies=sorted(service.list_taxonomy_keys()))


@router.get("/taxonomies/{key}", response_model=TaxonomyModel)
def read_taxonomy(key: str, service: ExerciseService = Depends(get_exercise_service)) -> TaxonomyModel:
    try:
        taxonomy = service.get_taxonomy(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TaxonomyModel.model_validate(taxonomy)


@router.get("/templates", response_model=TemplateListResponse)
def list_templates(service: ExerciseService = Depends(get_exercise_service)) -> TemplateListResponse:
    templates = [
        ExerciseTemplateModel.model_validate(template) for template in service.list_templates()
    ]
    return TemplateListResponse(templates=templates)


@router.get("/muscle-groups", response_model=MuscleGroupListResponse)
def list_muscle_groups(service: ExerciseService = Depends(get_exercise_service)) -> MuscleGroupListResponse:
    groups = [MuscleGroupModel.model_validate(group) for group in service.list_muscle_groups()]
    return MuscleGroupListResponse(groups=groups)


@router.get("/muscle-groups/{group_id}/muscles", response_model=MuscleListResponse)
def list_muscles_for_group(group_id: str, service: ExerciseService = Depends(get_exercise_service)) -> MuscleListResponse:
    try:
        muscles = [MuscleAliasModel.model_validate(alias) for alias in service.muscles_for_group(group_id)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    group = service.get_muscle_group(group_id)
    return MuscleListResponse(group_id=group.id, muscles=muscles)


@router.get("/muscle-groups/{group_id}/variants", response_model=ExerciseVariantListResponse)
def list_variants_for_group(
    group_id: str,
    service: ExerciseService = Depends(get_exercise_service),
) -> ExerciseVariantListResponse:
    try:
        variants = service.variants_for_muscle_group(group_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = [ExerciseVariantModel.model_validate(variant) for variant in variants]
    return ExerciseVariantListResponse(items=payload, count=len(payload))


@router.get("/muscles/{alias}/variants", response_model=ExerciseVariantListResponse)
def list_variants_for_muscle(alias: str, service: ExerciseService = Depends(get_exercise_service)) -> ExerciseVariantListResponse:
    try:
        variants = service.variants_for_muscle(alias)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = [ExerciseVariantModel.model_validate(variant) for variant in variants]
    return ExerciseVariantListResponse(items=payload, count=len(payload))


@router.get("/variants", response_model=ExerciseVariantListResponse)
def list_variants(
    body_region: str | None = Query(
        None,
        description="Filter exercises by `body_region` (upper_body, lower_body, core, etc.).",
    ),
    service: ExerciseService = Depends(get_exercise_service),
) -> ExerciseVariantListResponse:
    variants = [
        ExerciseVariantModel.model_validate(variant)
        for variant in service.list_variants(body_region=body_region)
    ]
    return ExerciseVariantListResponse(items=variants, count=len(variants))


@router.get("/variants/{exercise_id}", response_model=ExerciseVariantModel)
def read_variant(exercise_id: str, service: ExerciseService = Depends(get_exercise_service)) -> ExerciseVariantModel:
    try:
        variant = service.get_variant(exercise_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExerciseVariantModel.model_validate(variant)


@router.get("/variants/{exercise_id}/equipment", response_model=EquipmentSelectionResponse)
def read_variant_equipment(
    exercise_id: str,
    service: ExerciseService = Depends(get_exercise_service),
) -> EquipmentSelectionResponse:
    try:
        equipment = service.equipment_for_variant(exercise_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EquipmentSelectionResponse(
        exercise_id=exercise_id,
        equipment=equipment,
    )


@router.get("/equipment", response_model=EquipmentResponse)
def list_equipment(service: ExerciseService = Depends(get_exercise_service)) -> EquipmentResponse:
    equipment = [
        EquipmentItemModel.model_validate(item)
        for item in service.list_equipment()
    ]
    return EquipmentResponse(equipment=equipment)


@router.get("/equipment/{equipment_id}/variants", response_model=ExerciseVariantListResponse)
def list_variants_for_equipment(
    equipment_id: str,
    service: ExerciseService = Depends(get_exercise_service),
) -> ExerciseVariantListResponse:
    try:
        variants = service.variants_for_equipment(equipment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = [ExerciseVariantModel.model_validate(variant) for variant in variants]
    return ExerciseVariantListResponse(items=payload, count=len(payload))


@router.get("/muscle-aliases", response_model=MuscleAliasResponse)
def list_muscle_aliases(service: ExerciseService = Depends(get_exercise_service)) -> MuscleAliasResponse:
    aliases = [
        MuscleAliasModel.model_validate(alias)
        for alias in service.list_muscle_aliases()
    ]
    return MuscleAliasResponse(aliases=aliases)
