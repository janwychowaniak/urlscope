# urlscope

Async-first Python client for the urlscan.io API, published on PyPI as `urlscope`. The code
is the source of truth for what the library does. [docs/design.md](docs/design.md) records why
it is built this way and how the live urlscan API behaves; ideas outside the current scope live
in [BACKLOG.md](BACKLOG.md).

## Layout

- `src/urlscope/_client.py`: `UrlscopeClient`, the async client (submit, polling, results,
  search, artifacts, quotas).
- `src/urlscope/_sync.py`: `SyncClient`, which runs a fresh async client per call.
- `src/urlscope/_http.py`: the transport on `httpx2.AsyncClient`: API key, error mapping,
  429 retries.
- `src/urlscope/_exceptions.py`: the exception hierarchy.
- `src/urlscope/models/`: Pydantic response models.
- `src/urlscope/__init__.py`: public exports and `__version__`, the only place the version lives
  (`pyproject.toml` reads it).
- `tests/`: mocked tests, one file per feature area, shared fixtures in `tests/conftest.py` and
  sanitized payloads in `tests/fixtures/`. `tests/live/`: tests against the real API.

## Commands

```bash
uv sync                                    # Python from .python-version, dev group included
git config core.hooksPath .githooks        # once per clone: gitleaks hooks
uv run pytest tests/                       # mocked tests; live tests are deselected
uv run --env-file .env pytest -m live      # live tests: real key, two private scans per run
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/                           # strict
uv build && uvx twine check --strict dist/*
```

To run the mocked tests on another supported Python without touching `.venv`:
`UV_PROJECT_ENVIRONMENT=<scratch dir> uv run --python 3.11 pytest tests/`.

## Conventions

- Python 3.11-3.15 (`requires-python >=3.11` and the CI matrix); complete type annotations,
  mypy in strict mode, ruff for lint and format.
- `snake_case` for modules, functions and variables, `PascalCase` for classes; `_`-prefixed
  modules are internal, and public names are exported from `src/urlscope/__init__.py`.
- Every model uses `ConfigDict(extra="allow", populate_by_name=True)`; camelCase wire names map
  to snake_case fields through `Field(alias=...)`, e.g. `apexDomain` to `apex_domain`.
- Runtime dependencies are `httpx2` and `pydantic` only. Their lower bounds in `pyproject.toml`
  are what CI's `lowest-deps` job proves (Python 3.11 with the oldest allowed versions);
  Dependabot moves only `uv.lock`.

## Tests

- pytest with pytest-asyncio in auto mode. HTTP is mocked with respx through pytest-httpx2:
  request the `httpx2_mock` fixture and build responses as `httpx.Response` (respx does not
  accept `httpx2.Response` yet, so `httpx` stays a dev dependency). The fixture fails on routes
  that are never called and on requests without a route.
- Prefer shared fixtures in `tests/conftest.py` over inline payloads. Assert on values, not on
  `id()` or other runtime reuse details.
- To fake time in the client, replace `urlscope._client`'s `time` and `asyncio` references (see
  `fake_clock` in `tests/test_result.py`), never the global ones the event loop uses.
- Live tests (`tests/live/`, marker `live`) run on demand and weekly in CI (`live-api.yml`,
  environment `live-api`, secret `URLSCAN_API_KEY`). They fail on HTTP errors and on responses
  that no longer fit the models, and list unmodeled fields in the summary; `KNOWN_UNMODELED` in
  `tests/live/conftest.py` names the sections left untyped on purpose. Without a key they error
  instead of skipping. GitHub disables scheduled workflows after 60 days without repository
  activity; `.githooks/pre-push` warns when that has happened.
- When the live API differs from the models, change the models, the tests and the quirks in
  `docs/design.md` together; no silent compatibility hacks.

## Commits and releases

- Commit directly to `main`: one coherent change per commit, an imperative subject and a body
  that says why.
- Release: bump `__version__`, commit and push; push the tag `test-v<version>` to publish to
  TestPyPI and check the result there; then push `v<version>` to publish to PyPI. `release.yml`
  builds once, checks the tag against `__version__` and publishes through trusted publishing;
  environment `pypi` waits for the owner's approval. Push one tag at a time
  (`git push origin v<version>`), never `--tags`.
- Release tags cannot be moved or deleted (a repository ruleset), and PyPI never accepts the same
  version twice; fixing a published tag means a new version.

## Security

- Never commit API keys. The key comes from `URLSCAN_API_KEY` (locally from the git-ignored
  `.env`) or the `api_key` argument.
- Gitleaks scans staged content, commit messages and pushed ranges locally (`.githooks/`, rules in
  `.gitleaks.toml`) and the full history in CI. Validate a `.gitleaks.toml` change on a corpus of
  fake keys, one per file, against the current config: a rule's keywords can switch off the
  built-in generic rule.
- Keep fixtures and examples sanitized; do not commit captured scan artifacts or sensitive
  payloads.
- Publishing uses PyPI trusted publishing only; no long-lived PyPI tokens.
