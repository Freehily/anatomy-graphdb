"""
Neo4j artifact helpers for exercise data.

This module builds CSV artifacts as well as in-memory payloads that can be
merged into Neo4j via the existing graph builder.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Sequence

from stronger.databases.anatomy.neo4j_artifacts import CsvArtifact, NodePayload, RelationshipPayload
from stronger.databases.exercises.loader import ExerciseLoader, ExerciseVariant


def _join(values: Sequence[str] | None) -> str:
    filtered = [value for value in values or [] if value]
    return "|".join(filtered)


def _limb_value(entry: Dict[str, object], key: str) -> str | None:
    value = entry.get(key)
    return value if isinstance(value, str) else None


def build_node_artifacts(loader: ExerciseLoader) -> List[CsvArtifact]:
    artifacts: List[CsvArtifact] = []

    artifacts.append(
        CsvArtifact(
            filename="nodes_exercise_templates.csv",
            headers=["templateId:ID(ExerciseTemplate)", "name"],
            rows=[
                {
                    "templateId:ID(ExerciseTemplate)": template.id,
                    "name": template.name,
                }
                for template in loader.templates.values()
            ],
        )
    )

    artifacts.append(
        CsvArtifact(
            filename="nodes_exercises.csv",
            headers=[
                "exerciseId:ID(Exercise)",
                "name",
                "templateId:STRING",
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
                "arms_mode",
                "arms_cadence",
                "legs_cadence",
                "foot_elevation",
                "movement_patterns",
                "planes_of_motion",
                "target_muscle_group",
                "short_demo",
                "long_demo",
            ],
            rows=[
                _exercise_row(variant)
                for variant in loader.exercise_variants
            ],
        )
    )

    artifacts.append(
        CsvArtifact(
            filename="nodes_equipment.csv",
            headers=["equipmentId:ID(Equipment)", "name", "category"],
            rows=[
                {
                    "equipmentId:ID(Equipment)": item.id,
                    "name": item.name,
                    "category": item.parent_id or "",
                }
                for item in loader.equipment_items.values()
            ],
        )
    )

    movement_patterns = loader.taxonomies.get("movement_patterns", {})
    artifacts.append(
        CsvArtifact(
            filename="nodes_movement_patterns.csv",
            headers=["patternId:ID(MovementPattern)", "name", "description"],
            rows=[
                {
                    "patternId:ID(MovementPattern)": entry.id,
                    "name": entry.name,
                    "description": entry.description or "",
                }
                for entry in sorted(movement_patterns.values(), key=lambda item: item.id)
            ],
        )
    )

    planes = loader.taxonomies.get("planes", {})
    artifacts.append(
        CsvArtifact(
            filename="nodes_planes.csv",
            headers=["planeId:ID(Plane)", "name", "description"],
            rows=[
                {
                    "planeId:ID(Plane)": entry.id,
                    "name": entry.name,
                    "description": entry.description or "",
                }
                for entry in sorted(planes.values(), key=lambda item: item.id)
            ],
        )
    )

    return artifacts


def build_relationship_artifacts(
    loader: ExerciseLoader,
    anatomy_labels: Dict[str, str],
) -> List[CsvArtifact]:
    artifacts: List[CsvArtifact] = []

    artifacts.append(
        CsvArtifact(
            filename="rels_template_variants.csv",
            headers=[":START_ID(ExerciseTemplate)", ":END_ID(Exercise)", ":TYPE"],
            rows=[
                {
                    ":START_ID(ExerciseTemplate)": template_id,
                    ":END_ID(Exercise)": variant_id,
                    ":TYPE": "HAS_VARIANT",
                }
                for template_id, template in loader.templates.items()
                for variant_id in template.variants
            ],
        )
    )

    artifacts.append(
        CsvArtifact(
            filename="rels_exercise_uses_primary.csv",
            headers=[":START_ID(Exercise)", ":END_ID(Equipment)", ":TYPE"],
            rows=list(_equipment_relationship_rows(loader.exercise_variants, "primary", "USES_PRIMARY", loader)),
        )
    )

    artifacts.append(
        CsvArtifact(
            filename="rels_exercise_uses_secondary.csv",
            headers=[":START_ID(Exercise)", ":END_ID(Equipment)", ":TYPE"],
            rows=list(_equipment_relationship_rows(loader.exercise_variants, "secondary", "USES_SECONDARY", loader)),
        )
    )

    for role, slug, rel_type in [
        ("prime", "primary", "PRIMARY_TARGET"),
        ("secondary", "secondary", "SECONDARY_TARGET"),
        ("tertiary", "tertiary", "TERTIARY_TARGET"),
    ]:
        buckets = _partition_muscle_relationship_rows(
            loader.exercise_variants,
            role,
            rel_type,
            loader.muscle_aliases,
            anatomy_labels,
        )
        for label, suffix in (("Muscle", "muscle"), ("MuscleHead", "muscle_head")):
            artifacts.append(
                CsvArtifact(
                    filename=f"rels_exercise_{slug}_target_{suffix}.csv",
                    headers=[":START_ID(Exercise)", f":END_ID({label})", ":TYPE"],
                    rows=buckets.get(label, []),
                )
            )

    artifacts.append(
        CsvArtifact(
            filename="rels_exercise_movement_pattern.csv",
            headers=[":START_ID(Exercise)", ":END_ID(MovementPattern)", ":TYPE"],
            rows=list(_pattern_relationship_rows(loader.exercise_variants)),
        )
    )

    artifacts.append(
        CsvArtifact(
            filename="rels_exercise_plane.csv",
            headers=[":START_ID(Exercise)", ":END_ID(Plane)", ":TYPE"],
            rows=list(_plane_relationship_rows(loader.exercise_variants)),
        )
    )

    return artifacts


def build_node_payloads(loader: ExerciseLoader) -> List[NodePayload]:
    nodes: List[NodePayload] = []

    for template in loader.templates.values():
        nodes.append(
            NodePayload(
                label="ExerciseTemplate",
                id=template.id,
                properties={"name": template.name},
            )
        )

    for variant in loader.exercise_variants:
        entry = _exercise_row(variant)
        props = entry.copy()
        props.pop("exerciseId:ID(Exercise)")
        nodes.append(
            NodePayload(
                label="Exercise",
                id=variant.id,
                properties=props,
            )
        )

    for item in loader.equipment_items.values():
        nodes.append(
            NodePayload(
                label="Equipment",
                id=item.id,
                properties={
                    "name": item.name,
                    "category": item.parent_id or "",
                },
            )
        )

    movement_patterns = loader.taxonomies.get("movement_patterns", {})
    for entry in movement_patterns.values():
        nodes.append(
            NodePayload(
                label="MovementPattern",
                id=entry.id,
                properties={
                    "name": entry.name,
                    "description": entry.description or "",
                },
            )
        )

    planes = loader.taxonomies.get("planes", {})
    for entry in planes.values():
        nodes.append(
            NodePayload(
                label="Plane",
                id=entry.id,
                properties={
                    "name": entry.name,
                    "description": entry.description or "",
                },
            )
        )

    return nodes


def build_relationship_payloads(
    loader: ExerciseLoader,
    anatomy_labels: Dict[str, str],
) -> List[RelationshipPayload]:
    relationships: List[RelationshipPayload] = []

    for template in loader.templates.values():
        for variant_id in template.variants:
            relationships.append(
                RelationshipPayload(
                    type="HAS_VARIANT",
                    start_label="ExerciseTemplate",
                    start_id=template.id,
                    end_label="Exercise",
                    end_id=variant_id,
                    properties={},
                )
            )

    relationships.extend(
        _equipment_relationship_payloads(loader.exercise_variants, "primary", "USES_PRIMARY")
    )
    relationships.extend(
        _equipment_relationship_payloads(loader.exercise_variants, "secondary", "USES_SECONDARY")
    )

    for role, rel_type in [
        ("prime", "PRIMARY_TARGET"),
        ("secondary", "SECONDARY_TARGET"),
        ("tertiary", "TERTIARY_TARGET"),
    ]:
        for anatomy_id, label, variant_id in _resolved_muscle_targets(
            loader.exercise_variants, role, loader.muscle_aliases, anatomy_labels
        ):
            relationships.append(
                RelationshipPayload(
                    type=rel_type,
                    start_label="Exercise",
                    start_id=variant_id,
                    end_label=label,
                    end_id=anatomy_id,
                    properties={},
                )
            )

    for variant in loader.exercise_variants:
        for pattern_id in variant.raw.get("movement_patterns", []):  # type: ignore[assignment]
            relationships.append(
                RelationshipPayload(
                    type="FOLLOWS_PATTERN",
                    start_label="Exercise",
                    start_id=variant.id,
                    end_label="MovementPattern",
                    end_id=pattern_id,
                    properties={},
                )
            )

        for plane_id in variant.raw.get("planes_of_motion", []):  # type: ignore[assignment]
            relationships.append(
                RelationshipPayload(
                    type="OPERATES_IN",
                    start_label="Exercise",
                    start_id=variant.id,
                    end_label="Plane",
                    end_id=plane_id,
                    properties={},
                )
            )

    return relationships


# -----------------------
# Internal helpers
# -----------------------

def _exercise_row(variant: ExerciseVariant) -> Dict[str, str]:
    raw = variant.raw
    limb_usage = raw.get("limb_usage", {})
    arms = limb_usage.get("arms", {}) if isinstance(limb_usage, Mapping) else {}
    legs = limb_usage.get("legs", {}) if isinstance(limb_usage, Mapping) else {}

    return {
        "exerciseId:ID(Exercise)": variant.id,
        "name": variant.name,
        "templateId:STRING": variant.template,
        "body_region": raw.get("body_region", ""),
        "level": raw.get("level", ""),
        "force_type": raw.get("force_type", ""),
        "mechanics": raw.get("mechanics", ""),
        "laterality": raw.get("laterality", ""),
        "classification": raw.get("classification", ""),
        "posture": raw.get("posture", ""),
        "combination_type": raw.get("combination_type", ""),
        "load_position": raw.get("load_position", ""),
        "grip": raw.get("grip", ""),
        "arms_mode": _limb_value(arms, "mode") or "",
        "arms_cadence": _limb_value(arms, "cadence") or "",
        "legs_cadence": _limb_value(legs, "cadence") or "",
        "foot_elevation": _limb_value(legs, "foot_elevation") or "",
        "movement_patterns": _join(raw.get("movement_patterns")),
        "planes_of_motion": _join(raw.get("planes_of_motion")),
        "target_muscle_group": raw.get("target_muscle_group", ""),
        "short_demo": (raw.get("media", {}) or {}).get("short_demo", ""),
        "long_demo": (raw.get("media", {}) or {}).get("long_demo", ""),
    }


def _equipment_relationship_rows(
    variants: Iterable[ExerciseVariant],
    key: str,
    rel_type: str,
    loader: ExerciseLoader,
) -> Iterable[Dict[str, str]]:
    for variant in variants:
        eq_ids = variant.raw.get("equipment", {}).get(key, [])  # type: ignore[assignment]
        for eq_id in eq_ids:
            if eq_id in loader.equipment_items:
                yield {
                    ":START_ID(Exercise)": variant.id,
                    ":END_ID(Equipment)": eq_id,
                    ":TYPE": rel_type,
                }


def _equipment_relationship_payloads(
    variants: Iterable[ExerciseVariant],
    key: str,
    rel_type: str,
) -> Iterable[RelationshipPayload]:
    for variant in variants:
        eq_ids = variant.raw.get("equipment", {}).get(key, [])  # type: ignore[assignment]
        for eq_id in eq_ids:
            yield RelationshipPayload(
                type=rel_type,
                start_label="Exercise",
                start_id=variant.id,
                end_label="Equipment",
                end_id=eq_id,
                properties={},
            )


def _partition_muscle_relationship_rows(
    variants: Iterable[ExerciseVariant],
    role: str,
    rel_type: str,
    alias_map: Dict[str, List[Dict[str, str]]],
    anatomy_labels: Dict[str, str],
) -> Dict[str, List[Dict[str, str]]]:
    buckets: Dict[str, List[Dict[str, str]]] = {}
    for anatomy_id, label, variant_id in _resolved_muscle_targets(variants, role, alias_map, anatomy_labels):
        field = f":END_ID({label})"
        row = {
            ":START_ID(Exercise)": variant_id,
            field: anatomy_id,
            ":TYPE": rel_type,
        }
        buckets.setdefault(label, []).append(row)
    return buckets


def _resolved_muscle_targets(
    variants: Iterable[ExerciseVariant],
    role: str,
    alias_map: Dict[str, List[Dict[str, str]]],
    anatomy_labels: Dict[str, str],
) -> Iterable[tuple[str, str, str]]:
    for variant in variants:
        aliases = variant.raw.get("muscles", {}).get(role, [])  # type: ignore[assignment]
        for alias in aliases:
            alias_key = alias.lower()
            targets = alias_map.get(alias_key)
            if not targets:
                raise ValueError(f"Exercise '{variant.id}' references unknown muscle alias '{alias}'.")
            for target in targets:
                anatomy_id = target.get("id")
                label = target.get("label") or anatomy_labels.get(anatomy_id)
                if not anatomy_id or anatomy_id not in anatomy_labels:
                    raise ValueError(
                        f"Exercise '{variant.id}' alias '{alias}' points to missing anatomy id '{anatomy_id}'."
                    )
                if not label:
                    label = anatomy_labels[anatomy_id]
                yield anatomy_id, label, variant.id


def _pattern_relationship_rows(variants: Iterable[ExerciseVariant]) -> Iterable[Dict[str, str]]:
    for variant in variants:
        pattern_ids = variant.raw.get("movement_patterns", [])  # type: ignore[assignment]
        for pattern_id in pattern_ids:
            yield {
                ":START_ID(Exercise)": variant.id,
                ":END_ID(MovementPattern)": pattern_id,
                ":TYPE": "FOLLOWS_PATTERN",
            }


def _plane_relationship_rows(variants: Iterable[ExerciseVariant]) -> Iterable[Dict[str, str]]:
    for variant in variants:
        plane_ids = variant.raw.get("planes_of_motion", [])  # type: ignore[assignment]
        for plane_id in plane_ids:
            yield {
                ":START_ID(Exercise)": variant.id,
                ":END_ID(Plane)": plane_id,
                ":TYPE": "OPERATES_IN",
            }
