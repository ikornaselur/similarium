########
# Data #
########
all: wordlists create_db_tables prepare_data

wordlists:
	@cd scripts && ./download-wordlists.sh

create_db_tables:
	@poetry run python scripts/create_db.py

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
ifndef MSG
$(error MSG env var needs to be set to migration message)
endif
	@poetry run alembic revision --autogenerate -m "${MSG}"
	
