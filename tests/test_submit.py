import httpx
import pytest

from urlscope import SubmissionResponse, ValidationError


@pytest.mark.asyncio
async def test_submit_public_visibility_returns_submission_response(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_json,
) -> None:
    route = respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_json)
    )

    result = await mock_client.submit("https://example.com", visibility="public")

    assert isinstance(result, SubmissionResponse)
    assert result.uuid == "scan-123"
    assert result.result == "https://urlscan.io/result/scan-123/"
    assert result.visibility == "public"
    assert route.called


@pytest.mark.asyncio
async def test_submit_private_visibility_returns_submission_response(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_json,
) -> None:
    private_response = {**submission_response_json, "visibility": "private"}
    route = respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=private_response)
    )

    result = await mock_client.submit("https://example.com", visibility="private")

    assert isinstance(result, SubmissionResponse)
    assert result.visibility == "private"
    assert result.url == "https://example.com"
    assert route.called


@pytest.mark.asyncio
async def test_submit_with_all_optional_params(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_json,
) -> None:
    route = respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_json)
    )

    result = await mock_client.submit(
        "https://example.com",
        visibility="public",
        tags=["investigation", "phishing"],
        custom_agent="ExampleAgent/1.0",
        referer="https://referrer.example",
        override_safety=True,
        country="US",
    )

    assert isinstance(result, SubmissionResponse)
    assert route.called
    assert route.calls.last is not None
    assert route.calls.last.request.content == (
        b'{"url":"https://example.com","visibility":"public","tags":["investigation","phishing"],'
        b'"customagent":"ExampleAgent/1.0","referer":"https://referrer.example",'
        b'"overrideSafety":true,"country":"US"}'
    )


@pytest.mark.asyncio
async def test_submit_with_more_than_ten_tags_raises_value_error(
    mock_client,
) -> None:
    with pytest.raises(ValueError):
        await mock_client.submit(
            "https://example.com",
            tags=[f"tag-{index}" for index in range(11)],
        )


@pytest.mark.asyncio
async def test_submit_invalid_url_raises_validation_error(
    mock_client,
    respx_mock,
    test_base_url,
    validation_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=validation_error_response
    )

    with pytest.raises(ValidationError):
        await mock_client.submit("invalid-url", visibility="public")
