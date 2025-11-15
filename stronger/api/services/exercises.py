"""Exercise-facing service helpers backed by Neo4j."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from stronger.api.neo4j import Neo4jClient, get_neo4j_client


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _extra(payload: Mapping[str, Any], consumed: Sequence[str]) -> Dict[str, Any]:
    consumed_keys = set(consumed)
    return {key: value for key, value in payload.items() if key not in consumed_keys}


def _normalise_roles(payload: Mapping[str, Any]) -> Dict[str, List[str]]:
    return {
        "prime": _as_list(payload.get("prime")),
        "secondary": _as_list(payload.get("secondary")),
        "tertiary": _as_list(payload.get("tertiary")),
    }


def _normalise_equipment(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "primary": _as_list(payload.get("primary")),
        "secondary": _as_list(payload.get("secondary")),
        "primary_count": payload.get("primary_count"),
        "secondary_count": payload.get("secondary_count"),
    }


def _normalise_media(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "short_demo": payload.get("short_demo"),
        "long_demo": payload.get("long_demo"),
    }


def _build_variant(payload: Mapping[str, Any]) -> Dict[str, Any]:
    identifier = str(payload.get("id", ""))
    name = str(payload.get("name", ""))
    consumed = {
        "id",
        "name",
        "description",
        "template",
        "body_region",
        "level",
        "force_type",
        "mechanics",
        "laterality",
        "classification",
        "posture",
        "combination_type",
        "load_position",
        "grip",
        "limb_usage",
        "movement_patterns",
        "planes_of_motion",
        "target_muscle_group",
        "muscles",
        "equipment",
        "media",
    }
    limb_usage_raw = payload.get("limb_usage", {})
    arms = limb_usage_raw.get("arms", {}) if isinstance(limb_usage_raw, Mapping) else {}
    legs = limb_usage_raw.get("legs", {}) if isinstance(limb_usage_raw, Mapping) else {}
    return {
        "id": identifier,
        "name": name,
        "description": payload.get("description"),
        "template": str(payload.get("template", "")),
        "body_region": str(payload.get("body_region", "")),
        "level": payload.get("level"),
        "force_type": payload.get("force_type"),
        "mechanics": payload.get("mechanics"),
        "laterality": payload.get("laterality"),
        "classification": payload.get("classification"),
        "posture": payload.get("posture"),
        "combination_type": payload.get("combination_type"),
        "load_position": payload.get("load_position"),
        "grip": payload.get("grip"),
        "limb_usage": {
            "arms": dict(arms) if isinstance(arms, Mapping) else {},
            "legs": dict(legs) if isinstance(legs, Mapping) else {},
        },
        "movement_patterns": _as_list(payload.get("movement_patterns")),
        "planes_of_motion": _as_list(payload.get("planes_of_motion")),
        "target_muscle_group": payload.get("target_muscle_group"),
        "muscles": _normalise_roles(payload.get("muscles", {})),
        "equipment": _normalise_equipment(payload.get("equipment", {})),
        "media": _normalise_media(payload.get("media", {})),
        "extra": _extra(payload, consumed),
    }


def _build_template(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(payload.get("id", "")),
        "name": str(payload.get("name", "")),
        "description": payload.get("description"),
        "aliases": _as_list(payload.get("aliases")),
        "variants": _as_list(payload.get("variants")),
    }


def _build_equipment(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(payload.get("id", "")),
        "name": str(payload.get("name", "")),
        "description": payload.get("description"),
        "parent_id": payload.get("parent_id"),
        "aliases": _as_list(payload.get("aliases")),
    }


def _build_alias(payload: Mapping[str, Any]) -> Dict[str, Any]:
    targets_payload = payload.get("targets") or []
    targets: List[Dict[str, Any]] = []
    for target in targets_payload:
        target_id = target.get("id")
        if not target_id:
            continue
        targets.append({"id": str(target_id), "label": target.get("label")})
    return {
        "alias": str(payload.get("alias", "")),
        "name": payload.get("name"),
        "targets": targets,
    }


def _build_taxonomy_entry(payload: Mapping[str, Any], key: str) -> Dict[str, Any]:
    return {
        "key": key,
        "id": str(payload.get("id", "")),
        "name": str(payload.get("name", "")),
        "description": payload.get("description"),
        "aliases": _as_list(payload.get("aliases")),
    }


class ExerciseServiceError(RuntimeError):
    """Raised when an entity cannot be resolved from Neo4j."""


class ExerciseService:
    """Caches Neo4j payloads so repeated requests avoid re-querying Aura."""

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self._client = client or get_neo4j_client()
        self._taxonomies: Dict[str, List[Dict[str, Any]]] | None = None
        self._templates: List[Dict[str, Any]] | None = None
        self._variants: Dict[str, Dict[str, Any]] | None = None
        self._equipment: Dict[str, Dict[str, Any]] | None = None
        self._aliases: Dict[str, Dict[str, Any]] | None = None

    def _load_taxonomies(self) -> Dict[str, List[Dict[str, Any]]]:
        if self._taxonomies is not None:
            return self._taxonomies
        cache: Dict[str, List[Dict[str, Any]]] = {}
        rows = self._client.query(
            """
            MATCH (entry:TaxonomyEntry)
            RETURN entry.taxonomy_key AS key, entry.payload AS payload
            """
        )
        for row in rows:
            key = row.get("key")
            payload = row.get("payload")
            if not key or not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            cache.setdefault(key, []).append(_build_taxonomy_entry(data, key))
        for entries in cache.values():
            entries.sort(key=lambda item: item["id"])
        self._taxonomies = cache
        return cache

    def _load_templates(self) -> List[Dict[str, Any]]:
        if self._templates is not None:
            return self._templates
        rows = self._client.query(
            """
            MATCH (template:ExerciseTemplate)
            RETURN template.payload AS payload
            ORDER BY template.name
            """
        )
        templates: List[Dict[str, Any]] = []
        for row in rows:
            payload = row.get("payload")
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            templates.append(_build_template(data))
        templates.sort(key=lambda item: item["id"])
        self._templates = templates
        return templates

    def _load_variants(self) -> Dict[str, Dict[str, Any]]:
        if self._variants is not None:
            return self._variants
        rows = self._client.query(
            """
            MATCH (variant:Exercise)
            RETURN variant.payload AS payload
            """
        )
        variants: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            payload = row.get("payload")
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            variant = _build_variant(data)
            variants[variant["id"].lower()] = variant
        self._variants = variants
        return variants

    def _load_equipment(self) -> Dict[str, Dict[str, Any]]:
        if self._equipment is not None:
            return self._equipment
        rows = self._client.query(
            """
            MATCH (equipment:Equipment)
            RETURN equipment.payload AS payload
            """
        )
        equipment: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            payload = row.get("payload")
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            item = _build_equipment(data)
            equipment[item["id"].lower()] = item
        self._equipment = equipment
        return equipment

    def _load_aliases(self) -> Dict[str, Dict[str, Any]]:
        if self._aliases is not None:
            return self._aliases
        rows = self._client.query(
            """
            MATCH (alias:MuscleAlias)
            RETURN alias.payload AS payload
            """
        )
        aliases: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            payload = row.get("payload")
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            alias = _build_alias(data)
            aliases[alias["alias"].lower()] = alias
        self._aliases = aliases
        return aliases

    def list_taxonomy_keys(self) -> Sequence[str]:
        return sorted(self._load_taxonomies())

    def get_taxonomy(self, key: str) -> Dict[str, Any]:
        key_lower = key.lower()
        for taxonomy_key, entries in self._load_taxonomies().items():
            if taxonomy_key.lower() == key_lower:
                return {"key": taxonomy_key, "entries": entries}
        raise KeyError(f"Unknown taxonomy '{key}'.")

    def list_templates(self) -> Sequence[Dict[str, Any]]:
        return self._load_templates()

    def list_variants(self, *, body_region: str | None = None) -> Sequence[Dict[str, Any]]:
        variants = list(self._load_variants().values())
        if body_region:
            region_key = body_region.lower()
            variants = [variant for variant in variants if variant["body_region"].lower() == region_key]
        return sorted(variants, key=lambda item: item["id"])

    def get_variant(self, exercise_id: str) -> Dict[str, Any]:
        variant = self._load_variants().get(exercise_id.lower())
        if not variant:
            raise KeyError(f"Exercise '{exercise_id}' not found.")
        return variant

    def list_equipment(self) -> Sequence[Dict[str, Any]]:
        return sorted(self._load_equipment().values(), key=lambda item: item["id"])

    def get_equipment(self, equipment_id: str) -> Dict[str, Any]:
        match = self._load_equipment().get(equipment_id.lower())
        if not match:
            raise KeyError(f"Equipment '{equipment_id}' not found.")
        return match

    def list_muscle_aliases(self) -> Sequence[Dict[str, Any]]:
        return sorted(self._load_aliases().values(), key=lambda item: item["alias"])

    def get_muscle_alias(self, alias: str) -> Dict[str, Any]:
        match = self._load_aliases().get(alias.lower())
        if not match:
            raise KeyError(f"Muscle alias '{alias}' not found.")
        return match

    def list_muscle_groups(self) -> Sequence[Dict[str, Any]]:
        taxonomy = self.get_taxonomy("muscle_groups")
        return taxonomy["entries"]

    def get_muscle_group(self, group_id: str) -> Dict[str, Any]:
        key = group_id.lower()
        for entry in self.list_muscle_groups():
            if entry["id"].lower() == key:
                return entry
        raise KeyError(f"Muscle group '{group_id}' not found.")

    def _variant_aliases(self, variant: Mapping[str, Any]) -> List[str]:
        aliases: List[str] = []
        roles = variant.get("muscles", {})
        for bucket in ("prime", "secondary", "tertiary"):
            for alias in roles.get(bucket, []):
                if alias:
                    aliases.append(alias.lower())
        return aliases

    def muscles_for_group(self, group_id: str) -> Sequence[Dict[str, Any]]:
        group = self.get_muscle_group(group_id)
        group_key = group["id"].lower()
        aliases: Dict[str, Dict[str, Any]] = {}
        alias_index = self._load_aliases()
        for variant in self._load_variants().values():
            target = (variant.get("target_muscle_group") or "").lower()
            if target != group_key:
                continue
            for alias in self._variant_aliases(variant):
                entry = alias_index.get(alias)
                if entry:
                    aliases[alias] = entry
        return sorted(aliases.values(), key=lambda item: item["alias"])

    def variants_for_muscle_group(self, group_id: str) -> Sequence[Dict[str, Any]]:
        key = self.get_muscle_group(group_id)["id"].lower()
        matches = [
            variant
            for variant in self._load_variants().values()
            if (variant.get("target_muscle_group") or "").lower() == key
        ]
        return sorted(matches, key=lambda item: item["id"])

    def variants_for_muscle(self, alias: str) -> Sequence[Dict[str, Any]]:
        alias_entry = self.get_muscle_alias(alias)
        alias_key = alias_entry["alias"].lower()
        matches = [variant for variant in self._load_variants().values() if alias_key in self._variant_aliases(variant)]
        return sorted(matches, key=lambda item: item["id"])

    def equipment_for_variant(self, exercise_id: str) -> Dict[str, Any]:
        variant = self.get_variant(exercise_id)
        return variant["equipment"]

    def variants_for_equipment(self, equipment_id: str) -> Sequence[Dict[str, Any]]:
        equipment = self.get_equipment(equipment_id)
        eq_key = equipment["id"].lower()
        matches: List[Dict[str, Any]] = []
        for variant in self._load_variants().values():
            primary = [item.lower() for item in variant["equipment"]["primary"]]
            secondary = [item.lower() for item in variant["equipment"]["secondary"]]
            if eq_key in primary or eq_key in secondary:
                matches.append(variant)
        return sorted(matches, key=lambda item: item["id"])
