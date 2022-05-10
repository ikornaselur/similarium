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
	
