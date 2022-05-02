all: wordlists create_db_tables prepare_data

wordlists:
	@cd scripts && ./download-wordlists.sh

create_db_tables:
	@poetry run python scripts/create_db.py

prepare_data:
	@poetry run python scripts/dump.py

clean:
	rm word2vec.db*
	rm hints.json
	rm nearest.pickle

lint:
	@poetry run flake8 scripts src

pyright:
	@poetry run pyright scripts src

server:
	@poetry run python -m semantle_slack_bot.app

test:
	@poetry run pytest tests -vvs

shell:
	@poetry run ipython
