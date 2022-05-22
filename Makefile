VERSION := $(shell sed -n 's/^ *version.*=.*"\([^"]*\)".*/\1/p' pyproject.toml)
DOCKER_REPO = "absalon/similarium"

########
# Data #
########
all: wordlists init_db prepare_data

wordlists:
	@cd scripts && ./download-wordlists.sh

init_db:
	@poetry run alembic downgrade base
	@poetry run alembic upgrade head

prepare_data:
	@poetry run python scripts/dump.py

postgres:
	@docker run \
		--detach \
		--publish 127.0.0.1:5432:5432 \
		--env POSTGRES_PASSWORD=s3cr3t \
		--name postgres \
		postgres:14

########
# Lint #
########
lint:
	@poetry run flake8 scripts src

pyright:
	@poetry run pyright scripts src

##########
# Server #
##########
server:
	@poetry run python -m similarium.app

###########
# Testing #
###########
test:
	@SLACK_APP_TOKEN=xapp-456456 \
		SLACK_CLIENT_ID=123 \
		SLACK_CLIENT_SECRET=456 \
		SLACK_SIGNING_SECRET=789 \
		poetry run pytest tests -vvs

shell:
	@poetry run python scripts/shell.py
	
##############
# Migrations #
##############
upgrade:
	@poetry run alembic upgrade head

migrate:
	@[ "${MSG}" ] || ( echo ">> MSG env var needs to be set to the migration message"; exit 1 )
	@poetry run alembic revision --autogenerate -m "${MSG}"
	
##########
# Docker #
##########
docker_build_dev:
	@poetry export -E sqlite -E postgres -f requirements.txt > requirements.txt
	@docker build \
		-f docker/Dockerfile \
		-t $(DOCKER_REPO):latest-dev \
		.
	@rm requirements.txt

docker_run: docker_build_dev
	@docker run \
		-v "$(shell pwd)"/config.toml:/app/config.toml \
		-v "$(shell pwd)"/similarium.db:/app/similarium.db \
		--name similarium \
		--rm \
		$(DOCKER_REPO):latest-dev

docker_build_and_push:
	@poetry export -E sqlite -E postgres -f requirements.txt > requirements.txt
	@docker buildx build \
		--platform "linux/amd64,linux/arm64,linux/386,linux/arm/v7" \
		-f docker/Dockerfile \
		--push \
		-t $(DOCKER_REPO):$(VERSION) \
		-t $(DOCKER_REPO):latest \
		.
	@rm requirements.txt
