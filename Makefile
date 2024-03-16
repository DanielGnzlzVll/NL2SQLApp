PROFILE ?= dev
SERVICE ?= console
DOCKER_RUN_ARGS ?= --service-ports --rm

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: up
up: export DJANGO_SETTINGS_MODULE ?= project.settings
up: ## Run the container and jump into a
	@docker compose --profile ${PROFILE} run ${DOCKER_RUN_ARGS} ${SERVICE} ${COMMAND}

.PHONY: test
test: ## run the tests
test: COMMAND = pytest
test: up

.PHONY: runserver
runserver: ## run the develoment web server
runserver: COMMAND = python manage.py runserver 0.0.0.0:8000
runserver: up

.PHONY: stop
stop: ## stop Docker containers without removing them
	@docker compose stop || true

.PHONY: start
start: ## setup the dabase and download the models.
start: COMMAND = python manage.py migrate --no-input
start: up
start: COMMAND = python manage.py pull_models
start: up

.PHONY: down
down: ## Stop and remove all the containers
	@docker compose down --remove-orphans


.PHONY: build
build: ## Build the container using cache
	@docker compose build ${SERVICE}


.PHONY: build-no-cache
build-no-cache: ## Build the container without use cache
	@docker compose build --no-cache ${SERVICE}
