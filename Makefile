all: wordlists dump_vecs dump_hints

wordlists:
	@cd scripts && ./download-wordlists.sh

dump_vecs:
	@poetry run python scripts/dump-vecs.py

dump_hints:
	@poetry run python scripts/dump-hints.py

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
