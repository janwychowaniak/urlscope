import httpx
import pytest

from urlscope import NotFoundError, ScanDeletedError, ScanResult, ScanTimeoutError


@pytest.mark.asyncio
async def test_get_result_with_valid_uuid_returns_scan_result(
    mock_client,
    respx_mock,
    test_base_url,
    scan_result_json,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=httpx.Response(200, json=scan_result_json)
    )

    result = await mock_client.get_result("scan-123")

    assert isinstance(result, ScanResult)
    assert result.task.uuid == "scan-123"
    assert result.task.report_url == "https://urlscan.io/result/scan-123/"
    assert result.page.url == "https://malicious.example.test/oferta/session-token"
    assert result.verdicts is not None
    assert result.verdicts.overall is not None
    assert result.verdicts.overall.score == 100
    assert result.verdicts.urlscan is not None
    assert result.verdicts.urlscan.brands is not None
    assert result.verdicts.urlscan.brands[0].key == "allegrolokalnie"
    assert result.verdicts.engines is not None
    assert result.verdicts.engines.malicious_total == 0
    assert result.verdicts.community is not None
    assert result.verdicts.community.votes_total == 0


@pytest.mark.asyncio
async def test_get_result_with_pending_scan_raises_not_found_error(
    mock_client,
    respx_mock,
    test_base_url,
    not_found_error_response,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=not_found_error_response
    )

    with pytest.raises(NotFoundError):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_get_result_with_deleted_scan_raises_scan_deleted_error(
    mock_client,
    respx_mock,
    test_base_url,
    scan_deleted_error_response,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=scan_deleted_error_response
    )

    with pytest.raises(ScanDeletedError):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_submit_and_wait_polls_until_result_is_ready(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_json,
    scan_result_json,
    not_found_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_json)
    )
    route = respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=[
            not_found_error_response,
            httpx.Response(200, json=scan_result_json),
        ]
    )

    result = await mock_client.submit_and_wait(
        "https://example.com",
        initial_wait=0,
        poll_interval=0,
        poll_timeout=1,
    )

    assert isinstance(result, ScanResult)
    assert result.task.uuid == "scan-123"
    assert len(route.calls) == 2


@pytest.mark.asyncio
async def test_submit_and_wait_times_out_when_scan_stays_pending(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_json,
    not_found_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_json)
    )
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=not_found_error_response
    )

    with pytest.raises(ScanTimeoutError) as exc_info:
        await mock_client.submit_and_wait(
            "https://example.com",
            initial_wait=0,
            poll_interval=0,
            poll_timeout=0,
        )

    assert exc_info.value.uuid == "scan-123"


@pytest.mark.asyncio
async def test_submit_and_wait_raises_scan_deleted_error_during_poll(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_json,
    scan_deleted_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_json)
    )
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=[scan_deleted_error_response]
    )

    with pytest.raises(ScanDeletedError):
        await mock_client.submit_and_wait(
            "https://example.com",
            initial_wait=0,
            poll_interval=0,
            poll_timeout=1,
        )


def test_scan_result_parses_multiple_live_shaped_fixtures(
    clean_scan_result_json,
    scored_scan_result_json,
    scan_result_json,
) -> None:
    clean_result = ScanResult.model_validate(clean_scan_result_json)
    scored_result = ScanResult.model_validate(scored_scan_result_json)
    malicious_result = ScanResult.model_validate(scan_result_json)

    assert clean_result.verdicts is not None
    assert clean_result.verdicts.overall is not None
    assert clean_result.verdicts.overall.score == 0

    assert scored_result.verdicts is not None
    assert scored_result.verdicts.overall is not None
    assert scored_result.verdicts.overall.score == 60
    assert scored_result.verdicts.urlscan is not None
    assert scored_result.verdicts.urlscan.brands is not None
    assert scored_result.verdicts.urlscan.brands[0].name == "Example Brand"

    assert malicious_result.verdicts is not None
    assert malicious_result.verdicts.engines is not None
    assert malicious_result.verdicts.engines.tags == [
        "urlscan-ml",
        "urlscan-ml-60c5e22",
    ]


def test_scan_result_preserves_unmodeled_nested_fields(scan_result_json) -> None:
    result = ScanResult.model_validate(scan_result_json)

    assert result.verdicts is not None
    assert result.verdicts.engines is not None
    assert result.verdicts.engines.model_extra == {"emergingSignal": "high"}
