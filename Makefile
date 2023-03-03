SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

export PROJECT=perfana-kedro/src

targets: help

check: ## Check the code base
	black ./$(PROJECT) --check --diff
	isort ./$(PROJECT) --check --diff
	autoflake ./$(PROJECT) --check-diff --recursive
	mypy ./$(PROJECT)

lint: ## Check the code base, and fix it
	black ./$(PROJECT)
	isort ./$(PROJECT)
	autoflake ./$(PROJECT) --recursive
	mypy ./$(PROJECT)

cleantest:  ## Clean up test containers
	$(ci-docker-compose) build
	$(ci-docker-compose) down --remove-orphans

# Makefile
pre-commit:
	cd perfana-kedro && pre-commit run --files ./*

pre-commit-install:
	cd perfana-kedro && pre-commit install

## Migrations

migrations: ## Generate a migration using alembic
ifeq ($(m),)
	@echo "Specify a message with m={message} and a rev-id with revid={revid} (e.g. 0001 etc.)"; exit 1
else ifeq ($(revid),)
	@echo "Specify a message with m={message} and a rev-id with revid={revid} (e.g. 0001 etc.)"; exit 1
else
	docker-compose run api alembic revision --autogenerate -m "$(m)" --rev-id="$(revid)"
endif

migrate: ## Run migrations upgrade using alembic
	docker-compose run --rm api alembic upgrade head

downgrade: ## Run migrations downgrade using alembic
	docker-compose run --rm api alembic downgrade -1

help: ## Display this help message
	@awk -F '##' '/^[a-z_]+:[a-z ]+##/ { print "\033[34m"$$1"\033[0m" "\n" $$2 }' Makefile
