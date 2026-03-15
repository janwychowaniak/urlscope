# Research: urlscope API Wrapper Library

**Date**: 2026-03-15
**Branch**: `001-urlscan-api-wrapper`

## R1: Async httpx Client with Context Manager

**Decision**: Wrap `httpx.AsyncClient` internally; expose `__aenter__`/`__aexit__` on `UrlscopeClient` (async) and `__enter__`/`__exit__` on `SyncClient`.

**Rationale**: httpx's `AsyncClient` supports `async with` natively for connection pool lifecycle. Our client wraps it, delegating `aclose()` to the inner client. This ensures connections are cleaned up properly in long-running applications. Users who don't use the context manager can call `.close()` / `.aclose()` explicitly.

**Alternatives considered**:
- Lazy client creation on first request — rejected because it complicates lifecycle and makes error timing unpredictable.
- Global module-level client — rejected because it leaks resources and doesn't support multiple API keys.

## R2: Sync Wrappers over Async Code

**Decision**: Use `asyncio.run()` per method call. Each sync method creates a fresh `UrlscopeClient` (async), runs the operation inside `asyncio.run()`, and closes it. `SyncClient` does NOT hold a persistent `UrlscopeClient` instance across calls — it only stores constructor parameters (`_api_key`, `_base_url`, `_timeout`, `_max_retries`).

**Pattern per method**:
```python
def get_result(self, uuid: str) -> ScanResult:
    async def _run():
        async with UrlscopeClient(self._api_key, ...) as c:
            return await c.get_result(uuid)
    return asyncio.run(_run())
```

**Rationale**: `httpx.AsyncClient`'s connection pool is bound to the event loop that created it. A persistent async client across multiple `asyncio.run()` calls (each creating a new loop) leads to silently leaked or invalid pool state. Fresh client per call avoids this entirely. Performance cost (connection setup per call) is acceptable for the sync/script use case, where convenience outweighs throughput. Not suitable for use inside an already-running async context (documented limitation).

**Alternatives considered**:
- Persistent `UrlscopeClient` held by `SyncClient` — rejected because `httpx.AsyncClient` pools are event-loop-bound; reuse across `asyncio.run()` calls causes leaked/invalid pool state.
- `anyio.from_thread.run` — adds an unnecessary dependency (anyio). Rejected per "no unnecessary dependencies" constraint.
- Thread-based executor with persistent loop — over-engineered for this use case; adds complexity for marginal benefit.
- `nest_asyncio` — rejected because it patches the event loop globally, which is a side-effect-heavy approach.

## R3: Pydantic v2 Partial Typed Models with Raw Access

**Decision**: Use `model_config = ConfigDict(extra="allow")` on all response models. This lets Pydantic capture explicitly-typed fields while preserving extra fields in `model_extra`. Expose a `.raw` property that returns the original dict.

**Rationale**: The urlscan.io result JSON has hundreds of fields across deeply nested structures. Full typing is impractical and brittle (fields change without notice per API docs). `extra="allow"` stores unrecognized fields in `model_extra`, accessible via `model.model_extra["some_field"]`. Adding a `.raw` property on top provides the complete original dict for users who need arbitrary field access.

**Alternatives considered**:
- `extra="ignore"` — rejected because it silently discards fields users may need.
- `extra="forbid"` — rejected because API responses may include new fields at any time.
- Separate `raw: dict` field — rejected because `model_extra` already provides this natively.

## R4: Exponential Backoff for HTTP 429

**Decision**: Implement custom retry logic in a `_request` method. On 429, parse `X-Rate-Limit-Reset-After` header for wait duration; fall back to exponential backoff (base 2s, jitter ±25%) if header absent. Max 5 retries, configurable.

**Rationale**: urlscan.io returns standard rate limit headers including `X-Rate-Limit-Reset-After` (seconds until reset). Using this value is more efficient than blind exponential backoff. Adding jitter prevents thundering herd when multiple clients retry simultaneously. The retry logic must be in our request method, not in httpx transport (which doesn't natively handle 429).

**Alternatives considered**:
- `tenacity` library — adds a dependency. Rejected per constraint.
- httpx transport-level retry — only handles connection errors, not HTTP-level 429s.
- `urllib3.util.Retry` — wrong HTTP client ecosystem.

## R5: src/ Layout with Hatchling

**Decision**: Use `src/urlscope/` layout with hatchling as build backend. pyproject.toml as single config file for build, project metadata, ruff, mypy, and pytest.

**Rationale**: src/ layout is the modern standard for Python packages. It prevents accidental imports of the uninstalled package during development. Hatchling is lightweight, fast, and handles src/ layout natively.

**Alternatives considered**:
- Flat layout (`urlscope/` at root) — rejected because src/ layout provides better isolation.
- flit — viable but hatchling is more flexible and equally maintained.
- setuptools — viable but requires more configuration; hatchling is more modern.

**Structure**:
```
src/urlscope/
├── __init__.py          # Public API re-exports
├── _client.py           # AsyncClient implementation
├── _sync.py             # SyncClient wrapper
├── _http.py             # HTTP transport, retry logic, rate limiting
├── _exceptions.py       # Exception hierarchy
├── models/
│   ├── __init__.py
│   ├── _submission.py   # SubmissionRequest, SubmissionResponse
│   ├── _result.py       # ScanResult, TaskInfo, PageInfo, Verdicts, etc.
│   ├── _search.py       # SearchResult, SearchResultItem
│   └── _quota.py        # QuotaInfo
└── py.typed             # PEP 561 marker
```

## R6: respx for HTTP Mocking in pytest

**Decision**: Use respx as the HTTP mocking library. It integrates natively with httpx and supports both sync and async test patterns.

**Rationale**: respx is the de facto mock library for httpx (similar to responses for requests). It supports route matching by URL pattern, method, and headers. It can return pre-built `httpx.Response` objects. It works with pytest via `@respx.mock` decorator or `respx.mock()` context manager.

**Alternatives considered**:
- `pytest-httpx` — viable alternative; slightly different API style. respx has broader adoption.
- `vcrpy` — records/replays real HTTP; not suitable since we want no live calls.

**Test structure**:
```
tests/
├── conftest.py          # Shared fixtures (mock client, sample responses)
├── test_submit.py       # Submission API tests
├── test_result.py       # Result retrieval + polling tests
├── test_search.py       # Search API tests
├── test_artifacts.py    # Screenshot, DOM, certificate tests
├── test_quota.py        # Quota endpoint tests
├── test_retry.py        # Rate limit / backoff tests
├── test_sync.py         # Sync wrapper tests
├── test_auth.py         # API key resolution tests
└── test_errors.py       # Error handling tests
```
