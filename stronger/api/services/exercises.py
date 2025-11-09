"""Exercise-facing service helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Set

from stronger.domain.exercises import (
    EquipmentItem,
    EquipmentSelection,
    ExerciseDataset,
    ExerciseTemplate,
    ExerciseVariant,
    MuscleAlias,
    Taxonomy,
    TaxonomyEntry,
    build_exercise_dataset,
)


class ExerciseService:
    """Caches the parsed exercise dataset and exposes query helpers."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root
        self._cache: ExerciseDataset | None = None
        self._alias_index: Dict[str, MuscleAlias] | None = None

    def _dataset(self) -> ExerciseDataset:
        if self._cache is None:
            self._cache = build_exercise_dataset(self._root)
        return self._cache

    def _aliases(self) -> Dict[str, MuscleAlias]:
        if self._alias_index is None:
            self._alias_index = {alias.alias: alias for alias in self._dataset().muscle_aliases}
        return self._alias_index

    def list_taxonomy_keys(self) -> Sequence[str]:
        return [taxonomy.key for taxonomy in self._dataset().taxonomies]

    def get_taxonomy(self, key: str) -> Taxonomy:
        return self._dataset().taxonomy(key)

    def list_templates(self) -> Sequence[ExerciseTemplate]:
        return self._dataset().templates

    def list_variants(self, *, body_region: str | None = None) -> Sequence[ExerciseVariant]:
        variants = self._dataset().variants
        if body_region:
            body_region = body_region.lower()
            variants = [variant for variant in variants if variant.body_region.lower() == body_region]
        return variants

    def get_variant(self, exercise_id: str) -> ExerciseVariant:
        exercise_id = exercise_id.lower()
        for variant in self._dataset().variants:
            if variant.id.lower() == exercise_id:
                return variant
        raise KeyError(f"Exercise '{exercise_id}' not found.")

    def list_equipment(self) -> Sequence[EquipmentItem]:
        return self._dataset().equipment

    def get_equipment(self, equipment_id: str) -> EquipmentItem:
        eq_key = equipment_id.lower()
        for item in self.list_equipment():
            if item.id.lower() == eq_key:
                return item
        raise KeyError(f"Equipment '{equipment_id}' not found.")

    def list_muscle_aliases(self) -> Sequence[MuscleAlias]:
        return self._dataset().muscle_aliases

    def get_muscle_alias(self, alias: str) -> MuscleAlias:
        alias_key = alias.lower()
        match = self._aliases().get(alias_key)
        if not match:
            raise KeyError(f"Muscle alias '{alias}' not found.")
        return match

    def list_muscle_groups(self) -> Sequence[TaxonomyEntry]:
        taxonomy = self.get_taxonomy("muscle_groups")
        return taxonomy.entries

    def get_muscle_group(self, group_id: str) -> TaxonomyEntry:
        key = group_id.lower()
        for entry in self.list_muscle_groups():
            if entry.id.lower() == key:
                return entry
        raise KeyError(f"Muscle group '{group_id}' not found.")

    def _variant_aliases(self, variant: ExerciseVariant) -> Set[str]:
        aliases: Set[str] = set()
        for role_list in (variant.muscles.prime, variant.muscles.secondary, variant.muscles.tertiary):
            for alias in role_list:
                if alias:
                    aliases.add(alias.lower())
        return aliases

    def muscles_for_group(self, group_id: str) -> Sequence[MuscleAlias]:
        group = self.get_muscle_group(group_id)
        group_key = group.id.lower()
        aliases: Set[str] = set()
        for variant in self._dataset().variants:
            target = (variant.target_muscle_group or "").lower()
            if target == group_key:
                aliases.update(self._variant_aliases(variant))
        alias_index = self._aliases()
        resolved: List[MuscleAlias] = []
        for alias in sorted(aliases):
            resolved.append(alias_index.get(alias, MuscleAlias(alias=alias, name=None, targets=[])))
        return resolved

    def variants_for_muscle_group(self, group_id: str) -> Sequence[ExerciseVariant]:
        key = self.get_muscle_group(group_id).id.lower()
        return [
            variant
            for variant in self._dataset().variants
            if (variant.target_muscle_group or "").lower() == key
        ]

    def variants_for_muscle(self, alias: str) -> Sequence[ExerciseVariant]:
        alias_key = self.get_muscle_alias(alias).alias
        return [variant for variant in self._dataset().variants if alias_key in self._variant_aliases(variant)]

    def equipment_for_variant(self, exercise_id: str) -> EquipmentSelection:
        variant = self.get_variant(exercise_id)
        return variant.equipment

    def variants_for_equipment(self, equipment_id: str) -> Sequence[ExerciseVariant]:
        eq_key = self.get_equipment(equipment_id).id.lower()
        results: List[ExerciseVariant] = []
        for variant in self._dataset().variants:
            equipment = [*(item.lower() for item in variant.equipment.primary), *(item.lower() for item in variant.equipment.secondary)]
            if eq_key in equipment:
                results.append(variant)
        return results
