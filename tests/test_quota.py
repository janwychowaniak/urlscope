import httpx
import pytest

from urlscope import QuotaInfo


@pytest.fixture
def quota_response_json() -> dict[str, object]:
    return {
        "quotas": [
            {
                "scope": "user",
                "action": "search",
                "window": "minute",
                "limit": 60,
                "remaining": 59,
                "reset": "2026-03-17T10:00:00+00:00",
            },
            {
                "scope": "ip-address",
                "action": "public",
                "window": "day",
                "limit": 1000,
                "remaining": 998,
            },
        ]
    }


@pytest.mark.asyncio
async def test_get_quotas_returns_typed_quota_info_with_windows(
    mock_client,
    respx_mock,
    test_base_url,
    quota_response_json,
) -> None:
    respx_mock.get(f"{test_base_url}/user/quotas/").mock(
        return_value=httpx.Response(200, json=quota_response_json)
    )

    quotas = await mock_client.get_quotas()

    assert isinstance(quotas, QuotaInfo)
    assert len(quotas.quotas) == 2


@pytest.mark.asyncio
async def test_get_quotas_verifies_quota_fields(
    mock_client,
    respx_mock,
    test_base_url,
    quota_response_json,
) -> None:
    respx_mock.get(f"{test_base_url}/user/quotas/").mock(
        return_value=httpx.Response(200, json=quota_response_json)
    )

    quotas = await mock_client.get_quotas()

    first = quotas.quotas[0]
    assert first.scope == "user"
    assert first.action == "search"
    assert first.window == "minute"
    assert first.limit == 60
    assert first.remaining == 59
