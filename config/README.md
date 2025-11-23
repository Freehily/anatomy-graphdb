# Anatomy Config Layout

- `index.yaml` maps section names to filenames so loaders know which YAML to read.
- `body/` contains shared lookup tables such as `muscle_groups.yaml` (group -> category), `muscle_regions.yaml`, and `muscles.yml` used by relational services.
- `global/` stores anatomy entities that are reused across multiple regions (e.g., shared attachment points).
- `<category>/<muscle_group>/` directories (e.g., `upper_body/chest/`, `lower_body/quads/`) contain muscle-group-scoped YAML for bones, muscles, nerves, arteries, etc.
- Muscle-group folders are the canonical source; export/validation runs directly against them.
