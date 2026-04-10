import httpx
import pytest

from urlscope import (
    QuotaInfo,
    ScanResult,
    SearchResponse,
    SubmissionResponse,
    SyncClient,
)
from urlscope._client import UrlscopeClient


@pytest.fixture
def quota_response_json() -> dict[str, object]:
    return {
        "scope": "user",
        "limits": {
            "search": {
                "minute": {
                    "limit": 60,
                    "used": 1,
                    "remaining": 59,
                    "percent": 1.67,
                }
            }
        },
    }


def test_sync_submit_returns_typed_result(
    api_key: str,
    respx_mock,
    test_base_url: str,
    submission_response_json,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_json)
    )

    client = SyncClient(api_key=api_key, base_url=test_base_url)
    result = client.submit("https://example.com", visibility="public")

    assert isinstance(result, SubmissionResponse)
    assert result.uuid == str(submission_response_json["uuid"])


def test_sync_get_result_returns_typed_result(
    api_key: str,
    respx_mock,
    test_base_url: str,
    scan_result_json,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=httpx.Response(200, json=scan_result_json)
    )

    client = SyncClient(api_key=api_key, base_url=test_base_url)
    result = client.get_result("scan-123")

    assert isinstance(result, ScanResult)
    assert result.task.uuid == "scan-123"


def test_sync_search_returns_typed_result(
    api_key: str,
    respx_mock,
    test_base_url: str,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "_id": "scan-123",
                        "sort": [1742120000, "scan-123"],
                        "page": {"url": "https://example.com"},
                        "task": {"visibility": "public"},
                        "stats": {"requests": 5},
                    }
                ],
                "total": 1,
                "has_more": False,
            },
        )
    )

    client = SyncClient(api_key=api_key, base_url=test_base_url)
    result = client.search("domain:example.com", size=10)

    assert isinstance(result, SearchResponse)
    assert result.results[0].id == "scan-123"


def test_sync_get_screenshot_returns_bytes(
    api_key: str,
    respx_mock,
    test_base_url: str,
) -> None:
    respx_mock.get(f"{test_base_url}/screenshots/scan-123.png").mock(
        return_value=httpx.Response(200, content=b"\x89PNG\r\n\x1a\nmock")
    )

    client = SyncClient(api_key=api_key, base_url=test_base_url)
    result = client.get_screenshot("scan-123")

    assert result == b"\x89PNG\r\n\x1a\nmock"


def test_sync_get_dom_returns_string(
    api_key: str,
    respx_mock,
    test_base_url: str,
) -> None:
    respx_mock.get(f"{test_base_url}/dom/scan-123/").mock(
        return_value=httpx.Response(200, text="<html><body>mock</body></html>")
    )

    client = SyncClient(api_key=api_key, base_url=test_base_url)
    result = client.get_dom("scan-123")

    assert result == "<html><body>mock</body></html>"


def test_sync_get_quotas_returns_typed_result(
    api_key: str,
    respx_mock,
    test_base_url: str,
    quota_response_json,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/quotas").mock(
        return_value=httpx.Response(200, json=quota_response_json)
    )

    client = SyncClient(api_key=api_key, base_url=test_base_url)
    result = client.get_quotas()

    assert isinstance(result, QuotaInfo)
    assert len(result.quotas) == 1
    assert result.quotas[0].action == "search"


def test_sync_client_uses_fresh_async_client_per_call(
    api_key: str,
    respx_mock,
    test_base_url: str,
    scan_result_json,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients: list[UrlscopeClient] = []
    original_init = UrlscopeClient.__init__

    def tracking_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        original_init(self, *args, **kwargs)
        created_clients.append(self)

    monkeypatch.setattr(UrlscopeClient, "__init__", tracking_init)
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=httpx.Response(200, json=scan_result_json)
    )

    client = SyncClient(api_key=api_key, base_url=test_base_url)
    first = client.get_result("scan-123")
    second = client.get_result("scan-123")

    assert isinstance(first, ScanResult)
    assert isinstance(second, ScanResult)
    assert len(created_clients) == 2
    assert created_clients[0] is not created_clients[1]
