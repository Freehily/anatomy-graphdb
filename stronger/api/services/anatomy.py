"""Application-layer helpers that expose anatomy data sourced from Neo4j."""

from __future__ import annotations

import json
from typing import Dict, Sequence

from stronger.api.neo4j import Neo4jClient, get_neo4j_client
from stronger.databases.anatomy.loader import AnatomyRegion, SectionData
from stronger.domain.anatomy import AnatomyModel, DomainEntity, build_anatomy_model

SECTION_LABELS: Dict[str, str] = {
    "bones": "Bone",
    "attachment_points": "AttachmentPoint",
    "muscle_heads": "MuscleHead",
    "muscles": "Muscle",
    "nerves": "Nerve",
    "arteries": "Artery",
    "actions": "Action",
}


class AnatomyServiceError(RuntimeError):
    """Raised when the requested region cannot be resolved."""


class AnatomyService:
    """Queries AuraDB for anatomy nodes and converts them back into domain models."""

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self._client = client or get_neo4j_client()

    def list_regions(self) -> Sequence[str]:
        rows = self._client.query(
            """
            MATCH (b:Bone)
            WHERE b.region_slug IS NOT NULL
            RETURN DISTINCT b.region_slug AS region
            ORDER BY region
            """
        )
        return [row["region"] for row in rows if row.get("region")]

    def _load_section_items(self, label: str, region: str) -> list[dict]:
        rows = self._client.query(
            f"""
            MATCH (node:{label})
            WHERE node.region_slug = $region
            RETURN node.payload AS payload
            ORDER BY node.name
            """,
            {"region": region},
        )
        items: list[dict] = []
        for row in rows:
            payload = row.get("payload")
            if not payload:
                continue
            try:
                items.append(json.loads(payload))
            except json.JSONDecodeError:
                continue
        return items

    def get_region(self, region: str, *, include_shared: bool = True) -> AnatomyModel:
        if not include_shared:
            raise AnatomyServiceError("Shared exclusions are not supported with the Neo4j backend.")

        sections: Dict[str, SectionData] = {}
        for section_name, label in SECTION_LABELS.items():
            payloads = self._load_section_items(label, region)
            if payloads:
                sections[section_name] = SectionData(name=section_name, items=payloads)

        if not sections:
            raise AnatomyServiceError(f"Region '{region}' not found in Neo4j.")

        region_model = AnatomyRegion(region=region, sections=sections)
        return build_anatomy_model(region_model)

    def get_section(
        self,
        region: str,
        section: str,
        *,
        include_shared: bool = True,
    ) -> tuple[str, Sequence[DomainEntity]]:
        model = self.get_region(region, include_shared=include_shared)
        return model.region, model.section(section)
