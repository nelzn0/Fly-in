MAP_FILE 	?= maps/easy/01_linear_path.txt
PYTHON		= @uv run python

.PHONY: install run debug clean lint lint-strict

install:
	@uv sync

run:
	$(PYTHON) main.py $(MAP_FILE)

debug:
	$(PYTHON) -m pdb main.py $(MAP_FILE)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache

lint:
	@uv run flake8 .
	@uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@uv run flake8 .
	@uv run mypy . --strict