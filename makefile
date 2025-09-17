.PHONY: build
install:
	uv sync

.PHONY: run
run:
	uv run python src/server.py
