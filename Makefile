all: wordlists prepare_database

wordlists:
	@cd scripts && ./download-wordlists.sh

prepare_database:
	@poetry run python scripts/dump.py

clean:
	rm word2vec.db*
	rm hints.json
	rm nearest.pickle

lint:
	@poetry run flake8 scripts src

server:
	@poetry run python -m semantle_slack_bot.app

test:
	@poetry run pytest tests

shell:
	@poetry run ipython
