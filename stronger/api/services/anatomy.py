"""Application-layer helpers that expose anatomy data to the API."""

from __future__ import annotations

from typing import Sequence

from stronger.databases.anatomy.loader import AnatomyLoader
from stronger.domain.anatomy import (
    AnatomyModel,
    DomainEntity,
    build_anatomy_model,
)


class AnatomyService:
    """Thin wrapper around the loader that returns typed domain models."""

    def __init__(self, loader: AnatomyLoader | None = None) -> None:
        self._loader = loader or AnatomyLoader()

    def list_regions(self) -> Sequence[str]:
        return self._loader.available_regions()

    def get_region(self, region: str, *, include_shared: bool = True) -> AnatomyModel:
        payload = self._loader.load_region(region, include_shared=include_shared)
        return build_anatomy_model(payload)

    def get_section(
        self,
        region: str,
        section: str,
        *,
        include_shared: bool = True,
    ) -> tuple[str, Sequence[DomainEntity]]:
        model = self.get_region(region, include_shared=include_shared)
        return model.region, model.section(section)
