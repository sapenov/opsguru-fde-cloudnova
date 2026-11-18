PYTHON ?= python3

.PHONY: all setup test format format-check lint typecheck demo demo-check help

# Run the same checks as CI without modifying the working tree.
all: test lint format-check typecheck demo-check

setup:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m unittest discover -s evals -v
	$(PYTHON) -m unittest discover -s tests -v

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m pylint --persistent=no --fail-under=8.0 --fail-on=E,F app evals tests

typecheck:
	$(PYTHON) -m pyright --warnings

demo:
	$(PYTHON) -m app

demo-check:
	$(PYTHON) -m app > /dev/null

help:
	@printf '%s\n' \
	  'make setup         Install pinned development tools' \
	  'make test          Run evaluations and unit tests' \
	  'make format        Apply Ruff fixes and formatting' \
	  'make format-check  Check formatting without changes' \
	  'make lint          Run Ruff and Pylint' \
	  'make typecheck     Run Pyright' \
	  'make demo          Run the six-question demo' \
	  'make all           Run all checks without changing files'
