# Repository Guidelines

## Project Structure & Module Organization

This repository is currently spec-first. Product requirements and implementation planning live under `specs/001-urlscan-api-wrapper/`, including `spec.md`, `plan.md`, `tasks.md`, and `quickstart.md`. The planned Python package layout is `src/urlscope/` for library code and `tests/` for pytest coverage. Keep new implementation files aligned with the structure defined in `plan.md`: transport in `_http.py`, clients in `_client.py` and `_sync.py`, and Pydantic models in `models/`.

## Build, Test, and Development Commands

Use the commands defined in the spec documents once scaffolding is added:

```bash
pip install -e ".[dev]"
pytest tests/
ruff check src/ tests/
mypy src/
```

`pip install -e ".[dev]"` installs the package and developer tooling. `pytest` runs the full test suite. `ruff check` enforces linting. `mypy` must pass in strict mode. For a quick import check, use `python -c "import urlscope"`.

## Coding Style & Naming Conventions

Target Python 3.10+ with full type annotations. Follow the planned `src/` layout and keep public exports centralized in `src/urlscope/__init__.py`. Use `snake_case` for modules, functions, and variables, `PascalCase` for classes, and leading underscores for internal modules such as `_exceptions.py`. Pydantic models should preserve API compatibility with aliases for upstream camelCase fields where needed.

## Testing Guidelines

Use `pytest`, `pytest-asyncio`, and `respx` for HTTP mocking. Place tests in `tests/` with filenames matching the feature area, for example `test_submit.py` or `test_retry.py`. The spec requires 100% public API coverage, so every exported client method, model surface, and exception path needs direct tests.

## Commit & Pull Request Guidelines

Git history currently contains only `Initial commit`, so use short, imperative commit subjects such as `Add async client retry handling`. Keep commits focused and logically grouped. Pull requests should include a concise summary, linked issue or spec section, test evidence (`pytest`, `ruff`, `mypy`), and sample request/response snippets when API behavior changes.

## Security & Configuration Tips

Do not hardcode secrets. Read the API key from `URLSCAN_API_KEY` or pass it explicitly at runtime. Keep example values obviously fake, and avoid committing live credentials, scan data, or generated artifacts.
