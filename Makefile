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

clean:
	rm word2vec.db*
	rm hints.json
	rm nearest.pickle

lint:
	@poetry run flake8 scripts src

pyright:
	@poetry run pyright scripts src

server:
	@poetry run python -m similarium.app

test:
	@SLACK_BOT_TOKEN=xoxb-123123 \
		SLACK_APP_TOKEN=xapp-456456 \
		poetry run pytest tests -vvs

shell:
	@poetry run python scripts/shell.py
