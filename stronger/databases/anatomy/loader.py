"""
Utilities for loading anatomy configuration data from YAML files.

The loader understands the repository layout:

```
configs/
    index.yaml        # maps logical sections -> filenames
    <region>/*.yaml   # region-specific definitions
    shared/*.yaml     # shared entities available to every region
```

The goal is to provide a reusable API that returns a structured view of
an anatomy region so that validation, CSV export, or direct Neo4j
ingestion can all share the same parsing logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

import yaml

_DEFAULT_ROOT = Path(__file__).resolve().parent / "configs"


class AnatomyConfigError(RuntimeError):
    """Raised when configuration files are missing or malformed."""


@dataclass
class SectionData:
    """Holds the merged data for a single configuration section."""

    name: str
    items: List[dict]

    def id_index(self, key: str = "id") -> Dict[str, dict]:
        return {item[key]: item for item in self.items if key in item}


@dataclass
class AnatomyRegion:
    """Structured view of all data for a single anatomy region."""

    region: str
    sections: Mapping[str, SectionData]

    def require(self, section: str) -> SectionData:
        try:
            return self.sections[section]
        except KeyError as exc:
            raise AnatomyConfigError(f"Section '{section}' not loaded for region '{self.region}'") from exc

    def ids(self, section: str, key: str = "id") -> Sequence[str]:
        return list(self.require(section).id_index(key))


def _load_yaml(path: Path) -> MutableMapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, MutableMapping):
        raise AnatomyConfigError(f"Expected mapping in {path}, found {type(data).__name__}")
    return data


def _merge_items(primary: Iterable[dict], supplemental: Iterable[dict], key: str) -> List[dict]:
    by_id: Dict[str, dict] = {}
    for item in primary:
        item_id = item.get(key)
        if item_id:
            by_id[item_id] = item
    for item in supplemental:
        item_id = item.get(key)
        if not item_id:
            continue
        # Region-specific items override shared definitions with the same ID.
        by_id[item_id] = item
    return list(by_id.values())


class AnatomyLoader:
    """Loads anatomy region data with optional shared definitions."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = root or _DEFAULT_ROOT
        if not self.root.exists():
            raise AnatomyConfigError(f"Configuration root '{self.root}' does not exist")
        self._index = self._load_index()

    def _load_index(self) -> Mapping[str, str]:
        index_path = self.root / "index.yaml"
        if not index_path.exists():
            raise AnatomyConfigError(f"Missing index file at {index_path}")
        data = _load_yaml(index_path)
        return {str(section): str(filename) for section, filename in data.items()}

    def available_regions(self) -> Sequence[str]:
        return sorted(
            entry.name for entry in self.root.iterdir() if entry.is_dir() and entry.name not in {"shared"}
        )

    def load_region(self, region: str, include_shared: bool = True) -> AnatomyRegion:
        region_dir = self.root / region
        if not region_dir.exists():
            raise AnatomyConfigError(f"Region '{region}' not found under {self.root}")

        sections: Dict[str, SectionData] = {}
        shared_dir = self.root / "shared"

        for section, filename in self._index.items():
            region_path = region_dir / filename
            shared_path = shared_dir / filename

            region_payload = []
            shared_payload = []

            if include_shared and shared_path.exists():
                data = _load_yaml(shared_path)
                shared_payload = self._filter_items_for_region(list(data.get(section, []) or []), region)

            if region_path.exists():
                data = _load_yaml(region_path)
                region_payload = self._filter_items_for_region(list(data.get(section, []) or []), region)
            elif not shared_payload:
                # No region- or shared-level file for a section listed in the index.
                raise AnatomyConfigError(
                    f"Missing configuration for section '{section}' in region '{region}' (expected {region_path})"
                )

            items = _merge_items(shared_payload, region_payload, key="id")
            sections[section] = SectionData(name=section, items=items)

        return AnatomyRegion(region=region, sections=sections)

    def load_regions(self, regions: Sequence[str], include_shared: bool = True) -> AnatomyRegion:
        if not regions:
            raise AnatomyConfigError("No regions provided.")
        combined: Dict[str, Dict[str, dict]] = {}
        normalised_regions = []
        for region_name in regions:
            region_name = region_name.strip()
            if not region_name:
                continue
            normalised_regions.append(region_name)
            region_data = self.load_region(region_name, include_shared=include_shared)
            for section, section_data in region_data.sections.items():
                bucket = combined.setdefault(section, {})
                for item in section_data.items:
                    item_id = item.get("id")
                    if not item_id:
                        continue
                    bucket.setdefault(item_id, item)
        if not normalised_regions:
            raise AnatomyConfigError("No valid regions provided.")
        merged_sections = {
            name: SectionData(name=name, items=list(items.values()))
            for name, items in combined.items()
        }
        merged_name = "all" if len(normalised_regions) > 1 else normalised_regions[0]
        return AnatomyRegion(region=merged_name, sections=merged_sections)

    def _filter_items_for_region(self, items: List[dict], region: str) -> List[dict]:
        filtered: List[dict] = []
        region_lower = region.lower()
        for item in items:
            allowed_regions = [value.lower() for value in item.get("regions", []) or []]
            excluded_regions = [value.lower() for value in item.get("exclude_regions", []) or []]
            include = True
            if allowed_regions:
                if region_lower not in allowed_regions and "all" not in allowed_regions and "global" not in allowed_regions:
                    include = False
            if include and excluded_regions:
                if region_lower in excluded_regions:
                    include = False
            if include:
                cleaned = dict(item)
                cleaned.pop("regions", None)
                cleaned.pop("exclude_regions", None)
                filtered.append(cleaned)
        return filtered


def load_region(region: str, *, root: Optional[Path] = None, include_shared: bool = True) -> AnatomyRegion:
    """Convenience function to load a region without instantiating the class."""

    loader = AnatomyLoader(root=root)
    return loader.load_region(region, include_shared=include_shared)
