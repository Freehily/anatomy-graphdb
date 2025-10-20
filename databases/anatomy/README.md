# Anatomy Database Toolkit

This package contains YAML configs that describe anatomical structures, a validation helper, and tooling to export the data into a Neo4j property graph.

## Validation

Use the dedicated validators to check referential integrity:

- Upper limb:
  ```
  python stronger/databases/anatomy/scripts/validate_upper_limb.py
  ```
- Thorax:
  ```
  python stronger/databases/anatomy/scripts/validate_thorax.py
  ```
- Lower limb:
  ```
  python stronger/databases/anatomy/scripts/validate_lower_limb.py
  ```
- Back:
  ```
  python stronger/databases/anatomy/scripts/validate_back.py
  ```
- Pelvis:
  ```
  python stronger/databases/anatomy/scripts/validate_pelvis.py
  ```
- Head and neck:
  ```
  python stronger/databases/anatomy/scripts/validate_head_and_neck.py
  ```
- Hand:
  ```
  python stronger/databases/anatomy/scripts/validate_hand.py
  ```
- Foot:
  ```
  python stronger/databases/anatomy/scripts/validate_foot.py
  ```
- Abdomen:
  ```
  python stronger/databases/anatomy/scripts/validate_abdomen.py
  ```

Each script loads the region-specific YAML files and verifies that every attachment, muscle head, muscle, nerve, artery, and action reference resolves correctly. A non-zero exit code highlights missing or misspelled IDs.

## Neo4j Export Workflow

1. Generate CSV artifacts:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region upper_limb
   ```
   By default, files land in `data/neo4j/upper_limb`. Use `--output <dir>` to override.

   Thorax data can be exported by swapping the region flag:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region thorax
   ```
   which writes to `data/neo4j/thorax` unless a custom directory is provided.

   Lower limb data follows the same pattern:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region lower_limb
   ```
   generating CSVs under `data/neo4j/lower_limb` by default.

   Back data:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region back
   ```
   writes to `data/neo4j/back` unless another directory is supplied.

   Pelvis data:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region pelvis
   ```
   writes to `data/neo4j/pelvis` by default.

   Head and neck data:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region head_and_neck
   ```
   writes to `data/neo4j/head_and_neck` by default.

   Hand data:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region hand
   ```
   writes to `data/neo4j/hand` by default.

   Foot data:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region foot
   ```
   writes to `data/neo4j/foot` by default.

   Abdomen data:
   ```
   python stronger/databases/anatomy/scripts/export_upper_limb_neo4j.py --region abdomen
   ```
   writes to `data/neo4j/abdomen` by default.

2. Import into a local Neo4j instance (example commands):
   ```
   neo4j-admin database import full upper_limb \
     --nodes=data/neo4j/upper_limb/nodes_bones.csv \
     --nodes=data/neo4j/upper_limb/nodes_attachment_points.csv \
     --nodes=data/neo4j/upper_limb/nodes_muscles.csv \
     --nodes=data/neo4j/upper_limb/nodes_muscle_heads.csv \
     --nodes=data/neo4j/upper_limb/nodes_nerves.csv \
     --nodes=data/neo4j/upper_limb/nodes_arteries.csv \
     --nodes=data/neo4j/upper_limb/nodes_actions.csv \
     --relationships=data/neo4j/upper_limb/rels_bone_attachment.csv \
     --relationships=data/neo4j/upper_limb/rels_muscle_head.csv \
     --relationships=data/neo4j/upper_limb/rels_muscle_insertion.csv \
     --relationships=data/neo4j/upper_limb/rels_muscle_antagonist.csv \
     --relationships=data/neo4j/upper_limb/rels_head_origin.csv \
     --relationships=data/neo4j/upper_limb/rels_head_innervation.csv \
     --relationships=data/neo4j/upper_limb/rels_head_artery.csv \
     --relationships=data/neo4j/upper_limb/rels_nerve_targets.csv \
     --relationships=data/neo4j/upper_limb/rels_artery_supplies.csv \
     --relationships=data/neo4j/upper_limb/rels_artery_branches.csv \
     --relationships=data/neo4j/upper_limb/rels_action_primary.csv
   ```

3. Start Neo4j and run sanity checks. Example Cypher:
   ```
   MATCH (m:Muscle {id: 'flexor_digitorum_profundus'})-[:INSERTS_AT]->(ap)
   RETURN m.name, ap.name;
   ```

## Suggested Constraints

In the Neo4j browser or via `cypher-shell`, apply uniqueness and relationship guidance:

```
CREATE CONSTRAINT bone_id IF NOT EXISTS FOR (b:Bone) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT attach_id IF NOT EXISTS FOR (a:AttachmentPoint) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT muscle_id IF NOT EXISTS FOR (m:Muscle) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT head_id IF NOT EXISTS FOR (h:MuscleHead) REQUIRE h.id IS UNIQUE;
CREATE CONSTRAINT nerve_id IF NOT EXISTS FOR (n:Nerve) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT artery_id IF NOT EXISTS FOR (a:Artery) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE;
```

These constraints ensure imports remain idempotent and protect future updates.
