import logging

import httpx
import pytest

from urlscope import RateLimitError, ScanResult, UrlscopeClient
from urlscope import _http as http_module


@pytest.mark.asyncio
async def test_429_with_reset_after_header_retries_after_header_duration(
    api_key: str,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    rate_limit_response: httpx.Response,
    scan_result_json,
    test_base_url: str,
    respx_mock,
) -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(http_module.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(http_module.random, "uniform", lambda _a, _b: 1.1)
    caplog.set_level(logging.DEBUG, logger="urlscope")

    route = respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=[
            rate_limit_response,
            httpx.Response(200, json=scan_result_json),
        ]
    )

    async with UrlscopeClient(
        api_key=api_key,
        base_url=test_base_url,
        max_retries=2,
    ) as client:
        result = await client.get_result("scan-123")

    assert isinstance(result, ScanResult)
    assert sleep_calls == [pytest.approx(1.65)]
    assert len(route.calls) == 2
    assert "Retrying GET /api/v1/result/scan-123/ after HTTP 429" in caplog.text


@pytest.mark.asyncio
async def test_429_without_header_uses_exponential_backoff_with_jitter(
    api_key: str,
    monkeypatch: pytest.MonkeyPatch,
    scan_result_json,
    test_base_url: str,
    respx_mock,
) -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(http_module.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(http_module.random, "uniform", lambda _a, _b: 0.8)

    route = respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=[
            httpx.Response(429, json={"message": "Rate limit exceeded"}),
            httpx.Response(200, json=scan_result_json),
        ]
    )

    async with UrlscopeClient(
        api_key=api_key,
        base_url=test_base_url,
        max_retries=2,
    ) as client:
        result = await client.get_result("scan-123")

    assert isinstance(result, ScanResult)
    assert sleep_calls == [1.6]
    assert sleep_calls[0] != 2.0
    assert len(route.calls) == 2


@pytest.mark.asyncio
async def test_multiple_429s_then_200_succeeds(
    api_key: str,
    monkeypatch: pytest.MonkeyPatch,
    scan_result_json,
    test_base_url: str,
    respx_mock,
) -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(http_module.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(http_module.random, "uniform", lambda _a, _b: 1.0)

    route = respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=[
            httpx.Response(
                429,
                headers={"X-Rate-Limit-Reset-After": "0"},
                json={"message": "retry"},
            ),
            httpx.Response(
                429,
                headers={"X-Rate-Limit-Reset-After": "0"},
                json={"message": "retry"},
            ),
            httpx.Response(200, json=scan_result_json),
        ],
    )

    async with UrlscopeClient(
        api_key=api_key,
        base_url=test_base_url,
        max_retries=3,
    ) as client:
        result = await client.get_result("scan-123")

    assert isinstance(result, ScanResult)
    assert len(route.calls) == 3
    assert sleep_calls == [0.0, 0.0]


@pytest.mark.asyncio
async def test_max_retries_exceeded_raises_rate_limit_error_with_attrs(
    api_key: str,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_base_url: str,
    respx_mock,
) -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(http_module.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(http_module.random, "uniform", lambda _a, _b: 1.0)
    caplog.set_level(logging.WARNING, logger="urlscope")

    rate_limited = httpx.Response(
        429,
        headers={
            "X-Rate-Limit-Reset-After": "1.5",
            "X-Rate-Limit-Scope": "global",
            "X-Rate-Limit-Window": "minute",
        },
        json={"message": "Rate limit exceeded"},
    )
    route = respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=[rate_limited, rate_limited]
    )

    async with UrlscopeClient(
        api_key=api_key,
        base_url=test_base_url,
        max_retries=1,
    ) as client:
        with pytest.raises(RateLimitError) as exc_info:
            await client.get_result("scan-123")

    assert exc_info.value.retry_after == 1.5
    assert exc_info.value.scope == "global"
    assert exc_info.value.window == "minute"
    assert sleep_calls == [1.5]
    assert len(route.calls) == 2
    assert "Rate limit exhausted after 1 retries" in caplog.text
