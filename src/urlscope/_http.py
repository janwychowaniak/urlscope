import asyncio
import logging
import os
import random
from typing import Any

import httpx

from ._exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ScanDeletedError,
    ValidationError,
)

LOGGER = logging.getLogger("urlscope")
if not LOGGER.handlers:
    LOGGER.addHandler(logging.NullHandler())


class _HTTPTransport:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://urlscan.io",
        timeout: float = 30.0,
        max_retries: int = 5,
    ) -> None:
        resolved_api_key = api_key or os.getenv("URLSCAN_API_KEY")
        if not resolved_api_key:
            raise AuthenticationError(
                "API key is required. Pass api_key or set URLSCAN_API_KEY."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"API-Key": resolved_api_key},
        )

    async def __aenter__(self) -> "_HTTPTransport":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self._client.__aexit__(exc_type, exc, tb)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        retries = 0

        while True:
            response = await self._client.request(method, path, **kwargs)

            if response.status_code == 429:
                if retries >= self.max_retries:
                    retry_after = self._parse_retry_after(response)
                    scope = response.headers.get("X-Rate-Limit-Scope")
                    window = response.headers.get("X-Rate-Limit-Window")
                    LOGGER.warning(
                        "Rate limit exhausted after %s retries for %s %s",
                        retries,
                        method,
                        path,
                    )
                    raise RateLimitError(
                        self._extract_error_message(response),
                        retry_after=retry_after,
                        scope=scope,
                        window=window,
                    )

                retries += 1
                delay = self._compute_retry_delay(response, retries)
                LOGGER.debug(
                    "Retrying %s %s after HTTP 429 in %.3f seconds (attempt %s/%s)",
                    method,
                    path,
                    delay,
                    retries,
                    self.max_retries,
                )
                await asyncio.sleep(delay)
                continue

            self._raise_for_status(response)
            return response

    def _raise_for_status(self, response: httpx.Response) -> None:
        status_code = response.status_code
        if status_code < 400:
            return

        message = self._extract_error_message(response)
        if status_code == 400:
            raise ValidationError(message)
        if status_code in {401, 403}:
            raise AuthenticationError(message)
        if status_code == 404:
            raise NotFoundError(message)
        if status_code == 410:
            raise ScanDeletedError(message)
        raise APIError(status_code, message)

    def _compute_retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = self._parse_retry_after(response)
        if retry_after is not None:
            base_delay = retry_after
        else:
            base_delay = 2.0 * (2 ** (attempt - 1))

        jitter_multiplier = random.uniform(0.75, 1.25)
        return max(0.0, base_delay * jitter_multiplier)

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> float | None:
        raw_value = response.headers.get("X-Rate-Limit-Reset-After")
        if raw_value is None:
            return None

        try:
            return float(raw_value)
        except ValueError:
            return None

    @staticmethod
    def _extract_error_message(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            message = payload.get("message")
            description = payload.get("description")
            detail = payload.get("detail")

            if isinstance(message, str) and message:
                for extra in (description, detail):
                    if isinstance(extra, str) and extra and extra != message:
                        return f"{message}: {extra}"
                return message

            for key in ("description", "detail", "error"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value

            errors = payload.get("errors")
            if isinstance(errors, list):
                for error in errors:
                    if not isinstance(error, dict):
                        continue

                    title = error.get("title")
                    for key in ("description", "detail"):
                        value = error.get(key)
                        if isinstance(value, str) and value:
                            if isinstance(title, str) and title and title != value:
                                return f"{title}: {value}"
                            return value

                    if isinstance(title, str) and title:
                        return title

        if response.text:
            return response.text

        return f"HTTP {response.status_code}"
