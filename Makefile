REGION ?= all
DB_NAME ?= neo4j
CONTAINER_NAME ?= stronger-neo4j
NEO4J_IMAGE ?= neo4j:5.25
NEO4J_AUTH ?= neo4j/stronger
HTTP_PORT ?= 7474
BOLT_PORT ?= 7687
POETRY ?= poetry
DOCKER ?= docker
DOCKER_COMPOSE ?= $(DOCKER) compose
COMPOSE_FILE ?= docker-compose.yml
COMPOSE_PROJECT ?= anatomy-graphdb
ANATOMY_CLI ?= $(POETRY) run anatomy-graphdb
NEO4J_USERNAME ?= $(word 1,$(subst /, ,$(NEO4J_AUTH)))
NEO4J_PASSWORD ?= $(word 2,$(subst /, ,$(NEO4J_AUTH)))
NEO4J_URI ?= bolt://localhost:$(BOLT_PORT)

PROJECT_ROOT := $(CURDIR)
DATA_ROOT := $(PROJECT_ROOT)/data/neo4j
IMPORT_DIR := $(DATA_ROOT)/$(REGION)
DB_DIR := $(PROJECT_ROOT)/neo4j-data
LOG_DIR := $(PROJECT_ROOT)/neo4j-logs

.PHONY: neo4j-up neo4j-down neo4j-wait neo4j-logs neo4j-refresh neo4j-refresh-docker export-catalog

neo4j-up:
	mkdir -p $(DB_DIR) $(LOG_DIR)
	NEO4J_IMAGE=$(NEO4J_IMAGE) \
	NEO4J_AUTH=$(NEO4J_AUTH) \
	HTTP_PORT=$(HTTP_PORT) \
	BOLT_PORT=$(BOLT_PORT) \
	CONTAINER_NAME=$(CONTAINER_NAME) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT) up -d neo4j

neo4j-down:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT) down

neo4j-wait:
	@echo "Waiting for Neo4j to accept Bolt connections..."
	@attempts=0; \
	until $(DOCKER) exec $(CONTAINER_NAME) cypher-shell -u $(NEO4J_USERNAME) -p $(NEO4J_PASSWORD) "RETURN 1" >/dev/null 2>&1; do \
		attempts=$$((attempts + 1)); \
		if [ $$attempts -ge 60 ]; then \
			echo "Neo4j did not become ready in time."; \
			exit 1; \
		fi; \
		sleep 2; \
	done
	@echo "Neo4j is ready."

neo4j-logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) -p $(COMPOSE_PROJECT) logs -f neo4j

neo4j-refresh:
	rm -rf $(DATA_ROOT)
	mkdir -p $(DATA_ROOT) $(DB_DIR) $(LOG_DIR)
	$(ANATOMY_CLI) \
		--region $(REGION) \
		--output $(DATA_ROOT) \
		--mode bolt \
		--neo4j-uri $(NEO4J_URI) \
		--neo4j-username $(NEO4J_USERNAME) \
		--neo4j-password $(NEO4J_PASSWORD) \
		--wipe-database \
		--validate

neo4j-refresh-docker: neo4j-up neo4j-wait neo4j-refresh

export-catalog:
	$(ANATOMY_CLI) --export-catalog --region $(REGION) --catalog-output $(PROJECT_ROOT)/data/catalog/anatomy_catalog.json
