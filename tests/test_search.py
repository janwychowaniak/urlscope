import httpx
import pytest

from urlscope import SearchResponse


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

    response = await mock_client.search("domain:en.wikipedia.org")

    assert isinstance(response, SearchResponse)
    assert response.total == 10000
    assert response.took == 283
    assert response.has_more is True

    first = response.results[0]
    assert first.id == "019d8797-4e79-776f-af3d-53e92918fc3a"
    assert first.score is None
    assert first.result == (
        "https://urlscan.io/api/v1/result/019d8797-4e79-776f-af3d-53e92918fc3a/"
    )
    assert first.screenshot == (
        "https://urlscan.io/screenshots/019d8797-4e79-776f-af3d-53e92918fc3a.png"
    )
    assert first.page is not None
    assert first.page["domain"] == "es.wikipedia.org"
    assert first.task is not None
    assert first.task["uuid"] == first.id
    assert first.stats is not None
    assert first.stats["requests"] == 47
    assert first.submitter == {}
    assert route.calls.last is not None
    assert str(route.calls.last.request.url) == (
        f"{test_base_url}/api/v1/search/?q=domain%3Aen.wikipedia.org&size=100"
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

    response = await mock_client.search("domain:en.wikipedia.org", size=10)

    assert isinstance(response, SearchResponse)
    assert route.calls.last is not None
    assert str(route.calls.last.request.url) == (
        f"{test_base_url}/api/v1/search/?q=domain%3Aen.wikipedia.org&size=10"
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
        "domain:en.wikipedia.org",
        size=10,
        search_after=[1776096341115, "019d8797-4e79-776f-af3d-53e92918fc3a"],
    )

    assert isinstance(response, SearchResponse)
    assert route.calls.last is not None
    assert route.calls.last.request.url.params["search_after"] == (
        "1776096341115,019d8797-4e79-776f-af3d-53e92918fc3a"
    )


@pytest.mark.asyncio
async def test_search_with_datasource_and_collapse(
    mock_client,
    respx_mock,
    test_base_url,
    search_response_json,
) -> None:
    route = respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(200, json=search_response_json)
    )

    response = await mock_client.search(
        "domain:en.wikipedia.org",
        size=10,
        datasource="scans",
        collapse="page.domain.keyword",
    )

    assert isinstance(response, SearchResponse)
    assert route.calls.last is not None
    params = route.calls.last.request.url.params
    assert params["datasource"] == "scans"
    assert params["collapse"] == "page.domain.keyword"


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
    assert str(route.calls.last.request.url) == (
        f"{test_base_url}/api/v1/search/?q=%2A&size=100"
    )


@pytest.mark.asyncio
async def test_search_empty_results(
    mock_client,
    respx_mock,
    test_base_url,
    empty_search_response_json,
) -> None:
    respx_mock.get(f"{test_base_url}/api/v1/search/").mock(
        return_value=httpx.Response(200, json=empty_search_response_json)
    )

    response = await mock_client.search("domain:no-results.example")

    assert isinstance(response, SearchResponse)
    assert response.results == []
    assert response.total == 0
    assert response.took == 36
    assert response.has_more is False


def test_search_model_preserves_unmodeled_optional_sections(
    malicious_search_response_json,
) -> None:
    response = SearchResponse.model_validate(malicious_search_response_json)
    item = response.results[0]

    assert item.id == "a02f0630-01d6-414b-9648-c959ebce5c39"
    assert item.page is not None
    assert item.page["domain"] == "allegrolokalnie.pl-632462.icu"
    assert item.task is not None
    assert item.task["tags"] == ["falconsandbox"]
    assert item.model_extra["verdicts"]["score"] == 100
    assert item.model_extra["verdicts"]["urlscan"]["malicious"] is True


def test_ip_search_model_parses_live_shaped_item(ip_search_response_json) -> None:
    response = SearchResponse.model_validate(ip_search_response_json)
    item = response.results[0]

    assert response.total == 22
    assert item.page is not None
    assert item.page["ip"] == "185.112.102.233"
    assert item.task is not None
    assert item.task["source"] == "urlhaus"
