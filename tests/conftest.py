from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio

from urlscope import UrlscopeClient


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture
def test_base_url() -> str:
    return "https://test.urlscan.io"


@pytest_asyncio.fixture
async def mock_client(api_key: str, test_base_url: str) -> AsyncIterator[UrlscopeClient]:
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
    return {
        "task": {
            "uuid": "scan-123",
            "url": "https://example.com",
            "domain": "example.com",
            "apexDomain": "example.com",
            "time": "2026-03-15T10:00:00+00:00",
            "method": "api",
            "visibility": "public",
            "tags": ["investigation"],
            "options": {
                "customagent": "ExampleAgent/1.0",
                "overrideSafety": True,
            },
        },
        "page": {
            "url": "https://example.com/landing",
            "domain": "example.com",
            "apexDomain": "example.com",
            "ip": "93.184.216.34",
            "asn": "15133",
            "asnname": "EDGECAST",
            "country": "US",
            "city": "Los Angeles",
            "server": "ECS",
            "title": "Example Domain",
            "status": "200",
            "mimeType": "text/html",
            "tlsIssuer": "Example Test CA",
            "tlsValidFrom": "2026-03-01T00:00:00+00:00",
            "tlsValidDays": 90,
            "tlsAgeDays": 14,
            "umbrellaRank": 42,
            "redirected": "https://example.com/landing",
            "ptr": "edge.example.net",
        },
        "verdicts": {
            "score": 5,
            "categories": ["benign"],
            "brands": [
                {
                    "key": "example",
                    "name": "Example",
                    "country": ["US"],
                    "vertical": ["technology"],
                }
            ],
            "malicious": False,
        },
        "stats": {
            "requests": 7,
            "uniqIPs": 1,
        },
        "lists": {
            "ips": ["93.184.216.34"],
            "domains": ["example.com"],
            "urls": ["https://example.com/landing"],
            "countries": ["US"],
            "asns": [15133],
            "servers": ["ECS"],
            "hashes": ["abc123"],
            "certificates": [
                {
                    "subject": "CN=example.com",
                    "issuer": "Example Test CA",
                    "validFrom": "2026-03-01T00:00:00+00:00",
                    "validTo": "2026-06-01T00:00:00+00:00",
                    "sanList": ["example.com", "www.example.com"],
                }
            ],
            "linkDomains": ["cdn.example.com"],
        },
        "data": {
            "cookies": [],
        },
        "meta": {
            "processors": [],
        },
    }


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
