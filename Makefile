# Makefile for easy development workflows.
# GitHub Actions call uv directly.

.DEFAULT_GOAL := default

.PHONY: default run dashboard install dev-setup lint test upgrade clean check

default: install lint test

run:
	uv run -m nifty_analyzer

dashboard:
	uv run -m nifty_analyzer.app.dashboard

install:
	uv sync

dev-setup: install
	uv sync --all-extras --dev
# 	uv run pre-commit install
	uv pip install -e .
	@echo "Development environment ready!"

lint:
	uv run devtools/lint.py

check:
	uv run ruff check src/nifty_analyzer
	uv run ruff format src/nifty_analyzer --check
	uv run ty check src/nifty_analyzer

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
	-rm -rf .ruff_cache/
