# Repository Guidelines

## Project Structure & Module Organization

This repository uses a `src/` layout for the `urlscope` Python package. Core implementation lives in `src/urlscope/`: `_client.py` for the async client, `_http.py` for transport/auth/retry behavior, `_exceptions.py` for the exception hierarchy, and `models/` for Pydantic response models. Tests live in `tests/`, with shared fixtures in `tests/conftest.py`. Product requirements and task sequencing live under `specs/001-urlscan-api-wrapper/`; treat those documents as the source of truth for API behavior.

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

Target Python 3.10+ and keep type annotations complete. Use `snake_case` for modules, functions, and variables, `PascalCase` for classes, and `_`-prefixed module names for internal implementation details. Keep public exports centralized in `src/urlscope/__init__.py`. For models, preserve upstream JSON compatibility with Pydantic aliases for camelCase fields such as `apexDomain -> apex_domain`.

## Testing Guidelines

Use `pytest`, `pytest-asyncio`, and `respx` for async and HTTP transport tests. Name files by feature area, for example `tests/test_submit.py` or `tests/test_errors.py`. Prefer shared fixtures from `tests/conftest.py` over inline sample payloads. The current US1 tests cover submit, result retrieval, auth, error mapping, and async context management; sync-context checks are intentionally deferred until `SyncClient` exists.

## Commit & Pull Request Guidelines

Write short, imperative commit subjects such as `Add result polling tests`. Keep commits scoped to a single task or coherent change. Recent history follows task-based commits (`T010`, `T011`, etc.); continuing that pattern is preferred. PRs should include a concise summary, references to the relevant spec/task IDs, and the exact verification commands you ran.

## Security & Configuration Tips

Never commit real API keys. Use `URLSCAN_API_KEY` for local development or pass credentials explicitly at runtime. Keep fixtures and examples sanitized, and avoid checking in captured scan artifacts or sensitive response payloads.
