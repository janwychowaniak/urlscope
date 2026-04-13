import asyncio
from typing import Any, Literal

from ._client import UrlscopeClient
from .models import QuotaInfo, ScanResult, SearchResponse, SubmissionResponse


class SyncClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://urlscan.io",
        timeout: float = 30.0,
        max_retries: int = 5,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._max_retries = max_retries

    def __enter__(self) -> "SyncClient":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def close(self) -> None:
        return None

    def submit(
        self,
        url: str,
        *,
        visibility: Literal["public", "unlisted", "private"] | None = None,
        tags: list[str] | None = None,
        custom_agent: str | None = None,
        referer: str | None = None,
        override_safety: bool | str | None = None,
        country: str | None = None,
    ) -> SubmissionResponse:
        async def _run() -> SubmissionResponse:
            async with UrlscopeClient(
                self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            ) as client:
                return await client.submit(
                    url,
                    visibility=visibility,
                    tags=tags,
                    custom_agent=custom_agent,
                    referer=referer,
                    override_safety=override_safety,
                    country=country,
                )

        return asyncio.run(_run())

    def get_result(self, uuid: str) -> ScanResult:
        async def _run() -> ScanResult:
            async with UrlscopeClient(
                self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            ) as client:
                return await client.get_result(uuid)

        return asyncio.run(_run())

    def submit_and_wait(
        self,
        url: str,
        *,
        visibility: Literal["public", "unlisted", "private"] | None = None,
        tags: list[str] | None = None,
        custom_agent: str | None = None,
        referer: str | None = None,
        override_safety: bool | str | None = None,
        country: str | None = None,
        poll_interval: float = 5.0,
        initial_wait: float = 10.0,
        poll_timeout: float = 300.0,
    ) -> ScanResult:
        async def _run() -> ScanResult:
            async with UrlscopeClient(
                self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            ) as client:
                return await client.submit_and_wait(
                    url,
                    visibility=visibility,
                    tags=tags,
                    custom_agent=custom_agent,
                    referer=referer,
                    override_safety=override_safety,
                    country=country,
                    poll_interval=poll_interval,
                    initial_wait=initial_wait,
                    poll_timeout=poll_timeout,
                )

        return asyncio.run(_run())

    def search(
        self,
        query: str = "*",
        *,
        size: int = 100,
        search_after: list[Any] | None = None,
        datasource: Literal[
            "scans",
            "hostnames",
            "incidents",
            "notifications",
            "certificates",
        ]
        | None = None,
        collapse: str | None = None,
    ) -> SearchResponse:
        async def _run() -> SearchResponse:
            async with UrlscopeClient(
                self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            ) as client:
                return await client.search(
                    query,
                    size=size,
                    search_after=search_after,
                    datasource=datasource,
                    collapse=collapse,
                )

        return asyncio.run(_run())

    def get_screenshot(self, uuid: str) -> bytes:
        async def _run() -> bytes:
            async with UrlscopeClient(
                self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            ) as client:
                return await client.get_screenshot(uuid)

        return asyncio.run(_run())

    def get_dom(self, uuid: str) -> str:
        async def _run() -> str:
            async with UrlscopeClient(
                self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            ) as client:
                return await client.get_dom(uuid)

        return asyncio.run(_run())

    def get_quotas(self) -> QuotaInfo:
        async def _run() -> QuotaInfo:
            async with UrlscopeClient(
                self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            ) as client:
                return await client.get_quotas()

        return asyncio.run(_run())
