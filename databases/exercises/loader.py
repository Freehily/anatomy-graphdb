"""
Loader and validator for the exercise configuration set.

The loader understands `configs/index.yaml`, which enumerates every taxonomy,
equipment file, template file, and region-sharded exercise file. Consumers can
import this module to obtain normalized dictionaries or to run validation
before exporting to Neo4j.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

import yaml

CONFIG_ROOT = Path(__file__).resolve().parent / "configs"


class ExerciseConfigError(RuntimeError):
    """Raised when configs are missing or malformed."""


def _load_yaml(path: Path) -> MutableMapping[str, object]:
    if not path.exists():
        raise ExerciseConfigError(f"Missing config file: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, MutableMapping):
        raise ExerciseConfigError(f"{path} must contain a mapping at the top level.")
    return data


@dataclass
class TaxonomyEntry:
    id: str
    name: str
    description: str | None = None
    aliases: Sequence[str] | None = None


@dataclass
class EquipmentItem:
    id: str
    name: str
    parent_id: str | None = None


@dataclass
class ExerciseTemplate:
    id: str
    name: str
    aliases: Sequence[str]
    variants: Sequence[str]


@dataclass
class ExerciseVariant:
    id: str
    name: str
    body_region: str
    template: str
    raw: Mapping[str, object]


class ExerciseLoader:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or CONFIG_ROOT
        if not self.root.exists():
            raise ExerciseConfigError(f"Config root {self.root} does not exist.")
        self.index = _load_yaml(self.root / "index.yaml")
        self.taxonomies: Dict[str, Dict[str, TaxonomyEntry]] = {}
        self.taxonomy_aliases: Dict[str, Dict[str, str]] = {}
        self.templates: Dict[str, ExerciseTemplate] = {}
        self.equipment_items: Dict[str, EquipmentItem] = {}
        self.equipment_aliases: Dict[str, str] = {}
        self.exercise_variants: List[ExerciseVariant] = []
        self.muscle_aliases: Dict[str, List[Dict[str, str]]] = {}

    def load(self) -> None:
        self._load_taxonomies()
        self._load_equipment()
        self._load_muscle_aliases()
        self._load_templates()
        self._load_exercises()

    # -----------------------
    # Private helpers
    # -----------------------

    def _load_taxonomies(self) -> None:
        for key, rel_path in self.index.get("taxonomies", {}).items():
            self._ingest_taxonomy(key, self.root / rel_path)
        # muscle groups live outside the taxonomies block but behave the same
        muscle_def = self.index.get("muscle_groups", {}).get("definitions")
        if muscle_def:
            self._ingest_taxonomy("muscle_groups", self.root / muscle_def)

    def _ingest_taxonomy(self, key: str, path: Path) -> None:
        data = _load_yaml(path)
        section = next(iter(data))
        entries: List[TaxonomyEntry] = []
        alias_map: Dict[str, str] = {}
        for entry in data[section]:
            taxonomy_entry = TaxonomyEntry(
                id=entry["id"],
                name=entry["name"],
                description=entry.get("description"),
                aliases=entry.get("aliases"),
            )
            entries.append(taxonomy_entry)
            alias_map[taxonomy_entry.id] = taxonomy_entry.id
            alias_map[taxonomy_entry.name.lower()] = taxonomy_entry.id
            for alias in taxonomy_entry.aliases or []:
                alias_map[alias.lower()] = taxonomy_entry.id
        self.taxonomies[key] = {entry.id: entry for entry in entries}
        self.taxonomy_aliases[key] = alias_map

    def _load_equipment(self) -> None:
        equipment_files = self.index.get("equipment", {})
        items_path = self.root / equipment_files["items"]
        data = _load_yaml(items_path)
        canonical: Dict[str, EquipmentItem] = {}
        alias_map: Dict[str, str] = {}
        for entry in data.get("equipment", []):
            item = EquipmentItem(
                id=entry["id"],
                name=entry["name"],
                parent_id=entry.get("parent_id"),
            )
            canonical[item.id] = item
            alias_map[item.id] = item.id
            alias_map[item.name.lower()] = item.id
            for alias in entry.get("aliases", []) or []:
                alias_map[alias.lower()] = item.id
        self.equipment_items = canonical
        self.equipment_aliases = alias_map

    def _load_muscle_aliases(self) -> None:
        alias_config = self.index.get("anatomy_aliases", {}).get("muscles")
        if not alias_config:
            self.muscle_aliases = {}
            return
        path = self.root / alias_config
        data = _load_yaml(path)
        alias_map: Dict[str, List[Dict[str, str]]] = {}
        for entry in data.get("muscles", []):
            alias = entry.get("alias") or entry.get("id")
            targets = entry.get("targets", [])
            if not alias or not targets:
                continue
            alias_map[alias.lower()] = targets
        self.muscle_aliases = alias_map

    def _load_templates(self) -> None:
        templates_path = self.root / self.index["exercises"]["templates"]
        raw = _load_yaml(templates_path)
        for entry in raw.get("templates", []):
            self.templates[entry["id"]] = ExerciseTemplate(
                id=entry["id"],
                name=entry["name"],
                aliases=entry.get("aliases", []),
                variants=entry.get("variants", []),
            )

    def _load_exercises(self) -> None:
        variant_files = self.index["exercises"]["variants"]
        variants: List[ExerciseVariant] = []
        for rel_path in variant_files:
            path = self.root / rel_path
            data = _load_yaml(path)
            body_region = Path(rel_path).stem
            for entry in data.get("exercises", []):
                variants.append(
                    ExerciseVariant(
                        id=entry["id"],
                        name=entry["name"],
                        body_region=body_region,
                        template=entry["template"],
                        raw=entry,
                    )
                )
        self.exercise_variants = variants

    # -----------------------
    # Validation helpers
    # -----------------------

    def _resolve(self, taxonomy: str, value: str | None) -> bool:
        if not value:
            return True
        return value in self.taxonomies.get(taxonomy, {})

    def _validate_list(self, taxonomy: str, values: Iterable[str]) -> List[str]:
        missing = []
        for value in values:
            if value and not self._resolve(taxonomy, value):
                missing.append(value)
        return missing

    def validate(self) -> List[str]:
        errors: List[str] = []

        required_taxonomies = {
            "level": ("difficulty_levels", "level"),
            "body_region": ("body_regions", "body_region"),
            "force_type": ("force_types", "force_type"),
            "mechanics": ("mechanics", "mechanics"),
            "laterality": ("laterality", "laterality"),
            "classification": ("classifications", "classification"),
            "posture": ("postures", "posture"),
            "combination_type": ("combination_types", "combination_type"),
            "load_position": ("load_positions", "load_position"),
            "grip": ("grips", "grip"),
            "target_muscle_group": ("muscle_groups", "target_muscle_group"),
        }

        for variant in self.exercise_variants:
            payload = variant.raw
            if variant.template not in self.templates:
                errors.append(f"[template] Exercise '{variant.id}' references unknown template '{variant.template}'.")

            for field, (taxonomy_key, label) in required_taxonomies.items():
                value = payload.get(field)
                if isinstance(value, str) and not self._resolve(taxonomy_key, value):
                    errors.append(f"[{label}] Exercise '{variant.id}' uses unknown {label} '{value}'.")

            for taxonomy_key, values in (
                ("movement_patterns", payload.get("movement_patterns", [])),
                ("planes", payload.get("planes_of_motion", [])),
            ):
                missing = self._validate_list(taxonomy_key, values)
                if missing:
                    errors.append(
                        f"[{taxonomy_key}] Exercise '{variant.id}' references unknown value(s): {', '.join(missing)}"
                    )

            muscles_section = payload.get("muscles", {})
            for role in ("prime", "secondary", "tertiary"):
                for alias in muscles_section.get(role, []):
                    alias_key = alias.lower()
                    targets = self.muscle_aliases.get(alias_key)
                    if not targets:
                        errors.append(
                            f"[muscles] Exercise '{variant.id}' references unmapped alias '{alias}'."
                        )
                        continue
                    for target in targets:
                        if not target.get("id"):
                            errors.append(
                                f"[muscles] Alias '{alias}' for exercise '{variant.id}' is missing a target id."
                            )

            equipment_section = payload.get("equipment", {})
            for category in ("primary", "secondary"):
                for eq_id in equipment_section.get(category, []):
                    if eq_id not in self.equipment_items:
                        errors.append(f"[equipment] Exercise '{variant.id}' references undefined equipment '{eq_id}'.")

        return errors


def load_and_validate(root: Path | None = None) -> List[str]:
    loader = ExerciseLoader(root)
    loader.load()
    return loader.validate()
