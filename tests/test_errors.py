import httpx
import httpx2
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
    httpx2_mock,
    test_base_url,
    validation_error_response,
) -> None:
    httpx2_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=validation_error_response
    )

    with pytest.raises(ValidationError, match="Validation failed: Invalid URL format"):
        await mock_client.submit("https://example.com")


@pytest.mark.asyncio
async def test_400_invalid_api_key_format_raises_authentication_error(
    mock_client,
    httpx2_mock,
    test_base_url,
    invalid_api_key_format_response,
) -> None:
    httpx2_mock.get(f"{test_base_url}/api/v1/quotas").mock(
        return_value=invalid_api_key_format_response
    )

    with pytest.raises(AuthenticationError, match="Invalid API key format"):
        await mock_client.get_quotas()


@pytest.mark.asyncio
async def test_submit_401_raises_authentication_error(
    mock_client,
    httpx2_mock,
    test_base_url,
    authentication_error_response,
) -> None:
    httpx2_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=authentication_error_response
    )

    with pytest.raises(AuthenticationError):
        await mock_client.submit("https://example.com")


@pytest.mark.asyncio
async def test_submit_403_raises_authentication_error(
    mock_client,
    httpx2_mock,
    test_base_url,
) -> None:
    httpx2_mock.post(f"{test_base_url}/api/v1/scan/").mock(
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
    httpx2_mock,
    test_base_url,
    not_found_error_response,
) -> None:
    httpx2_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=not_found_error_response
    )

    with pytest.raises(NotFoundError):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_get_result_410_raises_scan_deleted_error(
    mock_client,
    httpx2_mock,
    test_base_url,
    scan_deleted_error_response,
) -> None:
    httpx2_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        return_value=scan_deleted_error_response
    )

    with pytest.raises(ScanDeletedError):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_get_result_500_raises_api_error_with_status_code(
    mock_client,
    httpx2_mock,
    test_base_url,
) -> None:
    httpx2_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
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
    httpx2_mock,
    test_base_url,
) -> None:
    httpx2_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
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
async def test_httpx2_connect_error_propagates_as_is(
    mock_client,
    httpx2_mock,
    test_base_url,
) -> None:
    request = httpx2.Request("GET", f"{test_base_url}/api/v1/result/scan-123/")
    httpx2_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=httpx2.ConnectError("connection lost", request=request)
    )

    with pytest.raises(httpx2.ConnectError, match="connection lost"):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_httpx2_timeout_exception_propagates_as_is(
    mock_client,
    httpx2_mock,
    test_base_url,
) -> None:
    request = httpx2.Request("GET", f"{test_base_url}/api/v1/result/scan-123/")
    httpx2_mock.get(f"{test_base_url}/api/v1/result/scan-123/").mock(
        side_effect=httpx2.ReadTimeout("timed out", request=request)
    )

    with pytest.raises(httpx2.TimeoutException, match="timed out"):
        await mock_client.get_result("scan-123")


@pytest.mark.asyncio
async def test_submit_400_uses_nested_error_description_when_needed(
    mock_client,
    httpx2_mock,
    test_base_url,
    submission_override_safety_error_response,
) -> None:
    httpx2_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=submission_override_safety_error_response
    )

    with pytest.raises(
        ValidationError,
        match='ValidationError: "overrideSafety" must be a string',
    ):
        await mock_client.submit("https://example.com", override_safety="true")


@pytest.mark.asyncio
async def test_binary_error_body_is_summarised_not_dumped(
    mock_client,
    httpx2_mock,
    test_base_url,
    screenshot_placeholder_response,
) -> None:
    httpx2_mock.get(f"{test_base_url}/screenshots/scan-123.png").mock(
        return_value=screenshot_placeholder_response
    )

    with pytest.raises(NotFoundError) as exc_info:
        await mock_client.get_screenshot("scan-123")

    size = len(screenshot_placeholder_response.content)
    assert str(exc_info.value) == f"HTTP 404 (image/png, {size} bytes)"


@pytest.mark.asyncio
async def test_long_text_error_body_is_truncated(
    mock_client,
    httpx2_mock,
    test_base_url,
    html_bad_gateway_response,
) -> None:
    httpx2_mock.get(f"{test_base_url}/api/v1/quotas").mock(
        return_value=html_bad_gateway_response
    )

    with pytest.raises(APIError) as exc_info:
        await mock_client.get_quotas()

    message = str(exc_info.value)
    assert exc_info.value.status_code == 502
    assert message.startswith("<html><body>Bad gateway. Bad gateway.")
    assert message.endswith("...")
    assert len(message) == 300 + len("...")


@pytest.mark.asyncio
async def test_binary_error_body_without_content_type_is_summarised(
    mock_client,
    httpx2_mock,
    test_base_url,
) -> None:
    httpx2_mock.get(f"{test_base_url}/api/v1/quotas").mock(
        return_value=httpx.Response(500, content=b"\xff\xfe\x00binary")
    )

    with pytest.raises(APIError, match=r"^HTTP 500 \(unknown type, 9 bytes\)$"):
        await mock_client.get_quotas()
