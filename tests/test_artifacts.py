import httpx
import pytest

from urlscope import NotFoundError
from urlscope.models import ScanResult


@pytest.mark.asyncio
async def test_get_screenshot_returns_bytes(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    respx_mock.get(f"{test_base_url}/screenshots/scan-123.png").mock(
        return_value=httpx.Response(200, content=b"\x89PNG\r\n\x1a\nmock")
    )

    screenshot = await mock_client.get_screenshot("scan-123")

    assert screenshot == b"\x89PNG\r\n\x1a\nmock"


@pytest.mark.asyncio
async def test_get_dom_returns_string(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    respx_mock.get(f"{test_base_url}/dom/scan-123/").mock(
        return_value=httpx.Response(200, text="<html><body>mock</body></html>")
    )

    dom = await mock_client.get_dom("scan-123")

    assert dom == "<html><body>mock</body></html>"


@pytest.mark.asyncio
async def test_get_screenshot_for_invalid_uuid_raises_error(
    mock_client,
    respx_mock,
    test_base_url,
    not_found_error_response,
) -> None:
    respx_mock.get(f"{test_base_url}/screenshots/invalid-uuid.png").mock(
        return_value=not_found_error_response
    )

    with pytest.raises(NotFoundError):
        await mock_client.get_screenshot("invalid-uuid")


def test_certificate_chain_accessible_from_scan_result_model(
    scan_result_json,
) -> None:
    result = ScanResult.model_validate(scan_result_json)

    assert result.lists is not None
    assert result.lists.certificates is not None
    assert len(result.lists.certificates) == 1
    assert result.lists.certificates[0].subject_name == "malicious.example.test"
    assert result.lists.certificates[0].issuer == "WE1"
    assert result.lists.certificates[0].valid_from is not None
    assert result.lists.certificates[0].valid_from.year == 2026
