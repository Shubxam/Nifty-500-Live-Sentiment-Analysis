# Agent Instructions

## Package Manager
Use **uv**: `uv sync`, `uv run <command>`, `uv add <package>`
Bootstrap project with `make dev-setup`.

## Commit Attribution
AI commits MUST include:
```
Co-Authored-By: Claude Sonnet 4 <noreply@example.com>
```

## File-Scoped Commands
| Task | Command |
|------|---------|
| Lint | `uv run ruff check path/to/file.py` |
| Format | `uv run ruff format path/to/file.py` |
| Typecheck | `uv run ty check path/to/file.py` |
| Test | `uv run pytest path/to/file_test.py` |

## Project-Wide Commands
| Task | Command |
|------|---------|
| Run Main | `make run` |
| Dashboard | `make dashboard` |
| Full Check | `make check` |
| Tests | `make test` |

## Architecture & Conventions
- **Database**: Local persistent `duckdb`.
- **Typing**: The project uses `ty` as its typechecker frontend (`uv run ty check`).
- **Formatting**: `ruff` is configured for single-quote strings and space indentation.
