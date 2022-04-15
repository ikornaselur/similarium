all: wordlists dump_vecs

wordlists:
	@cd scripts && ./download-wordlists.sh

dump_vecs:
	@poetry run python scripts/dump-vecs.py

dump_hints:
	@poetry run python scripts/dump-hints.py

lint:
	@poetry run flake8 scripts src
