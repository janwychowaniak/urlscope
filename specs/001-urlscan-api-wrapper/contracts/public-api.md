# Public API Contract: urlscope

**Branch**: `001-urlscan-api-wrapper`
**Date**: 2026-03-15

This document defines the public interface of the `urlscope` library — the classes, methods, and types users import and interact with. Everything not listed here is considered internal (`_`-prefixed modules).

## Package Exports (`urlscope.__init__`)

```
urlscope.UrlscopeClient       # Async client (primary)
urlscope.SyncClient           # Sync convenience wrapper

# Response models
urlscope.SubmissionResponse
urlscope.ScanResult
urlscope.TaskInfo
urlscope.PageInfo
urlscope.Verdicts
urlscope.BrandMatch
urlscope.ScanLists
urlscope.CertificateInfo
urlscope.SearchResponse
urlscope.SearchResultItem
urlscope.QuotaInfo
urlscope.QuotaWindow

# Exceptions
urlscope.UrlscopeError        # Base exception
urlscope.AuthenticationError  # 401/403
urlscope.NotFoundError        # 404 (scan not found)
urlscope.ScanDeletedError     # 410 (scan deleted)
urlscope.ValidationError      # 400 (bad request / invalid URL)
urlscope.RateLimitError       # 429 after max retries exhausted
urlscope.ScanTimeoutError     # Polling timeout exceeded
urlscope.APIError             # Other HTTP errors from API
```

`Verdicts` mirrors the live nested urlscan result structure. Users should access verdict data through sections such as `result.verdicts.overall.score` and `result.verdicts.urlscan.brands`.

**Typing imports**: `from typing import Any, Literal, Self`

## UrlscopeClient (async)

```
class UrlscopeClient:
    def __init__(
        self,
        api_key: str | None = None,        # Explicit key (preferred)
        *,
        base_url: str = "https://urlscan.io",
        timeout: float = 30.0,              # Per-request timeout (seconds)
        max_retries: int = 5,               # Max 429 retry attempts
    ) -> None: ...

    # Context manager
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, ...) -> None: ...
    async def aclose(self) -> None: ...

    # Submission
    async def submit(
        self,
        url: str,
        *,
        visibility: Literal["public", "unlisted", "private"] | None = None,
        tags: list[str] | None = None,
        custom_agent: str | None = None,
        referer: str | None = None,
        override_safety: bool | str | None = None,
        country: str | None = None,
    ) -> SubmissionResponse: ...

    # Result retrieval
    async def get_result(self, uuid: str) -> ScanResult: ...

    # Submit + poll until complete
    async def submit_and_wait(
        self,
        url: str,
        *,
        visibility: Literal["public", "unlisted", "private"] | None = None,
        tags: list[str] | None = None,
        custom_agent: str | None = None,
        referer: str | None = None,
        override_safety: bool | str | None = None,
        country: str | None = None,
        poll_interval: float = 5.0,         # Seconds between polls
        initial_wait: float = 10.0,         # Wait before first poll
        poll_timeout: float = 300.0,        # Max wait (seconds)
    ) -> ScanResult: ...

    # Search
    async def search(
        self,
        query: str = "*",
        *,
        size: int = 100,
        search_after: list[Any] | None = None,  # Pagination cursor
        datasource: Literal[
            "scans",
            "hostnames",
            "incidents",
            "notifications",
            "certificates",
        ] | None = None,
        collapse: str | None = None,
    ) -> SearchResponse: ...

    # Artifacts
    async def get_screenshot(self, uuid: str) -> bytes: ...
    async def get_dom(self, uuid: str) -> str: ...

    # Account
    async def get_quotas(self) -> QuotaInfo: ...
```

`override_safety=True` is supported as a convenience and is serialized to the current live wire format (`"true"`).
`search_after` is serialized as one comma-separated cursor string for compatibility with the live search API.
`datasource` and `collapse` are passed through as optional search query parameters.
Search is backed by urlscan's searchable index and is not guaranteed to find every UUID that `get_result(uuid)` can retrieve; use `get_result()` when the scan UUID is already known.
`get_quotas()` returns the live nested quota payload in `QuotaInfo.limits` and a flattened `QuotaInfo.quotas` convenience list for minute/hour/day windows. Raw metadata entries under `limits` are preserved but not flattened.

## SyncClient

Thin sync wrapper. Stores constructor parameters only — each method call creates a fresh `UrlscopeClient` inside `asyncio.run()` and closes it after the call. No persistent connection state. Same constructor parameters as `UrlscopeClient`.

```
class SyncClient:
    def __init__(self, api_key: str | None = None, *, ...) -> None: ...

    # Context manager (no-op — no persistent connection to clean up;
    # each method call creates and closes a fresh UrlscopeClient internally.
    # Provided for API symmetry with UrlscopeClient and ergonomic use in scripts.)
    def __enter__(self) -> Self: ...
    def __exit__(self, *args) -> None: ...
    def close(self) -> None: ...

    # All methods create a fresh UrlscopeClient per call via asyncio.run()
    def submit(self, url: str, *, ...) -> SubmissionResponse: ...
    def get_result(self, uuid: str) -> ScanResult: ...
    def submit_and_wait(self, url: str, *, ...) -> ScanResult: ...
    def search(self, query: str = "*", *, ...) -> SearchResponse: ...
    def get_screenshot(self, uuid: str) -> bytes: ...
    def get_dom(self, uuid: str) -> str: ...
    def get_quotas(self) -> QuotaInfo: ...
```

## Exception Hierarchy

```
UrlscopeError (base)
├── AuthenticationError    # HTTP 401/403
├── ValidationError        # HTTP 400 (surfaces API message plus description/detail when available)
├── NotFoundError          # HTTP 404 (scan still pending or not found)
├── ScanDeletedError       # HTTP 410
├── RateLimitError         # HTTP 429 after max retries
│     .retry_after: float | None     # Seconds until reset (if known)
│     .scope: str | None             # Rate limit scope
│     .window: str | None            # Rate limit window
├── ScanTimeoutError       # Polling exceeded poll_timeout
│     .uuid: str                     # UUID that timed out
└── APIError               # Other unexpected HTTP errors
      .status_code: int
      .message: str
```

## Behavioral Contracts

### API Key Resolution
1. Explicit `api_key` parameter → used if provided
2. `URLSCAN_API_KEY` environment variable → fallback
3. Neither → raises `AuthenticationError` at construction time

### Rate Limit Handling
1. On HTTP 429: read `X-Rate-Limit-Reset-After` header
2. If header present: wait that many seconds + jitter
3. If header absent: exponential backoff (base 2s, factor 2x, jitter ±25%)
4. Retry up to `max_retries` times
5. After max retries: raise `RateLimitError`

### Polling Behavior (`submit_and_wait`)
1. Submit scan → receive UUID
2. Wait `initial_wait` seconds
3. Poll `GET /api/v1/result/{uuid}/` every `poll_interval` seconds
4. HTTP 404 → scan still pending, continue polling
5. HTTP 200 → return parsed `ScanResult`
6. HTTP 410 → raise `ScanDeletedError`
7. Elapsed time > `poll_timeout` → raise `ScanTimeoutError`

### Logging
- Logger name: `"urlscope"`
- Default handler: `NullHandler` (silent)
- DEBUG: retry attempts, poll iterations, request details
- WARNING: rate limit exhaustion, unexpected response fields
