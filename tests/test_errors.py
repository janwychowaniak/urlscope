import httpx
import pytest

from urlscope import (
    APIError,
    AuthenticationError,
    NotFoundError,
    ScanDeletedError,
    ValidationError,
)


@pytest.mark.asyncio
async def test_submit_400_raises_validation_error_with_message(
    mock_client,
    respx_mock,
    test_base_url,
    validation_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=validation_error_response
    )

    with pytest.raises(ValidationError, match="Validation failed: Invalid URL format"):
        await mock_client.submit("https://example.com")


@pytest.mark.asyncio
async def test_submit_401_raises_authentication_error(
    mock_client,
    respx_mock,
    test_base_url,
    authentication_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=authentication_error_response
    )

    with pytest.raises(AuthenticationError):
        await mock_client.submit("https://example.com")


@pytest.mark.asyncio
async def test_submit_403_raises_authentication_error(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(
            403,
            json={"message": "Forbidden", "description": "Access denied"},
        )
    )

    with pytest.raises(AuthenticationError):
        await mock_client.submit("https://example.com")


@pytest.mark.asyncio
async def test_get_result_404_raises_not_found_error(
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
async def test_get_result_410_raises_scan_deleted_error(
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
async def test_get_result_500_raises_api_error_with_status_code(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=httpx.Response(
            500,
            json={"message": "Internal server error"},
        )
    )

    with pytest.raises(APIError) as exc_info:
        await mock_client.get_result("scan-123")

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_missing_optional_fields_in_partial_result_do_not_crash(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=httpx.Response(
            200,
            json={
                "task": {
                    "uuid": "scan-123",
                    "url": "https://example.com",
                    "time": "2026-03-15T10:00:00+00:00",
                    "visibility": "public",
                },
                "page": {
                    "url": "https://example.com",
                },
            },
        )
    )

    result = await mock_client.get_result("scan-123")

    assert result.verdicts is None
    assert result.lists is None
    assert result.page.mime_type is None


@pytest.mark.asyncio
async def test_httpx_connect_error_propagates_as_is(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    request = httpx.Request("GET", f"{test_base_url}/api/v1/result/scan-123/")
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=httpx.ConnectError("connection lost", request=request)
    )

    with pytest.raises(httpx.ConnectError, match="connection lost"):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_httpx_timeout_exception_propagates_as_is(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    request = httpx.Request("GET", f"{test_base_url}/api/v1/result/scan-123/")
    respx_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=httpx.ReadTimeout("timed out", request=request)
    )

    with pytest.raises(httpx.TimeoutException, match="timed out"):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_submit_400_uses_nested_error_description_when_needed(
    mock_client,
    respx_mock,
    test_base_url,
    submission_override_safety_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=submission_override_safety_error_response
    )

    with pytest.raises(
        ValidationError,
        match='ValidationError: "overrideSafety" must be a string',
    ):
        await mock_client.submit("https://example.com", override_safety="true")
