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
    assert result.page.url == "https://example.com/landing"
    assert result.verdicts is not None
    assert result.verdicts.score == 5


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
