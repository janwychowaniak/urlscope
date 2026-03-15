# Repository Guidelines

## Project Structure & Module Organization

This repository uses a `src/` layout for the `urlscope` Python package. Library code lives in `src/urlscope/`, with internal modules such as `_exceptions.py` and `_http.py`. Reserve `src/urlscope/models/` for Pydantic response models. Put tests in `tests/`. Product requirements, contracts, and task sequencing live under `specs/001-urlscan-api-wrapper/`; treat those files as the source of truth before changing public behavior.

## Build, Test, and Development Commands

Use the managed virtual environment:

```bash
uv sync --extra dev
.venv/bin/python -c "import urlscope"
.venv/bin/pytest tests/
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/
```

`uv sync --extra dev` installs runtime and dev dependencies into `.venv`. The import check confirms packaging works. Run `pytest` for tests, `ruff` for linting, and `mypy` in strict mode before opening a PR.

## Coding Style & Naming Conventions

Target Python 3.10+ and keep type annotations complete. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `_`-prefixed module names for internal implementation details. Keep public exports centralized in `src/urlscope/__init__.py`. Follow the contract docs when naming API-facing classes and exceptions.

## Testing Guidelines

Use `pytest`, `pytest-asyncio`, and `respx` for async and HTTP transport tests. Name files by feature area, for example `tests/test_auth.py` or `tests/test_retry.py`. The spec requires full public API coverage, so add direct tests for every exported method, exception mapping, and retry/auth edge case.

## Commit & Pull Request Guidelines

Write short, imperative commit subjects such as `Add HTTP transport retry handling`. Keep commits scoped to a single task or coherent change. PRs should include a concise summary, references to the relevant spec or task IDs, and the exact verification commands you ran.

## Security & Configuration Tips

Never commit real API keys. Use `URLSCAN_API_KEY` for local development or pass credentials explicitly at runtime. Keep fixtures and examples sanitized, and avoid checking in captured scan artifacts or sensitive response payloads.
