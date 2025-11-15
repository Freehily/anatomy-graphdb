# Anatomy Config Layout

- `index.yaml` maps section names to filenames so loaders know which YAML to read.
- `body/` contains shared lookup tables such as `muscle_groups.yaml`, `muscle_regions.yaml`, and `muscles.yml` used by relational services.
- `global/` stores anatomy entities that are reused across multiple regions (e.g., shared attachment points).
- `<region>/` directories (e.g., `upper_limb/`, `thorax/`) contain the region-specific YAML for bones, muscles, nerves, arteries, etc.
