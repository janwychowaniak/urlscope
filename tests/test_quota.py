import httpx
import pytest

from urlscope import QuotaInfo, QuotaWindow


@pytest.mark.asyncio
async def test_get_quotas_returns_live_shaped_quota_info_with_windows(
    mock_client,
    respx_mock,
    test_base_url,
    quota_response_json,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/quotas").mock(
        return_value=httpx.Response(200, json=quota_response_json)
    )

    quotas = await mock_client.get_quotas()

    assert isinstance(quotas, QuotaInfo)
    assert quotas.scope == "user"
    assert quotas.limits["maxRetentionPeriodDays"] == 7
    assert quotas.limits["queryVisibility"] == ["public"]
    assert len(quotas.quotas) == 21
    assert all(isinstance(window, QuotaWindow) for window in quotas.quotas)


@pytest.mark.asyncio
async def test_get_quotas_verifies_quota_fields(
    mock_client,
    respx_mock,
    test_base_url,
    quota_response_json,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/quotas").mock(
        return_value=httpx.Response(200, json=quota_response_json)
    )

    quotas = await mock_client.get_quotas()

    search_minute = next(
        window
        for window in quotas.quotas
        if window.action == "search" and window.window == "minute"
    )
    assert search_minute.scope == "user"
    assert search_minute.limit == 120
    assert search_minute.used == 0
    assert search_minute.remaining == 120
    assert search_minute.percent == 0
    assert search_minute.reset is None

    search_day = next(
        window
        for window in quotas.quotas
        if window.action == "search" and window.window == "day"
    )
    assert search_day.reset == "2030-01-01T00:00:00.000Z"


def test_quota_model_flattens_only_minute_hour_day_windows(
    quota_response_json,
) -> None:
    quotas = QuotaInfo.model_validate(quota_response_json)

    actions = {window.action for window in quotas.quotas}
    assert actions == {
        "livescan",
        "malicious",
        "private",
        "public",
        "retrieve",
        "search",
        "unlisted",
    }
    assert "features" not in actions
    assert "products" not in actions
    assert "queryableFields" not in actions
    assert "maxRetentionPeriodDays" not in actions
