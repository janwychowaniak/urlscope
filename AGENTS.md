# Repository Guidelines

## Project Structure & Module Organization

This repository uses a `src/` layout for the `urlscope` Python package. Core implementation lives in `src/urlscope/`: `_client.py` for the async client, `_sync.py` for the sync wrapper, `_http.py` for transport/auth/retry behavior, `_exceptions.py` for the exception hierarchy, and `models/` for Pydantic response models (`_submission.py`, `_result.py`, `_search.py`, `_quota.py`). Tests live in `tests/`, with shared fixtures in `tests/conftest.py`. Product requirements and task sequencing live under `specs/001-urlscan-api-wrapper/`; treat those documents as the source of truth, but verify against the live urlscan API when behavior appears to drift.

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

Target Python 3.10+ and keep type annotations complete. Use `snake_case` for modules, functions, and variables, `PascalCase` for classes, and `_`-prefixed module names for internal implementation details. Keep public exports centralized in `src/urlscope/__init__.py`. For models, preserve upstream JSON compatibility with Pydantic aliases for camelCase fields such as `apexDomain -> apex_domain`. When the live API shape differs from the local spec, update the spec docs and tests together instead of carrying silent compatibility hacks.

## Testing Guidelines

Use `pytest`, `pytest-asyncio`, and `respx` for async and HTTP transport tests. Name files by feature area, for example `tests/test_submit.py` or `tests/test_errors.py`. Prefer shared fixtures from `tests/conftest.py` over inline sample payloads. The current suite covers async and sync client behavior, search pagination, artifacts, quota handling, retry logic, and context management. Run focused files while iterating, then rerun the affected area after any live-API-driven fix. Avoid brittle assertions based on `id()` or other runtime reuse details when a direct object or value assertion is possible.

## Live API Drift

Treat mocked tests as the default, but use live smoke tests to validate behavior that may have changed upstream. When the real urlscan API contradicts the local spec, update implementation, tests, and spec docs together instead of leaving the mismatch undocumented. Known live-API corrections in this repo:

- Search pagination requires `search_after` as one comma-separated string, not repeated query parameters.
- Quotas come from `GET /api/v1/quotas`, and the live response is nested under `limits`. The library preserves raw `limits` and exposes a flattened `QuotaInfo.quotas` convenience view.

Keep live smoke tests small and explicit, and avoid turning them into default test-suite requirements.

## Commit & Pull Request Guidelines

Write short, imperative commit subjects such as `Add result polling tests`. Keep commits scoped to a single task or coherent change. Recent history follows task-based commits and occasional follow-up fixes for live API mismatches; continuing that pattern is preferred. PRs should include a concise summary, references to the relevant spec/task IDs, and the exact verification commands you ran, including live smoke tests when they drove a behavior change.

## Security & Configuration Tips

Never commit real API keys. Use `URLSCAN_API_KEY` for local development or pass credentials explicitly at runtime. Keep fixtures and examples sanitized, and avoid checking in captured scan artifacts or sensitive response payloads.
