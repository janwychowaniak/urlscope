# urlscope

`urlscope` is an async-first Python wrapper for the urlscan.io API. It provides typed Pydantic models for common API responses, automatic API key handling, built-in retry logic for rate limits, and a sync convenience wrapper for scripts.

## Installation

```bash
pip install urlscope
```

If you want to install the current prerelease from PyPI, use:

```bash
pip install --pre urlscope
```

Set your API key before making requests:

```bash
export URLSCAN_API_KEY="your-api-key-here"
```

## Quickstart

### Async submit and wait

```python
import asyncio
from urlscope import UrlscopeClient


async def main() -> None:
    async with UrlscopeClient() as client:
        result = await client.submit_and_wait(
            "https://example.com",
            visibility="public",
        )
        overall = result.verdicts.overall if result.verdicts else None
        print(result.task.uuid)
        print(result.page.url)
        print(overall.score if overall else None)


asyncio.run(main())
```

### Sync usage

```python
from urlscope import SyncClient


with SyncClient() as client:
    result = client.get_result("scan-uuid-here")
    print(result.page.url)
```

### Search

```python
import asyncio
from urlscope import UrlscopeClient


async def main() -> None:
    async with UrlscopeClient() as client:
        response = await client.search("domain:example.com", size=10)
        for item in response.results:
            print(item.id, item.page.get("url") if item.page else None)

        # Cursor-based pagination is handled via the previous item's sort key.
        if response.has_more and response.results and response.results[-1].sort:
            next_page = await client.search(
                "domain:example.com",
                size=10,
                search_after=response.results[-1].sort,
            )
            print(len(next_page.results))


asyncio.run(main())
```

### Download artifacts

```python
import asyncio
from urlscope import UrlscopeClient


async def main() -> None:
    async with UrlscopeClient() as client:
        screenshot = await client.get_screenshot("scan-uuid-here")
        dom = await client.get_dom("scan-uuid-here")
        print(len(screenshot), len(dom))


asyncio.run(main())
```

### Check quotas

```python
import asyncio
from urlscope import UrlscopeClient


async def main() -> None:
    async with UrlscopeClient() as client:
        quotas = await client.get_quotas()
        print(quotas.scope)
        for q in quotas.quotas[:5]:
            print(q.scope, q.action, q.window, q.used, q.remaining, q.limit)


asyncio.run(main())
```

The live quotas response is also available in raw form via `QuotaInfo.limits`.

### Error handling

```python
import asyncio
from urlscope import RateLimitError, ScanTimeoutError, UrlscopeClient


async def main() -> None:
    async with UrlscopeClient() as client:
        try:
            await client.submit_and_wait("https://example.com", poll_timeout=120.0)
        except ScanTimeoutError as exc:
            print(exc.uuid)
        except RateLimitError as exc:
            print(exc.retry_after, exc.scope, exc.window)


asyncio.run(main())
```

`submit(..., override_safety=True)` is supported by the wrapper and is serialized to the current live urlscan wire format for `overrideSafety`.

## API Reference

Primary clients:

- `UrlscopeClient`: async interface for submit, result retrieval, polling, search, artifacts, and quotas
- `SyncClient`: sync wrapper with the same method surface for scripts and simple integrations

Key response models:

- `SubmissionResponse`
- `ScanResult`, `TaskInfo`, `PageInfo`, `Verdicts`, `BrandMatch`, `ScanLists`, `CertificateInfo`
- `SearchResponse`, `SearchResultItem`
- `QuotaInfo`, `QuotaWindow`

`ScanResult.verdicts` follows the live urlscan structure with nested sections such as `overall`, `urlscan`, `engines`, and `community`. For example, use `result.verdicts.overall.score` for the top-level score.

Key exceptions:

- `UrlscopeError`
- `AuthenticationError`
- `ValidationError`
- `NotFoundError`
- `ScanDeletedError`
- `RateLimitError`
- `ScanTimeoutError`
- `APIError`

## Development

```bash
uv sync --extra dev
.venv/bin/pytest tests/
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
```

The package version is defined in `src/urlscope/__init__.py` and read dynamically by Hatchling during builds.

## License

MIT
