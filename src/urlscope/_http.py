import asyncio
import logging
import os
import random
from typing import Any

import httpx2

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

# urlscan answers a malformed API key with 400 and this message instead of 401;
# tests/live checks that the message still reads this way.
_INVALID_API_KEY_FORMAT = "Invalid API key format"

# A non-JSON error body goes into the exception message only when it is text, and
# only this many characters of it: urlscan answers a missing screenshot with 404 and
# a PNG, and proxies answer 5xx with whole HTML pages.
_MAX_ERROR_BODY_CHARS = 300
_TEXTUAL_MEDIA_TYPES = {"application/json", "application/xml", "application/javascript"}


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
        self._client = httpx2.AsyncClient(
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
    ) -> httpx2.Response:
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

    def _raise_for_status(self, response: httpx2.Response) -> None:
        status_code = response.status_code
        if status_code < 400:
            return

        message = self._extract_error_message(response)
        if status_code == 400:
            if message.startswith(_INVALID_API_KEY_FORMAT):
                raise AuthenticationError(message)
            raise ValidationError(message)
        if status_code in {401, 403}:
            raise AuthenticationError(message)
        if status_code == 404:
            raise NotFoundError(message)
        if status_code == 410:
            raise ScanDeletedError(message)
        raise APIError(status_code, message)

    def _compute_retry_delay(self, response: httpx2.Response, attempt: int) -> float:
        retry_after = self._parse_retry_after(response)
        if retry_after is not None:
            base_delay = retry_after
        else:
            base_delay = 2.0 * (2 ** (attempt - 1))

        jitter_multiplier = random.uniform(0.75, 1.25)
        return max(0.0, base_delay * jitter_multiplier)

    @staticmethod
    def _parse_retry_after(response: httpx2.Response) -> float | None:
        raw_value = response.headers.get("X-Rate-Limit-Reset-After")
        if raw_value is None:
            return None

        try:
            return float(raw_value)
        except ValueError:
            return None

    @staticmethod
    def _extract_error_message(response: httpx2.Response) -> str:
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

        return _describe_body(response)


def _describe_body(response: httpx2.Response) -> str:
    status = f"HTTP {response.status_code}"
    if not response.content:
        return status

    content_type = response.headers.get("content-type", "")
    media_type = content_type.split(";", 1)[0].strip().lower()
    textual = (
        media_type.startswith("text/")
        or media_type in _TEXTUAL_MEDIA_TYPES
        or media_type.endswith(("+json", "+xml"))
    )
    if not media_type:
        try:
            response.content.decode("utf-8")
        except UnicodeDecodeError:
            textual = False
        else:
            textual = True

    if not textual:
        size = len(response.content)
        return f"{status} ({media_type or 'unknown type'}, {size} bytes)"

    text = response.text.strip()
    if not text:
        return status
    if len(text) > _MAX_ERROR_BODY_CHARS:
        return text[:_MAX_ERROR_BODY_CHARS] + "..."
    return text
