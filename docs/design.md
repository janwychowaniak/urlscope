# urlscope design notes

Why the library is built the way it is, and how the live urlscan.io API behaves where it differs
from what one would expect. The code is the source of truth for what the library does.

## Principles

- **The urlscan API changes without notice.** Response shapes have changed under released
  versions of this library. The models therefore type the stable, commonly used fields and keep
  the rest in Pydantic extras, and a weekly live test (`tests/live/`) checks the real API.
- **Partial typing.** Every model uses `extra="allow"`: fields a model does not type stay
  readable in `model.model_extra`, and `model.model_dump(by_alias=True)` returns the whole payload
  under urlscan's field names. `extra="ignore"` would drop data users need; `extra="forbid"` would
  break on every field urlscan adds. Sections whose presence and shape vary between scans stay
  untyped on purpose (see the quirks below).
- **Few dependencies.** The runtime needs `httpx2`, Pydantic's continuation of httpx (whose last
  stable release is 0.28.1 from December 2024), and `pydantic`. Retries are written in the
  transport instead of pulling in `tenacity`, and the sync wrapper uses `asyncio.run` instead of
  `anyio`.
- **Async first, sync by wrapping.** `SyncClient` stores only its constructor arguments and runs
  each call through `asyncio.run()` with a fresh `UrlscopeClient`. An `httpx2.AsyncClient`
  connection pool belongs to the event loop that created it, so a client kept across
  `asyncio.run()` calls would end up with an invalid pool; a thread with its own loop would add
  complexity, and `nest_asyncio` patches the event loop globally. The price is a new connection
  per call, and `SyncClient` cannot be used inside a running event loop. Its context manager is a
  no-op, kept for symmetry with `UrlscopeClient`.

## Behaviour

### API key

An explicit `api_key` wins over the `URLSCAN_API_KEY` environment variable. With neither, the
client raises `AuthenticationError` at construction, before any request.

### Errors

| Response | Exception |
|---|---|
| 400 "Invalid API key format" | `AuthenticationError` |
| any other 400 | `ValidationError` |
| 401, 403 | `AuthenticationError` |
| 404 | `NotFoundError` (also a scan that is still pending) |
| 410 | `ScanDeletedError` |
| 429 after `max_retries` retries | `RateLimitError` (`retry_after`, `scope`, `window`) |
| any other 4xx or 5xx | `APIError` (`status_code`, `message`) |

The message comes from the JSON error body (`message`, `description`, `detail` or `errors[]`). A
non-JSON body enters the message only when it is text, cut to 300 characters; otherwise the
message reads like `HTTP 404 (image/png, 15130 bytes)`. Network failures (connection errors,
timeouts) are not wrapped: they propagate as `httpx2` exceptions. `submit` rejects more than 10
tags with `ValueError` before sending anything.

### Rate limits

On 429 the transport waits `X-Rate-Limit-Reset-After` seconds when urlscan sends that header,
otherwise 2 s doubling with each attempt, in both cases with ±25% jitter, and retries up to
`max_retries` times (default 5). The limits differ between account tiers; the policy does not.
Other errors are not retried.

### Polling (`submit_and_wait`)

After submitting, it waits `initial_wait` (default 10 s) and polls `GET /api/v1/result/{uuid}/`:
404 means still pending, 200 returns the result, 410 raises `ScanDeletedError`. It polls at least
once, even when `initial_wait` has used up `poll_timeout` (default 300 s), checks the deadline
only after a 404, and cuts the last sleep (`poll_interval`, default 5 s) to the time left, so the
last poll happens at the deadline; then it raises `ScanTimeoutError`. A 404 cannot tell a pending
scan from an unknown UUID.

### Logging

Logger `urlscope` with a `NullHandler`, silent unless the application configures it. DEBUG:
retries, the initial wait and each poll. WARNING: rate limit retries exhausted.

## Live API quirks

- `search_after` is one comma-separated string of the previous page's last `sort` values, not
  repeated query parameters. `datasource` and `collapse` pass through as optional parameters. The
  page size defaults to 100; urlscan enforces the maximum.
- Search reads urlscan's search index: a UUID that `get_result` retrieves may not appear in
  `task.uuid:<uuid>` results. Use `get_result` when the UUID is known.
- Search items carry sections that vary between scans (`verdicts`, `dom`, `frames`, `links`,
  `text`, `scanner`, `meta`, `image`, `clipboard`, `team`, `websockets`); they stay in extras and
  are listed in `KNOWN_UNMODELED` in `tests/live/conftest.py`. A fresh scan result sometimes
  carries `metatags`, which a later fetch of the same scan lacks.
- Quotas (`GET /api/v1/quotas`) are nested under `limits`, next to metadata entries such as
  `features`, `products` and `queryableFields`. `QuotaInfo.limits` keeps the raw structure, and
  `QuotaInfo.quotas` flattens only the minute, hour and day windows.
- urlscan expects `overrideSafety` as the string `"true"`; `override_safety=True` is sent that
  way.
- Certificates use `subjectName` and may send `validFrom` and `validTo` as epoch timestamps;
  `CertificateInfo` normalizes them. The certificate chain is part of the scan result
  (`lists.certificates`); there is no separate endpoint.
- A malformed API key gets 400 "Invalid API key format"; a well-formed key that does not exist
  gets 401.
- `GET /dom/{uuid}/` returns the document without its `<html>` wrapper; it starts with `<head>`.
- urlscan sometimes produces no screenshot for a finished scan: `/screenshots/{uuid}.png` answers
  404 with a placeholder PNG even though the result is ready and `task.screenshotURL` is set.
- `search` and `quotas` also answer without an API key, with limits per IP address; the client
  still requires a key (see BACKLOG.md).

## Out of scope

No command-line interface, no receiver for webhooks or callbacks, no submission of many URLs in
one call, and no async iterator over search pages: callers paginate with `search_after`.
