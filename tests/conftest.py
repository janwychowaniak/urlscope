import json
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from urlscope import UrlscopeClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load_json_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text())


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture
def test_base_url() -> str:
    return "https://test.urlscan.io"


@pytest_asyncio.fixture
async def mock_client(
    api_key: str,
    test_base_url: str,
) -> AsyncIterator[UrlscopeClient]:
    async with UrlscopeClient(api_key=api_key, base_url=test_base_url) as client:
        yield client


@pytest.fixture
def submission_response_json() -> dict[str, object]:
    return {
        "message": "Submission successful",
        "uuid": "scan-123",
        "result": "https://urlscan.io/result/scan-123/",
        "api": "https://urlscan.io/api/v1/result/scan-123/",
        "visibility": "public",
        "url": "https://example.com",
        "country": "US",
        "options": {
            "customagent": "ExampleAgent/1.0",
            "overrideSafety": True,
        },
    }


@pytest.fixture
def scan_result_json() -> dict[str, object]:
    return _load_json_fixture("result_malicious.json")


@pytest.fixture
def clean_scan_result_json() -> dict[str, object]:
    return _load_json_fixture("result_clean.json")


@pytest.fixture
def scored_scan_result_json() -> dict[str, object]:
    return _load_json_fixture("result_scored.json")


@pytest.fixture
def rate_limit_response() -> httpx.Response:
    return httpx.Response(
        429,
        headers={
            "X-Rate-Limit-Reset-After": "1.5",
            "X-Rate-Limit-Scope": "user",
            "X-Rate-Limit-Window": "minute",
        },
        json={"message": "Rate limit exceeded"},
    )


@pytest.fixture
def validation_error_response() -> httpx.Response:
    return httpx.Response(
        400,
        json={
            "message": "Validation failed",
            "description": "Invalid URL format",
        },
    )


@pytest.fixture
def authentication_error_response() -> httpx.Response:
    return httpx.Response(
        401,
        json={
            "message": "Unauthorized",
            "description": "Invalid API key",
        },
    )


@pytest.fixture
def not_found_error_response() -> httpx.Response:
    return httpx.Response(
        404,
        json={
            "message": "Scan not found",
            "description": "The scan is still pending or does not exist",
        },
    )


@pytest.fixture
def scan_deleted_error_response() -> httpx.Response:
    return httpx.Response(
        410,
        json={
            "message": "Scan deleted",
            "description": "The requested scan was deleted",
        },
    )
