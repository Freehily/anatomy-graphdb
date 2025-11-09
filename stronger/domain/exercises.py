"""
Typed domain structures for the exercise dataset.

This translates the raw dictionaries loaded by `ExerciseLoader` into stable
dataclasses so API layers and other consumers can work with explicit fields
instead of hand-rolled dict access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml

from stronger.databases.exercises.loader import ExerciseLoader


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _common(payload: Mapping[str, Any]) -> Dict[str, Any]:
    try:
        identifier = payload["id"]
        name = payload["name"]
    except KeyError as exc:  # pragma: no cover - configuration errors
        raise ValueError(
            f"Expected key '{exc.args[0]}' in exercise payload: {payload}"
        ) from exc
    return {
        "id": str(identifier),
        "name": str(name),
        "description": payload.get("description"),
    }


def _extra(
        payload: Mapping[str, Any], consumed: Iterable[str]
) -> Dict[str, Any]:
    cons_keys = set(consumed)
    return {
        key: value for key, value in payload.items() if key not in cons_keys
    }


@dataclass(slots=True)
class DomainEntity:
    id: str
    name: str
    description: str | None = field(default=None, kw_only=True)
    extra: Dict[str, Any] = field(default_factory=dict, repr=False, kw_only=True)


@dataclass(slots=True)
class TaxonomyEntry(DomainEntity):
    aliases: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Taxonomy:
    key: str
    entries: List[TaxonomyEntry]


@dataclass(slots=True)
class EquipmentItem(DomainEntity):
    parent_id: str | None = None
    aliases: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ExerciseTemplate(DomainEntity):
    aliases: List[str] = field(default_factory=list)
    variants: List[str] = field(default_factory=list)


@dataclass(slots=True)
class LimbUsage:
    arms: Dict[str, Any] = field(default_factory=dict)
    legs: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MuscleRoles:
    prime: List[str] = field(default_factory=list)
    secondary: List[str] = field(default_factory=list)
    tertiary: List[str] = field(default_factory=list)


@dataclass(slots=True)
class EquipmentSelection:
    primary: List[str] = field(default_factory=list)
    secondary: List[str] = field(default_factory=list)
    primary_count: int | None = None
    secondary_count: int | None = None


@dataclass(slots=True)
class MediaLinks:
    short_demo: str | None = None
    long_demo: str | None = None


@dataclass(slots=True)
class ExerciseVariant(DomainEntity):
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
    limb_usage: LimbUsage = field(default_factory=LimbUsage)
    movement_patterns: List[str] = field(default_factory=list)
    planes_of_motion: List[str] = field(default_factory=list)
    target_muscle_group: str | None = None
    muscles: MuscleRoles = field(default_factory=MuscleRoles)
    equipment: EquipmentSelection = field(default_factory=EquipmentSelection)
    media: MediaLinks = field(default_factory=MediaLinks)


@dataclass(slots=True)
class MuscleAliasTarget:
    id: str
    label: str | None = None


@dataclass(slots=True)
class MuscleAlias:
    alias: str
    name: str | None = None
    targets: List[MuscleAliasTarget] = field(default_factory=list)


@dataclass(slots=True)
class ExerciseDataset:
    taxonomies: List[Taxonomy] = field(default_factory=list)
    equipment: List[EquipmentItem] = field(default_factory=list)
    templates: List[ExerciseTemplate] = field(default_factory=list)
    variants: List[ExerciseVariant] = field(default_factory=list)
    muscle_aliases: List[MuscleAlias] = field(default_factory=list)

    def taxonomy(self, key: str) -> Taxonomy:
        for taxonomy in self.taxonomies:
            if taxonomy.key == key:
                return taxonomy
        raise KeyError(f"Unknown taxonomy '{key}'")


def _build_taxonomies(loader: ExerciseLoader) -> List[Taxonomy]:
    taxonomies: List[Taxonomy] = []
    for key in sorted(loader.taxonomies):
        entries_source = loader.taxonomies[key]
        entries = [
            TaxonomyEntry(
                **_common(entry.__dict__),
                aliases=list(entry.aliases or []),
                extra={},  # ExerciseLoader entries already normalized.
            )
            for entry in sorted(entries_source.values(), key=lambda item: item.id)
        ]
        taxonomies.append(Taxonomy(key=key, entries=entries))
    return taxonomies


def _build_equipment(loader: ExerciseLoader) -> List[EquipmentItem]:
    items: List[EquipmentItem] = []
    for item in sorted(
        loader.equipment_items.values(), key=lambda entry: entry.id
    ):
        items.append(
            EquipmentItem(
                **_common(item.__dict__),
                parent_id=item.parent_id,
                aliases=[
                    alias
                    for alias, canonical in loader.equipment_aliases.items()
                    if canonical == item.id and alias != item.id and alias != item.name.lower()
                ],
                extra={},
            )
        )
    return items


def _build_templates(loader: ExerciseLoader) -> List[ExerciseTemplate]:
    return [
        ExerciseTemplate(
            **_common(template.__dict__),
            aliases=list(template.aliases or []),
            variants=list(template.variants or []),
            extra={},
        )
        for template in sorted(loader.templates.values(), key=lambda entry: entry.id)
    ]


def _normalize_roles(payload: Mapping[str, Any]) -> MuscleRoles:
    return MuscleRoles(
        prime=_as_list(payload.get("prime")),
        secondary=_as_list(payload.get("secondary")),
        tertiary=_as_list(payload.get("tertiary")),
    )


def _normalize_equipment(payload: Mapping[str, Any]) -> EquipmentSelection:
    return EquipmentSelection(
        primary=_as_list(payload.get("primary")),
        secondary=_as_list(payload.get("secondary")),
        primary_count=payload.get("primary_count"),
        secondary_count=payload.get("secondary_count"),
    )


def _normalize_media(payload: Mapping[str, Any]) -> MediaLinks:
    return MediaLinks(
        short_demo=payload.get("short_demo"),
        long_demo=payload.get("long_demo"),
    )


def _build_variant(entry: Mapping[str, Any]) -> ExerciseVariant:
    common = _common(entry)
    consumed = {
        *common.keys(),
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
    extra = _extra(entry, consumed)
    return ExerciseVariant(
        **common,
        template=str(entry.get("template", "")),
        body_region=str(entry.get("body_region", "")),
        level=entry.get("level"),
        force_type=entry.get("force_type"),
        mechanics=entry.get("mechanics"),
        laterality=entry.get("laterality"),
        classification=entry.get("classification"),
        posture=entry.get("posture"),
        combination_type=entry.get("combination_type"),
        load_position=entry.get("load_position"),
        grip=entry.get("grip"),
        limb_usage=LimbUsage(
            arms=dict(entry.get("limb_usage", {}).get("arms", {})),
            legs=dict(entry.get("limb_usage", {}).get("legs", {})),
        ),
        movement_patterns=_as_list(entry.get("movement_patterns")),
        planes_of_motion=_as_list(entry.get("planes_of_motion")),
        target_muscle_group=entry.get("target_muscle_group"),
        muscles=_normalize_roles(entry.get("muscles", {})),
        equipment=_normalize_equipment(entry.get("equipment", {})),
        media=_normalize_media(entry.get("media", {})),
        extra=extra,
    )


def _build_variants(loader: ExerciseLoader) -> List[ExerciseVariant]:
    variants = [_build_variant(variant.raw) for variant in loader.exercise_variants]
    return sorted(variants, key=lambda variant: variant.id)


def _build_muscle_aliases(loader: ExerciseLoader) -> List[MuscleAlias]:
    alias_config = loader.index.get("anatomy_aliases", {}).get("muscles")
    if not alias_config:
        return []
    path = loader.root / alias_config
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    entries: List[MuscleAlias] = []
    for entry in data.get("muscles", []) or []:
        alias = entry.get("alias") or entry.get("id")
        if not alias:
            continue
        targets_payload = entry.get("targets") or []
        targets = [
            MuscleAliasTarget(id=str(target["id"]), label=target.get("label"))
            for target in targets_payload
            if target.get("id")
        ]
        entries.append(
            MuscleAlias(
                alias=str(alias),
                name=entry.get("name"),
                targets=targets,
            )
        )
    return sorted(entries, key=lambda item: item.alias)


def build_exercise_dataset(root: Path | None = None) -> ExerciseDataset:
    loader = ExerciseLoader(root)
    loader.load()
    return ExerciseDataset(
        taxonomies=_build_taxonomies(loader),
        equipment=_build_equipment(loader),
        templates=_build_templates(loader),
        variants=_build_variants(loader),
        muscle_aliases=_build_muscle_aliases(loader),
    )
