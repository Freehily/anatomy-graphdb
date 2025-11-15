# Exercise Database Toolkit

This package mirrors the anatomy dataset but focuses on training movements.
Everything is rooted at `configs/index.yaml`, which describes four building
blocks:

1. **Taxonomies** – re-usable vocabularies (levels, mechanics, force types,
   movement patterns, planes, body regions, postures, grips, cadence, etc.)
   stored under `configs/taxonomies/`.
2. **Equipment** – hierarchical definitions under `configs/equipment/`.
3. **Muscle groups & anatomy aliases** – bridge high-level muscle buckets and
   anatomy IDs (`configs/muscle_groups/`, `configs/anatomy/`).
4. **Exercises** – canonical templates plus four region-sharded variant files in
   `configs/exercises/`.

## Regenerating configs

The raw source lives at `data/exercise_data_raw.csv`. Rebuild templates and all
region files with:

```
poetry run python stronger/databases/exercises/scripts/build_dataset.py
```

Flags:

- `--csv <path>` to read an alternate export.
- `--limit N` to process only the first `N` rows while iterating.

Running the script will:

- Parse the CSV, normalise every taxonomy reference via the YAML vocabularies,
  and shard exercises into `core`, `upper_body`, `lower_body`, and `full_body`
  files.
- Generate `exercises/templates.yaml` with template aliases + variant IDs.
- Refresh `configs/anatomy/muscle_aliases.yaml` so every muscle name found in
  the CSV can be mapped to anatomy IDs.
- Emit lookup tables for equipment, movement patterns, and planes-of-motion so
  the Neo4j graph can build dedicated nodes/relationships for richer queries.

Treat the CSV as the source of truth—running the script overwrites existing
exercise files.

## Validating

Use the loader/validator before exporting to Neo4j or shipping a release:

```
poetry run python stronger/databases/exercises/scripts/validate_configs.py
```

The validator loads `index.yaml`, ensures every exercise references valid
taxonomies/equipment/templates, and reports any missing IDs. A passing run will
note how many exercises were parsed (currently 3,242).

You can also import `ExerciseLoader` directly:

```python
from stronger.databases.exercises.loader import ExerciseLoader

loader = ExerciseLoader()
loader.load()
errors = loader.validate()
assert not errors
```

## Next Steps

- Wire the exercise loader into the Neo4j build pipeline so exercises link to
  anatomy nodes (`muscles`, `movement_patterns`, `equipment`).
- Add round-trip tests to guard against taxonomy drift or accidental deletions.
