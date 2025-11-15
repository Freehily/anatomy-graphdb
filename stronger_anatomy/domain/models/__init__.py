"""
Typed domain models wrapping `stronger_anatomy.databases.anatomy.loader`.

The loader returns generic dictionaries, which is flexible but awkward for API
consumers.  These dataclasses provide a stable API surface and keep any
schema-specific decisions (list coercion, optional fields, renamed attributes)
in one place.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, TypeVar

from stronger_anatomy.databases.anatomy.loader import AnatomyRegion, SectionData

DomainEntityT = TypeVar("DomainEntityT", bound="DomainEntity")


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _common_kwargs(payload: Mapping[str, Any]) -> Dict[str, Any]:
    try:
        identifier = payload["id"]
        name = payload["name"]
    except KeyError as exc:  # pragma: no cover - configuration errors
        missing = exc.args[0]
        raise ValueError(f"Expected key '{missing}' in anatomy payload: {payload}") from exc
    return {
        "id": str(identifier),
        "name": str(name),
        "description": payload.get("description"),
    }


def _extra(payload: Mapping[str, Any], consumed: Iterable[str]) -> Dict[str, Any]:
    consumed_keys = set(consumed)
    return {key: value for key, value in payload.items() if key not in consumed_keys}


@dataclass(slots=True)
class DomainEntity:
    """Base class for all typed anatomy entities."""

    id: str
    name: str
    description: str | None = field(default=None, kw_only=True)
    extra: Dict[str, Any] = field(default_factory=dict, repr=False, kw_only=True)


@dataclass(slots=True)
class Bone(DomainEntity):
    region: str | None = None
    attachments: List[str] = field(default_factory=list)


@dataclass(slots=True)
class AttachmentPoint(DomainEntity):
    bone: str | None = None


@dataclass(slots=True)
class MuscleHead(DomainEntity):
    origin: List[str] = field(default_factory=list)
    innervation: List[str] = field(default_factory=list)
    arteries: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Muscle(DomainEntity):
    group: str | None = None
    order: str | None = None
    heads: List[str] = field(default_factory=list)
    insertion: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    antagonists: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Nerve(DomainEntity):
    derivations: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    pathway: str | None = None
    clinical_significance: str | None = None
    innervates: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Artery(DomainEntity):
    branches_from: str | None = None
    supplies: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Action(DomainEntity):
    joint: str | None = None
    action_type: str | None = None
    primary_movers: List[str] = field(default_factory=list)


@dataclass(slots=True)
class AnatomyModel:
    """Fully-typed representation of a single loaded region."""

    region: str
    bones: List[Bone] = field(default_factory=list)
    attachment_points: List[AttachmentPoint] = field(default_factory=list)
    muscle_heads: List[MuscleHead] = field(default_factory=list)
    muscles: List[Muscle] = field(default_factory=list)
    nerves: List[Nerve] = field(default_factory=list)
    arteries: List[Artery] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)

    def section(self, name: str) -> Sequence[DomainEntity]:
        """Return one of the section lists by name, raising on typos."""

        try:
            return getattr(self, name)
        except AttributeError as exc:
            raise KeyError(f"Unknown anatomy section '{name}'") from exc


def _build_entities(
    section: SectionData | None,
    builder: Callable[[Mapping[str, Any]], DomainEntityT],
) -> List[DomainEntityT]:
    if section is None:
        return []
    return [builder(item) for item in section.items]


def _section(region: AnatomyRegion, name: str) -> SectionData | None:
    return region.sections.get(name)


def _build_bone(payload: Mapping[str, Any]) -> Bone:
    common = _common_kwargs(payload)
    attachments = _as_list(payload.get("attachments"))
    extra = _extra(payload, {*common.keys(), "attachments", "region"})
    return Bone(
        **common,
        region=payload.get("region"),
        attachments=attachments,
        extra=extra,
    )


def _build_attachment_point(payload: Mapping[str, Any]) -> AttachmentPoint:
    common = _common_kwargs(payload)
    extra = _extra(payload, {*common.keys(), "bone"})
    return AttachmentPoint(**common, bone=payload.get("bone"), extra=extra)


def _build_muscle_head(payload: Mapping[str, Any]) -> MuscleHead:
    common = _common_kwargs(payload)
    extra = _extra(payload, {*common.keys(), "origin", "innervation", "arteries"})
    return MuscleHead(
        **common,
        origin=_as_list(payload.get("origin")),
        innervation=_as_list(payload.get("innervation")),
        arteries=_as_list(payload.get("arteries")),
        extra=extra,
    )


def _build_muscle(payload: Mapping[str, Any]) -> Muscle:
    common = _common_kwargs(payload)
    consumed = {
        *common.keys(),
        "group",
        "order",
        "heads",
        "insertion",
        "actions",
        "antagonists",
    }
    extra = _extra(payload, consumed)
    return Muscle(
        **common,
        group=payload.get("group"),
        order=payload.get("order"),
        heads=_as_list(payload.get("heads")),
        insertion=_as_list(payload.get("insertion")),
        actions=_as_list(payload.get("actions")),
        antagonists=_as_list(payload.get("antagonists")),
        extra=extra,
    )


def _build_nerve(payload: Mapping[str, Any]) -> Nerve:
    common = _common_kwargs(payload)
    consumed = {
        *common.keys(),
        "derivations",
        "type",
        "pathway",
        "clinical_significance",
        "innervates",
    }
    extra = _extra(payload, consumed)
    return Nerve(
        **common,
        derivations=_as_list(payload.get("derivations")),
        categories=_as_list(payload.get("type")),
        pathway=payload.get("pathway"),
        clinical_significance=payload.get("clinical_significance"),
        innervates=_as_list(payload.get("innervates")),
        extra=extra,
    )


def _build_artery(payload: Mapping[str, Any]) -> Artery:
    common = _common_kwargs(payload)
    consumed = {*common.keys(), "branches_from", "supplies"}
    extra = _extra(payload, consumed)
    return Artery(
        **common,
        branches_from=payload.get("branches_from"),
        supplies=_as_list(payload.get("supplies")),
        extra=extra,
    )


def _build_action(payload: Mapping[str, Any]) -> Action:
    common = _common_kwargs(payload)
    consumed = {*common.keys(), "joint", "type", "primary_movers"}
    extra = _extra(payload, consumed)
    return Action(
        **common,
        joint=payload.get("joint"),
        action_type=payload.get("type"),
        primary_movers=_as_list(payload.get("primary_movers")),
        extra=extra,
    )


def build_anatomy_model(region: AnatomyRegion) -> AnatomyModel:
    """Convert a loader `AnatomyRegion` into typed dataclasses."""

    return AnatomyModel(
        region=region.region,
        bones=_build_entities(_section(region, "bones"), _build_bone),
        attachment_points=_build_entities(_section(region, "attachment_points"), _build_attachment_point),
        muscle_heads=_build_entities(_section(region, "muscle_heads"), _build_muscle_head),
        muscles=_build_entities(_section(region, "muscles"), _build_muscle),
        nerves=_build_entities(_section(region, "nerves"), _build_nerve),
        arteries=_build_entities(_section(region, "arteries"), _build_artery),
        actions=_build_entities(_section(region, "actions"), _build_action),
    )
