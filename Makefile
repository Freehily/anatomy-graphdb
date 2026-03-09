ifneq (,$(wildcard .env))
include .env
export
endif

REGION ?= all
DB_NAME ?= $(if $(NEO4J_DATABASE),$(NEO4J_DATABASE),neo4j)
NEO4J_AUTH ?= neo4j/stronger
NEO4J_URI ?= bolt://localhost:7687
POETRY ?= poetry
ANATOMY_CLI ?= $(POETRY) run anatomy-graphdb
NEO4J_USERNAME ?= $(word 1,$(subst /, ,$(NEO4J_AUTH)))
NEO4J_PASSWORD ?= $(word 2,$(subst /, ,$(NEO4J_AUTH)))

PROJECT_ROOT := $(CURDIR)
DATA_ROOT := $(PROJECT_ROOT)/data/neo4j
IMPORT_DIR := $(DATA_ROOT)/$(REGION)

.PHONY: neo4j-refresh export-catalog

neo4j-refresh:
	rm -rf $(DATA_ROOT)
	mkdir -p $(DATA_ROOT)
	$(ANATOMY_CLI) \
		--region $(REGION) \
		--output $(DATA_ROOT) \
		--mode bolt \
		--neo4j-uri $(NEO4J_URI) \
		--neo4j-username $(NEO4J_USERNAME) \
		--neo4j-password $(NEO4J_PASSWORD) \
		--neo4j-database $(DB_NAME) \
		--wipe-database \
		--validate

export-catalog:
	$(ANATOMY_CLI) --export-catalog --region $(REGION) --catalog-output $(PROJECT_ROOT)/data/catalog/anatomy_catalog.json
