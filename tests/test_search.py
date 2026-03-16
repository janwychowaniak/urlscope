import httpx
import pytest

from urlscope import SearchResponse


@pytest.fixture
def search_response_json() -> dict[str, object]:
    return {
        "results": [
            {
                "_id": "scan-123",
                "sort": [1742120000, "scan-123"],
                "page": {"url": "https://example.com"},
                "task": {"visibility": "public"},
                "stats": {"requests": 5},
            }
        ],
        "total": 1,
        "has_more": True,
    }


@pytest.mark.asyncio
async def test_search_with_query_returns_typed_results(
    mock_client,
    respx_mock,
    test_base_url,
    search_response_json,
) -> None:
    route = respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(200, json=search_response_json)
    )

    response = await mock_client.search("domain:example.com")

    assert isinstance(response, SearchResponse)
    assert response.results[0].id == "scan-123"
    assert response.total == 1
    assert response.has_more is True
    assert route.calls.last is not None
    assert str(route.calls.last.request.url) == (
        f"{test_base_url}/api/v1/search/?q=domain%3Aexample.com&size=100"
    )


@pytest.mark.asyncio
async def test_search_with_custom_size(
    mock_client,
    respx_mock,
    test_base_url,
    search_response_json,
) -> None:
    route = respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(200, json=search_response_json)
    )

    response = await mock_client.search("domain:example.com", size=10)

    assert isinstance(response, SearchResponse)
    assert route.calls.last is not None
    assert str(route.calls.last.request.url) == (
        f"{test_base_url}/api/v1/search/?q=domain%3Aexample.com&size=10"
    )


@pytest.mark.asyncio
async def test_search_pagination_via_search_after(
    mock_client,
    respx_mock,
    test_base_url,
    search_response_json,
) -> None:
    route = respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(200, json=search_response_json)
    )

    response = await mock_client.search(
        "domain:example.com",
        size=10,
        search_after=[1742120000, "scan-123"],
    )

    assert isinstance(response, SearchResponse)
    assert route.calls.last is not None
    assert route.calls.last.request.url.params.get_list("search_after") == [
        "1742120000",
        "scan-123",
    ]


@pytest.mark.asyncio
async def test_search_empty_query_defaults_to_wildcard(
    mock_client,
    respx_mock,
    test_base_url,
    search_response_json,
) -> None:
    route = respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(200, json=search_response_json)
    )

    response = await mock_client.search()

    assert isinstance(response, SearchResponse)
    assert route.calls.last is not None
    assert str(route.calls.last.request.url) == f"{test_base_url}/api/v1/search/?q=%2A&size=100"


@pytest.mark.asyncio
async def test_search_empty_results(
    mock_client,
    respx_mock,
    test_base_url,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [],
                "total": 0,
                "has_more": False,
            },
        )
    )

    response = await mock_client.search("domain:no-results.example")

    assert isinstance(response, SearchResponse)
    assert response.results == []
    assert response.total == 0
    assert response.has_more is False
