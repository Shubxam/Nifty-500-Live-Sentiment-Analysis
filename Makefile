# Makefile for easy development workflows.
# GitHub Actions call uv directly.

.DEFAULT_GOAL := default

.PHONY: default run dashboard install dev-setup lint test upgrade clean check

default: install lint test

run:
	uv run src/main.py

dashboard:
	uv run src/dashboard-generation.py

install:
	uv sync

dev-setup: install
	uv sync --all-extras --dev
	uv run pre-commit install
	@echo "Development environment ready!"

lint:
	uv run src/devtools/lint.py

check:
	uv run ruff check src/*.py
	uv run ruff format src/*.py --check
	uv run ty check src/*.py

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
