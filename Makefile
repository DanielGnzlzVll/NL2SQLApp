PROFILE ?= dev
SERVICE ?= console
DOCKER_RUN_ARGS ?= --service-ports --rm

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: up
up: export DJANGO_SETTINGS_MODULE ?= project.settings
up: ## Run the container and jump into a
	@docker compose run ${DOCKER_RUN_ARGS} ${SERVICE} ${COMMAND}

.PHONY: test
test: ## run the tests
test: COMMAND = pytest
test: up

.PHONY: test-circleci
test-circleci: ## run the tests and collect results
test-circleci: COMMAND = pytest --junitxml=test-results/junit.xml
test-circleci: SERVICE = circle_ci_console
test-circleci:
	@docker compose run --name nl2sqlapp_console ${SERVICE} ${COMMAND} || true
	@docker cp nl2sqlapp_console:/app/test-results/ test-results/

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
