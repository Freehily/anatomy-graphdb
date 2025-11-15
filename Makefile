REGION ?= all
DB_NAME ?= neo4j
CONTAINER_NAME ?= stronger-neo4j
NEO4J_IMAGE ?= neo4j:5.25
NEO4J_AUTH ?= neo4j/stronger
HTTP_PORT ?= 7474
BOLT_PORT ?= 7687
POETRY ?= poetry
DOCKER ?= docker
ANATOMY_CLI ?= $(POETRY) run stronger-anatomy

PROJECT_ROOT := $(CURDIR)
DATA_ROOT := $(PROJECT_ROOT)/data/neo4j
IMPORT_DIR := $(DATA_ROOT)/$(REGION)
DB_DIR := $(PROJECT_ROOT)/neo4j-data
LOG_DIR := $(PROJECT_ROOT)/neo4j-logs

.PHONY: neo4j-refresh

neo4j-refresh:
	rm -rf $(DATA_ROOT)
	mkdir -p $(DATA_ROOT) $(DB_DIR) $(LOG_DIR)
	$(ANATOMY_CLI) \
		--region $(REGION) \
		--output $(DATA_ROOT) \
		--mode bolt \
		--wipe-database \
		--validate
