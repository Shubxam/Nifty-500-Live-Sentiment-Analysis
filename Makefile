# Makefile for easy development workflows.
# GitHub Actions call uv directly.

.DEFAULT_GOAL := default

.PHONY: default run dashboard install install-dev lint test upgrade clean

default: install lint test

run:
	uv run ./src/main.py

dashboard:
	uv run ./src/dashboard-generation.py

install:
	uv sync

install-dev:
	uv sync --all-extras --dev

lint:
	uv run python devtools/lint.py

test:
	uv run pytest

upgrade:
	uv sync --upgrade

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .mypy_cache/
	-rm -rf .venv/
	-find . -type d -name "__pycache__" -exec rm -rf {} +