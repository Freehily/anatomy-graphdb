REGION ?= all
DB_NAME ?= neo4j
CONTAINER_NAME ?= stronger-neo4j
NEO4J_IMAGE ?= neo4j:5.25
NEO4J_AUTH ?= neo4j/stronger
HTTP_PORT ?= 7474
BOLT_PORT ?= 7687
POETRY ?= poetry
DOCKER ?= docker

PROJECT_ROOT := $(CURDIR)
DATA_ROOT := $(PROJECT_ROOT)/data/neo4j
IMPORT_DIR := $(DATA_ROOT)/$(REGION)
DB_DIR := $(PROJECT_ROOT)/neo4j-data
LOG_DIR := $(PROJECT_ROOT)/neo4j-logs
BUILD_GRAPH_SCRIPT := stronger/databases/anatomy/scripts/build_graph.py

.PHONY: neo4j-refresh neo4j-export neo4j-import neo4j-run neo4j-stop

neo4j-refresh: neo4j-export neo4j-import neo4j-run

neo4j-export:
	rm -rf $(DATA_ROOT)
	mkdir -p $(DATA_ROOT) $(DB_DIR) $(LOG_DIR)
	$(POETRY) run python $(BUILD_GRAPH_SCRIPT) \
		--region $(REGION) \
		--output $(DATA_ROOT) \
		--validate

neo4j-import: neo4j-stop
	test -d "$(IMPORT_DIR)" || (echo "Missing CSV exports in $(IMPORT_DIR). Run 'make neo4j-export' first." && exit 1)
	$(DOCKER) run --rm \
		-v "$(IMPORT_DIR)":/import/data \
		-v "$(DB_DIR)":/data \
		-v "$(LOG_DIR)":/logs \
		$(NEO4J_IMAGE) \
		neo4j-admin database import full $(DB_NAME) \
			--overwrite-destination=true \
			--verbose \
			--nodes=Bone=/import/data/nodes_bones.csv \
			--nodes=AttachmentPoint=/import/data/nodes_attachment_points.csv \
			--nodes=Muscle=/import/data/nodes_muscles.csv \
			--nodes=MuscleHead=/import/data/nodes_muscle_heads.csv \
			--nodes=Nerve=/import/data/nodes_nerves.csv \
			--nodes=Artery=/import/data/nodes_arteries.csv \
			--nodes=Action=/import/data/nodes_actions.csv \
			--relationships=/import/data/rels_bone_attachment.csv \
			--relationships=/import/data/rels_muscle_head.csv \
			--relationships=/import/data/rels_muscle_insertion.csv \
			--relationships=/import/data/rels_muscle_antagonist_muscle.csv \
			--relationships=/import/data/rels_muscle_antagonist_head.csv \
			--relationships=/import/data/rels_head_origin.csv \
			--relationships=/import/data/rels_head_innervation.csv \
			--relationships=/import/data/rels_head_artery.csv \
			--relationships=/import/data/rels_nerve_targets_muscle.csv \
			--relationships=/import/data/rels_nerve_targets_head.csv \
			--relationships=/import/data/rels_artery_supplies_muscle.csv \
			--relationships=/import/data/rels_artery_supplies_head.csv \
			--relationships=/import/data/rels_artery_branches.csv \
			--relationships=/import/data/rels_action_primary_muscle.csv \
			--relationships=/import/data/rels_action_primary_head.csv

neo4j-run: neo4j-stop
	$(DOCKER) run -d \
		--name $(CONTAINER_NAME) \
		-p $(HTTP_PORT):7474 \
		-p $(BOLT_PORT):7687 \
		-e NEO4J_AUTH=$(NEO4J_AUTH) \
		-v "$(DB_DIR)":/data \
		-v "$(LOG_DIR)":/logs \
		$(NEO4J_IMAGE)
	@echo "Neo4j container '$(CONTAINER_NAME)' is starting on http://localhost:$(HTTP_PORT) (Bolt $(BOLT_PORT))."

neo4j-stop:
	-$(DOCKER) ps -q -f name="^$(CONTAINER_NAME)$$" | xargs -r $(DOCKER) stop
	-$(DOCKER) ps -aq -f name="^$(CONTAINER_NAME)$$" | xargs -r $(DOCKER) rm
