import asyncio
import logging
import time
from typing import Any, Literal

from ._exceptions import NotFoundError, ScanDeletedError, ScanTimeoutError
from ._http import _HTTPTransport
from .models import ScanResult, SearchResponse, SubmissionResponse

LOGGER = logging.getLogger("urlscope")


class UrlscopeClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://urlscan.io",
        timeout: float = 30.0,
        max_retries: int = 5,
    ) -> None:
        self._transport = _HTTPTransport(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def __aenter__(self) -> "UrlscopeClient":
        await self._transport.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self._transport.__aexit__(exc_type, exc, tb)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def submit(
        self,
        url: str,
        *,
        visibility: Literal["public", "unlisted", "private"] | None = None,
        tags: list[str] | None = None,
        custom_agent: str | None = None,
        referer: str | None = None,
        override_safety: bool | None = None,
        country: str | None = None,
    ) -> SubmissionResponse:
        if tags is not None and len(tags) > 10:
            raise ValueError("tags must contain at most 10 items")

        payload = {
            "url": url,
            "visibility": visibility,
            "tags": tags,
            "customagent": custom_agent,
            "referer": referer,
            "overrideSafety": override_safety,
            "country": country,
        }
        response = await self._transport._request(
            "POST",
            "/api/v1/scan/",
            json={key: value for key, value in payload.items() if value is not None},
        )
        return SubmissionResponse.model_validate(response.json())

    async def get_result(self, uuid: str) -> ScanResult:
        response = await self._transport._request("GET", f"/api/v1/result/{uuid}/")
        return ScanResult.model_validate(response.json())

    async def search(
        self,
        query: str = "*",
        *,
        size: int = 100,
        search_after: list[Any] | None = None,
    ) -> SearchResponse:
        params: dict[str, Any] = {
            "q": query,
            "size": size,
        }
        if search_after is not None:
            params["search_after"] = search_after

        response = await self._transport._request(
            "GET",
            "/api/v1/search/",
            params=params,
        )
        return SearchResponse.model_validate(response.json())

    async def submit_and_wait(
        self,
        url: str,
        *,
        visibility: Literal["public", "unlisted", "private"] | None = None,
        tags: list[str] | None = None,
        custom_agent: str | None = None,
        referer: str | None = None,
        override_safety: bool | None = None,
        country: str | None = None,
        poll_interval: float = 5.0,
        initial_wait: float = 10.0,
        poll_timeout: float = 300.0,
    ) -> ScanResult:
        submission = await self.submit(
            url,
            visibility=visibility,
            tags=tags,
            custom_agent=custom_agent,
            referer=referer,
            override_safety=override_safety,
            country=country,
        )
        started_at = time.monotonic()

        if initial_wait > 0:
            LOGGER.debug(
                "Waiting %.3f seconds before polling result for scan %s",
                initial_wait,
                submission.uuid,
            )
            await asyncio.sleep(initial_wait)

        while True:
            elapsed = time.monotonic() - started_at
            if elapsed > poll_timeout:
                raise ScanTimeoutError(
                    f"Scan {submission.uuid} still pending after {poll_timeout} seconds",
                    uuid=submission.uuid,
                )

            try:
                LOGGER.debug("Polling result for scan %s", submission.uuid)
                return await self.get_result(submission.uuid)
            except NotFoundError:
                LOGGER.debug("Scan %s is still pending", submission.uuid)
                await asyncio.sleep(poll_interval)
            except ScanDeletedError:
                raise
