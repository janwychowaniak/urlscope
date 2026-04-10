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
    assert result.uuid == "019d789c-c97f-7483-9af5-4bc79125ebdc"
    assert result.result == "https://urlscan.io/result/019d789c-c97f-7483-9af5-4bc79125ebdc/"
    assert result.visibility == "public"
    assert result.options == {}
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

    result = await mock_client.submit(
        "https://en.wikipedia.org/wiki/Main_Page",
        visibility="private",
    )

    assert isinstance(result, SubmissionResponse)
    assert result.visibility == "private"
    assert result.url == "https://en.wikipedia.org/wiki/Main_Page"
    assert route.called


@pytest.mark.asyncio
async def test_submit_with_all_optional_params(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_optional_json,
) -> None:
    route = respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_optional_json)
    )

    result = await mock_client.submit(
        "https://en.wikipedia.org/wiki/Main_Page",
        visibility="public",
        tags=["audit", "submission"],
        custom_agent="urlscope-audit/1.0",
        referer="https://example.com/ref",
        override_safety=True,
        country="de",
    )

    assert isinstance(result, SubmissionResponse)
    assert result.country == "de"
    assert result.options == {
        "headers": {"referer": "https://example.com/ref"},
        "useragent": "urlscope-audit/1.0",
    }
    assert route.called
    assert route.calls.last is not None
    assert route.calls.last.request.content == (
        b'{"url":"https://en.wikipedia.org/wiki/Main_Page","visibility":"public","tags":["audit","submission"],'
        b'"customagent":"urlscope-audit/1.0","referer":"https://example.com/ref",'
        b'"overrideSafety":"true","country":"de"}'
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
async def test_submit_dns_rejection_raises_validation_error(
    mock_client,
    respx_mock,
    test_base_url,
    submission_dns_error_response,
) -> None:
    respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=submission_dns_error_response
    )

    with pytest.raises(
        ValidationError,
        match=(
            "DNS Error - Could not resolve domain: "
            "The domain allegrolokalnie\\.pl-632462\\.icu could not be resolved"
        ),
    ):
        await mock_client.submit(
            "https://allegrolokalnie.pl-632462.icu/oferta/WtjvlLrQofZyCc1-jSpGWbBbcFBALNh-qQMrx4qU2aT1Ifv/19",
            visibility="public",
        )


@pytest.mark.asyncio
async def test_submit_override_safety_string_passes_through(
    mock_client,
    respx_mock,
    test_base_url,
    submission_response_optional_json,
) -> None:
    route = respx_mock.post(f"{test_base_url}/api/v1/scan/").mock(
        return_value=httpx.Response(200, json=submission_response_optional_json)
    )

    await mock_client.submit(
        "https://en.wikipedia.org/wiki/Main_Page",
        override_safety="1",
    )

    assert route.calls.last is not None
    assert route.calls.last.request.content == (
        b'{"url":"https://en.wikipedia.org/wiki/Main_Page","overrideSafety":"1"}'
    )
