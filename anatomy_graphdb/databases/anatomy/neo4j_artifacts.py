"""
Helpers to convert anatomy regions into Neo4j-friendly CSV artifacts.

Each artifact describes the file name, header ordering, and row payloads. The
callers (CLI, export scripts, tests) can decide whether to persist the files to
disk or stream them directly into Neo4j.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

import json

from .loader import AnatomyRegion


@dataclass
class CsvArtifact:
    filename: str
    headers: Sequence[str]
    rows: List[Dict[str, str]]


def _join(values: Sequence[str]) -> str:
    return "|".join(str(v) for v in values) if values else ""


def _dump_payload(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def build_node_artifacts(region: AnatomyRegion) -> List[CsvArtifact]:
    attachment_points = region.require("attachment_points").items
    bones = region.require("bones").items
    muscles = region.require("muscles").items
    muscle_heads = region.require("muscle_heads").items
    nerves = region.require("nerves").items
    arteries = region.require("arteries").items
    actions = region.require("actions").items

    return [
        CsvArtifact(
            filename="nodes_bones.csv",
            headers=["boneId:ID(Bone)", "name", "region:STRING", "region_slug", "payload"],
            rows=list(
                {
                    "boneId:ID(Bone)": bone["id"],
                    "name": bone.get("name", ""),
                    "region:STRING": bone.get("region", region.region),
                    "region_slug": region.region,
                    "payload": _dump_payload(bone),
                }
                for bone in bones
            ),
        ),
        CsvArtifact(
            filename="nodes_attachment_points.csv",
            headers=[
                "attachId:ID(AttachmentPoint)",
                "name",
                "structure:STRING",
                "region_slug",
                "payload",
            ],
            rows=list(
                {
                    "attachId:ID(AttachmentPoint)": ap["id"],
                    "name": ap.get("name", ""),
                    "structure:STRING": ap.get("bone", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(ap),
                }
                for ap in attachment_points
            ),
        ),
        CsvArtifact(
            filename="nodes_muscles.csv",
            headers=[
                "muscleId:ID(Muscle)",
                "name",
                "group",
                "order",
                "region_slug",
                "payload",
            ],
            rows=list(
                {
                    "muscleId:ID(Muscle)": muscle["id"],
                    "name": muscle.get("name", ""),
                    "group": muscle.get("group", ""),
                    "order": muscle.get("order", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(muscle),
                }
                for muscle in muscles
            ),
        ),
        CsvArtifact(
            filename="nodes_muscle_heads.csv",
            headers=["headId:ID(MuscleHead)", "name", "region_slug", "payload"],
            rows=list(
                {
                    "headId:ID(MuscleHead)": head["id"],
                    "name": head.get("name", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(head),
                }
                for head in muscle_heads
            ),
        ),
        CsvArtifact(
            filename="nodes_nerves.csv",
            headers=[
                "nerveId:ID(Nerve)",
                "name",
                "derivations",
                "types",
                "pathway",
                "clinical",
                "region_slug",
                "payload",
            ],
            rows=list(
                {
                    "nerveId:ID(Nerve)": nerve["id"],
                    "name": nerve.get("name", ""),
                    "derivations": _join(nerve.get("derivations", [])),
                    "types": _join(nerve.get("type", [])),
                    "pathway": nerve.get("pathway", ""),
                    "clinical": nerve.get("clinical_significance", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(nerve),
                }
                for nerve in nerves
            ),
        ),
        CsvArtifact(
            filename="nodes_arteries.csv",
            headers=["arteryId:ID(Artery)", "name", "region_slug", "payload"],
            rows=list(
                {
                    "arteryId:ID(Artery)": artery["id"],
                    "name": artery.get("name", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(artery),
                }
                for artery in arteries
            ),
        ),
        CsvArtifact(
            filename="nodes_actions.csv",
            headers=[
                "actionId:ID(Action)",
                "name",
                "joint",
                "movement_type",
                "region_slug",
                "payload",
            ],
            rows=list(
                {
                    "actionId:ID(Action)": action["id"],
                    "name": action.get("name", ""),
                    "joint": action.get("joint", ""),
                    "movement_type": action.get("type", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(action),
                }
                for action in actions
            ),
        ),
    ]


def _partition_contractiles(
    targets: Sequence[str],
    muscle_ids: set[str],
    muscle_head_ids: set[str],
) -> tuple[List[str], List[str]]:
    muscle_targets: List[str] = []
    head_targets: List[str] = []
    for target_id in targets:
        if target_id in muscle_ids:
            muscle_targets.append(target_id)
        elif target_id in muscle_head_ids:
            head_targets.append(target_id)
    return muscle_targets, head_targets


def build_relationship_artifacts(region: AnatomyRegion) -> List[CsvArtifact]:
    attachment_points = region.require("attachment_points").items
    bones = region.require("bones").items
    muscles = region.require("muscles").items
    muscle_heads = region.require("muscle_heads").items
    nerves = region.require("nerves").items
    arteries = region.require("arteries").items
    actions = region.require("actions").items

    attachment_ids = {item["id"] for item in attachment_points}
    muscle_ids = {item["id"] for item in muscles}
    muscle_head_ids = {item["id"] for item in muscle_heads}
    artery_ids = {item["id"] for item in arteries}

    antagonist_muscle_rows: List[Dict[str, str]] = []
    antagonist_head_rows: List[Dict[str, str]] = []
    nerve_muscle_rows: List[Dict[str, str]] = []
    nerve_head_rows: List[Dict[str, str]] = []
    artery_muscle_rows: List[Dict[str, str]] = []
    artery_head_rows: List[Dict[str, str]] = []
    action_muscle_rows: List[Dict[str, str]] = []
    action_head_rows: List[Dict[str, str]] = []

    for muscle in muscles:
        muscle_targets, head_targets = _partition_contractiles(
            muscle.get("antagonists", []),
            muscle_ids,
            muscle_head_ids,
        )
        for target_id in muscle_targets:
            antagonist_muscle_rows.append(
                {
                    ":START_ID(Muscle)": muscle["id"],
                    ":END_ID(Muscle)": target_id,
                    ":TYPE": "ANTAGONIST",
                }
            )
        for target_id in head_targets:
            antagonist_head_rows.append(
                {
                    ":START_ID(Muscle)": muscle["id"],
                    ":END_ID(MuscleHead)": target_id,
                    ":TYPE": "ANTAGONIST",
                }
            )

    for nerve in nerves:
        muscle_targets, head_targets = _partition_contractiles(
            nerve.get("innervates", []),
            muscle_ids,
            muscle_head_ids,
        )
        for target_id in muscle_targets:
            nerve_muscle_rows.append(
                {
                    ":START_ID(Nerve)": nerve["id"],
                    ":END_ID(Muscle)": target_id,
                    ":TYPE": "INNERVATES",
                }
            )
        for target_id in head_targets:
            nerve_head_rows.append(
                {
                    ":START_ID(Nerve)": nerve["id"],
                    ":END_ID(MuscleHead)": target_id,
                    ":TYPE": "INNERVATES",
                }
            )

    for artery in arteries:
        muscle_targets, head_targets = _partition_contractiles(
            artery.get("supplies", []),
            muscle_ids,
            muscle_head_ids,
        )
        for target_id in muscle_targets:
            artery_muscle_rows.append(
                {
                    ":START_ID(Artery)": artery["id"],
                    ":END_ID(Muscle)": target_id,
                    ":TYPE": "SUPPLIES",
                }
            )
        for target_id in head_targets:
            artery_head_rows.append(
                {
                    ":START_ID(Artery)": artery["id"],
                    ":END_ID(MuscleHead)": target_id,
                    ":TYPE": "SUPPLIES",
                }
            )

    for action in actions:
        muscle_targets, head_targets = _partition_contractiles(
            action.get("primary_movers", []),
            muscle_ids,
            muscle_head_ids,
        )
        for target_id in muscle_targets:
            action_muscle_rows.append(
                {
                    ":START_ID(Action)": action["id"],
                    ":END_ID(Muscle)": target_id,
                    ":TYPE": "PRIMARY_MOVER",
                }
            )
        for target_id in head_targets:
            action_head_rows.append(
                {
                    ":START_ID(Action)": action["id"],
                    ":END_ID(MuscleHead)": target_id,
                    ":TYPE": "PRIMARY_MOVER",
                }
            )

    return [
        CsvArtifact(
            filename="rels_bone_attachment.csv",
            headers=[":START_ID(Bone)", ":END_ID(AttachmentPoint)", ":TYPE"],
            rows=list(
                {
                    ":START_ID(Bone)": bone["id"],
                    ":END_ID(AttachmentPoint)": attachment,
                    ":TYPE": "HAS_ATTACHMENT",
                }
                for bone in bones
                for attachment in bone.get("attachments", [])
                if attachment in attachment_ids
            ),
        ),
        CsvArtifact(
            filename="rels_muscle_head.csv",
            headers=[":START_ID(Muscle)", ":END_ID(MuscleHead)", ":TYPE"],
            rows=list(
                {
                    ":START_ID(Muscle)": muscle["id"],
                    ":END_ID(MuscleHead)": head_id,
                    ":TYPE": "HAS_HEAD",
                }
                for muscle in muscles
                for head_id in muscle.get("heads", [])
                if head_id in muscle_head_ids
            ),
        ),
        CsvArtifact(
            filename="rels_muscle_insertion.csv",
            headers=[":START_ID(Muscle)", ":END_ID(AttachmentPoint)", ":TYPE"],
            rows=list(
                {
                    ":START_ID(Muscle)": muscle["id"],
                    ":END_ID(AttachmentPoint)": attachment_id,
                    ":TYPE": "INSERTS_AT",
                }
                for muscle in muscles
                for attachment_id in muscle.get("insertion", [])
                if attachment_id in attachment_ids
            ),
        ),
        CsvArtifact(
            filename="rels_muscle_antagonist_muscle.csv",
            headers=[":START_ID(Muscle)", ":END_ID(Muscle)", ":TYPE"],
            rows=antagonist_muscle_rows,
        ),
        CsvArtifact(
            filename="rels_muscle_antagonist_head.csv",
            headers=[":START_ID(Muscle)", ":END_ID(MuscleHead)", ":TYPE"],
            rows=antagonist_head_rows,
        ),
        CsvArtifact(
            filename="rels_head_origin.csv",
            headers=[":START_ID(MuscleHead)", ":END_ID(AttachmentPoint)", ":TYPE"],
            rows=list(
                {
                    ":START_ID(MuscleHead)": head["id"],
                    ":END_ID(AttachmentPoint)": origin_id,
                    ":TYPE": "ORIGINATES_AT",
                }
                for head in muscle_heads
                for origin_id in head.get("origin", [])
                if origin_id in attachment_ids
            ),
        ),
        CsvArtifact(
            filename="rels_head_innervation.csv",
            headers=[":START_ID(MuscleHead)", ":END_ID(Nerve)", ":TYPE"],
            rows=list(
                {
                    ":START_ID(MuscleHead)": head["id"],
                    ":END_ID(Nerve)": nerve_id,
                    ":TYPE": "INNERVATED_BY",
                }
                for head in muscle_heads
                for nerve_id in head.get("innervation", [])
            ),
        ),
        CsvArtifact(
            filename="rels_head_artery.csv",
            headers=[":START_ID(MuscleHead)", ":END_ID(Artery)", ":TYPE"],
            rows=list(
                {
                    ":START_ID(MuscleHead)": head["id"],
                    ":END_ID(Artery)": artery_id,
                    ":TYPE": "SUPPLIED_BY",
                }
                for head in muscle_heads
                for artery_id in head.get("arteries", [])
            ),
        ),
        CsvArtifact(
            filename="rels_nerve_targets_muscle.csv",
            headers=[":START_ID(Nerve)", ":END_ID(Muscle)", ":TYPE"],
            rows=nerve_muscle_rows,
        ),
        CsvArtifact(
            filename="rels_nerve_targets_head.csv",
            headers=[":START_ID(Nerve)", ":END_ID(MuscleHead)", ":TYPE"],
            rows=nerve_head_rows,
        ),
        CsvArtifact(
            filename="rels_artery_supplies_muscle.csv",
            headers=[":START_ID(Artery)", ":END_ID(Muscle)", ":TYPE"],
            rows=artery_muscle_rows,
        ),
        CsvArtifact(
            filename="rels_artery_supplies_head.csv",
            headers=[":START_ID(Artery)", ":END_ID(MuscleHead)", ":TYPE"],
            rows=artery_head_rows,
        ),
        CsvArtifact(
            filename="rels_artery_branches.csv",
            headers=[":START_ID(Artery)", ":END_ID(Artery)", ":TYPE"],
            rows=list(
                {
                    ":START_ID(Artery)": artery["id"],
                    ":END_ID(Artery)": artery.get("branches_from"),
                    ":TYPE": "BRANCHES_FROM",
                }
                for artery in arteries
                if artery.get("branches_from") in artery_ids
            ),
        ),
        CsvArtifact(
            filename="rels_action_primary_muscle.csv",
            headers=[":START_ID(Action)", ":END_ID(Muscle)", ":TYPE"],
            rows=action_muscle_rows,
        ),
        CsvArtifact(
            filename="rels_action_primary_head.csv",
            headers=[":START_ID(Action)", ":END_ID(MuscleHead)", ":TYPE"],
            rows=action_head_rows,
        ),
    ]


def build_all_artifacts(region: AnatomyRegion) -> List[CsvArtifact]:
    return [*build_node_artifacts(region), *build_relationship_artifacts(region)]


@dataclass
class NodePayload:
    label: str
    id: str
    properties: Dict[str, object]


@dataclass
class RelationshipPayload:
    type: str
    start_label: str
    start_id: str
    end_label: str
    end_id: str
    properties: Dict[str, object]


def build_node_payloads(region: AnatomyRegion) -> List[NodePayload]:
    nodes: List[NodePayload] = []

    for bone in region.require("bones").items:
        nodes.append(
            NodePayload(
                label="Bone",
                id=bone["id"],
                properties={
                    "name": bone.get("name", ""),
                    "region": bone.get("region", region.region),
                    "region_slug": region.region,
                    "payload": _dump_payload(bone),
                },
            )
        )

    for ap in region.require("attachment_points").items:
        nodes.append(
            NodePayload(
                label="AttachmentPoint",
                id=ap["id"],
                properties={
                    "name": ap.get("name", ""),
                    "structure": ap.get("bone", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(ap),
                },
            )
        )

    for muscle in region.require("muscles").items:
        nodes.append(
            NodePayload(
                label="Muscle",
                id=muscle["id"],
                properties={
                    "name": muscle.get("name", ""),
                    "group": muscle.get("group", ""),
                    "order": muscle.get("order", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(muscle),
                },
            )
        )

    for head in region.require("muscle_heads").items:
        nodes.append(
            NodePayload(
                label="MuscleHead",
                id=head["id"],
                properties={
                    "name": head.get("name", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(head),
                },
            )
        )

    for nerve in region.require("nerves").items:
        nodes.append(
            NodePayload(
                label="Nerve",
                id=nerve["id"],
                properties={
                    "name": nerve.get("name", ""),
                    "derivations": nerve.get("derivations", []),
                    "types": nerve.get("type", []),
                    "pathway": nerve.get("pathway", ""),
                    "clinical": nerve.get("clinical_significance", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(nerve),
                },
            )
        )

    for artery in region.require("arteries").items:
        nodes.append(
            NodePayload(
                label="Artery",
                id=artery["id"],
                properties={
                    "name": artery.get("name", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(artery),
                },
            )
        )

    for action in region.require("actions").items:
        nodes.append(
            NodePayload(
                label="Action",
                id=action["id"],
                properties={
                    "name": action.get("name", ""),
                    "joint": action.get("joint", ""),
                    "movement_type": action.get("type", ""),
                    "region_slug": region.region,
                    "payload": _dump_payload(action),
                },
            )
        )

    return nodes


def build_relationship_payloads(region: AnatomyRegion) -> List[RelationshipPayload]:
    relationships: List[RelationshipPayload] = []

    attachment_ids = {item["id"] for item in region.require("attachment_points").items}
    muscle_ids = {item["id"] for item in region.require("muscles").items}
    muscle_head_ids = {item["id"] for item in region.require("muscle_heads").items}
    artery_ids = {item["id"] for item in region.require("arteries").items}
    nerve_ids = {item["id"] for item in region.require("nerves").items}

    contractile_ids = muscle_ids | muscle_head_ids

    for bone in region.require("bones").items:
        for attachment in bone.get("attachments", []):
            if attachment in attachment_ids:
                relationships.append(
                    RelationshipPayload(
                        type="HAS_ATTACHMENT",
                        start_label="Bone",
                        start_id=bone["id"],
                        end_label="AttachmentPoint",
                        end_id=attachment,
                        properties={},
                    )
                )

    for muscle in region.require("muscles").items:
        for head_id in muscle.get("heads", []):
            if head_id in muscle_head_ids:
                relationships.append(
                    RelationshipPayload(
                        type="HAS_HEAD",
                        start_label="Muscle",
                        start_id=muscle["id"],
                        end_label="MuscleHead",
                        end_id=head_id,
                        properties={},
                    )
                )

        for insertion in muscle.get("insertion", []):
            if insertion in attachment_ids:
                relationships.append(
                    RelationshipPayload(
                        type="INSERTS_AT",
                        start_label="Muscle",
                        start_id=muscle["id"],
                        end_label="AttachmentPoint",
                        end_id=insertion,
                        properties={},
                    )
                )

        for antagonist in muscle.get("antagonists", []):
            if antagonist in muscle_ids:
                end_label = "Muscle"
            elif antagonist in muscle_head_ids:
                end_label = "MuscleHead"
            else:
                continue
            relationships.append(
                RelationshipPayload(
                    type="ANTAGONIST",
                    start_label="Muscle",
                    start_id=muscle["id"],
                    end_label=end_label,
                    end_id=antagonist,
                    properties={},
                )
            )

    for head in region.require("muscle_heads").items:
        for origin in head.get("origin", []):
            if origin in attachment_ids:
                relationships.append(
                    RelationshipPayload(
                        type="ORIGINATES_AT",
                        start_label="MuscleHead",
                        start_id=head["id"],
                        end_label="AttachmentPoint",
                        end_id=origin,
                        properties={},
                    )
                )

        for nerve in head.get("innervation", []):
            if nerve in nerve_ids:
                relationships.append(
                    RelationshipPayload(
                        type="INNERVATED_BY",
                        start_label="MuscleHead",
                        start_id=head["id"],
                        end_label="Nerve",
                        end_id=nerve,
                        properties={},
                    )
                )

        for artery in head.get("arteries", []):
            if artery in artery_ids:
                relationships.append(
                    RelationshipPayload(
                        type="SUPPLIED_BY",
                        start_label="MuscleHead",
                        start_id=head["id"],
                        end_label="Artery",
                        end_id=artery,
                        properties={},
                    )
                )

    for nerve in region.require("nerves").items:
        for target in nerve.get("innervates", []):
            if target in muscle_ids:
                end_label = "Muscle"
            elif target in muscle_head_ids:
                end_label = "MuscleHead"
            else:
                continue
            relationships.append(
                RelationshipPayload(
                    type="INNERVATES",
                    start_label="Nerve",
                    start_id=nerve["id"],
                    end_label=end_label,
                    end_id=target,
                    properties={},
                )
            )

    for artery in region.require("arteries").items:
        if artery.get("branches_from") in artery_ids:
            relationships.append(
                RelationshipPayload(
                    type="BRANCHES_FROM",
                    start_label="Artery",
                    start_id=artery["id"],
                    end_label="Artery",
                    end_id=artery["branches_from"],
                    properties={},
                )
            )

        for target in artery.get("supplies", []):
            if target in muscle_ids:
                end_label = "Muscle"
            elif target in muscle_head_ids:
                end_label = "MuscleHead"
            else:
                continue
            relationships.append(
                RelationshipPayload(
                    type="SUPPLIES",
                    start_label="Artery",
                    start_id=artery["id"],
                    end_label=end_label,
                    end_id=target,
                    properties={},
                )
            )

    for action in region.require("actions").items:
        for mover in action.get("primary_movers", []):
            if mover in muscle_ids:
                end_label = "Muscle"
            elif mover in muscle_head_ids:
                end_label = "MuscleHead"
            else:
                continue
            relationships.append(
                RelationshipPayload(
                    type="PRIMARY_MOVER",
                    start_label="Action",
                    start_id=action["id"],
                    end_label=end_label,
                    end_id=mover,
                    properties={},
                )
            )

    return relationships
