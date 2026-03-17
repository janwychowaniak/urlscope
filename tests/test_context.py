import pytest

import urlscope
from urlscope import UrlscopeClient


@pytest.mark.asyncio
async def test_async_context_manager_opens_and_closes_properly(api_key: str) -> None:
    client = UrlscopeClient(api_key=api_key)

    async with client as managed_client:
        assert managed_client is client
        assert not client._transport._client.is_closed

    assert client._transport._client.is_closed


@pytest.mark.asyncio
async def test_aclose_works_without_context_manager(api_key: str) -> None:
    client = UrlscopeClient(api_key=api_key)

    await client.aclose()

    assert client._transport._client.is_closed


@pytest.mark.asyncio
async def test_double_close_does_not_raise(api_key: str) -> None:
    client = UrlscopeClient(api_key=api_key)

    await client.aclose()
    await client.aclose()

    assert client._transport._client.is_closed


def test_sync_client_works_as_context_manager(api_key: str) -> None:
    with urlscope.SyncClient(api_key=api_key) as client:
        assert client is not None


def test_sync_client_exit_does_not_raise(api_key: str) -> None:
    with urlscope.SyncClient(api_key=api_key) as client:
        assert client is not None


def test_sync_client_close_is_callable_without_error(api_key: str) -> None:
    client = urlscope.SyncClient(api_key=api_key)

    client.close()
