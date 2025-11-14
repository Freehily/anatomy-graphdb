"""HTTP routes for anatomy data."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from stronger.api.dependencies import get_anatomy_service
from stronger.api.schemas.anatomy import (
    AnatomyModelResponse,
    SECTION_MODEL_MAP,
    SectionName,
    SectionResponse,
    RegionsResponse,
)
from stronger.api.services.anatomy import AnatomyService, AnatomyServiceError

router = APIRouter(prefix="/anatomy", tags=["anatomy"])


@router.get("/regions", response_model=RegionsResponse)
def list_regions(service: AnatomyService = Depends(get_anatomy_service)) -> RegionsResponse:
    return RegionsResponse(regions=sorted(service.list_regions()))


@router.get("/regions/{region}", response_model=AnatomyModelResponse)
def read_region(
    region: str,
    include_shared: bool = Query(
        True,
        description="Include definitions from the shared directory when building the region.",
    ),
    service: AnatomyService = Depends(get_anatomy_service),
) -> AnatomyModelResponse:
    try:
        model = service.get_region(region, include_shared=include_shared)
    except AnatomyServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnatomyModelResponse.model_validate(model)


@router.get("/regions/{region}/sections/{section}", response_model=SectionResponse)
def read_section(
    region: str,
    section: SectionName,
    include_shared: bool = Query(
        True,
        description="Include definitions from the shared directory when building the region.",
    ),
    service: AnatomyService = Depends(get_anatomy_service),
) -> SectionResponse:
    try:
        resolved_region, items = service.get_section(
            region,
            section.value,
            include_shared=include_shared,
        )
    except AnatomyServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    model_cls = SECTION_MODEL_MAP[section]
    payload = [model_cls.model_validate(entity) for entity in items]
    return SectionResponse(region=resolved_region, section=section, items=payload)
