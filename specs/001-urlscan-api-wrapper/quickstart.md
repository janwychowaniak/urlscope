# Quickstart: urlscope

**Branch**: `001-urlscan-api-wrapper`
**Date**: 2026-03-15

## Installation

```bash
pip install urlscope
```

## Setup

Set your API key (get one from https://urlscan.io/user/signup):

```bash
export URLSCAN_API_KEY="your-api-key-here"
```

Or pass it directly in code (takes precedence over env var).

## Async Usage (primary)

### Submit and wait for result

```python
import asyncio
from urlscope import UrlscopeClient

async def main():
    async with UrlscopeClient() as client:
        result = await client.submit_and_wait("https://example.com", visibility="public")
        overall = result.verdicts.overall if result.verdicts else None
        print(f"Overall score: {overall.score if overall else None}")
        print(f"Page title: {result.page.title}")
        print(f"IPs contacted: {result.lists.ips}")

asyncio.run(main())
```

### Submit without waiting

```python
async with UrlscopeClient(api_key="your-key") as client:
    submission = await client.submit("https://example.com", visibility="private")
    print(f"Scan UUID: {submission.uuid}")
    print(f"Result URL: {submission.result}")
    # ... later ...
    result = await client.get_result(submission.uuid)
```

### Search existing scans

```python
async with UrlscopeClient() as client:
    response = await client.search(
        "domain:example.com",
        size=10,
        datasource="scans",
    )
    print(f"Total matches: {response.total}, query took: {response.took}ms")

    for item in response.results:
        page_url = item.page.get("url", "N/A") if item.page else "N/A"
        print(f"{item.id}: {page_url} -> {item.result}")

    # Paginate
    if response.has_more:
        next_page = await client.search(
            "domain:example.com",
            size=10,
            search_after=response.results[-1].sort,
        )
```

### Download artifacts

```python
async with UrlscopeClient() as client:
    screenshot = await client.get_screenshot("scan-uuid-here")
    with open("screenshot.png", "wb") as f:
        f.write(screenshot)

    dom = await client.get_dom("scan-uuid-here")
    with open("dom.html", "w") as f:
        f.write(dom)
```

### Check quotas

```python
async with UrlscopeClient() as client:
    quotas = await client.get_quotas()
    for q in quotas.quotas:
        print(f"{q.action} ({q.window}): {q.remaining}/{q.limit}")
```

## Sync Usage (convenience)

For scripts and simple applications:

```python
from urlscope import SyncClient

with SyncClient() as client:
    result = client.submit_and_wait("https://example.com")
    overall = result.verdicts.overall if result.verdicts else None
    print(f"Overall score: {overall.score if overall else None}")
```

All async methods have sync equivalents with the same signature (minus `await`).

## Error Handling

```python
from urlscope import UrlscopeClient, RateLimitError, ScanTimeoutError

async with UrlscopeClient() as client:
    try:
        result = await client.submit_and_wait(
            "https://example.com",
            poll_timeout=120.0,
        )
    except ScanTimeoutError as e:
        print(f"Scan {e.uuid} still pending after timeout")
    except RateLimitError as e:
        print(f"Rate limited. Retry after: {e.retry_after}s")
```

## Accessing Raw API Response

All response models expose the full raw API response for accessing fields not covered by the typed model:

```python
result = await client.get_result("uuid")
# Typed access (common fields)
print(result.page.title)
# Raw access (any field)
print(result.model_extra.get("some_new_field"))
```
