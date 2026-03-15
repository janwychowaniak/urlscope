class UrlscopeError(Exception):
    """Base exception for all urlscope errors."""


class AuthenticationError(UrlscopeError):
    """Raised when API authentication fails."""


class ValidationError(UrlscopeError):
    """Raised when the API rejects a request as invalid."""


class NotFoundError(UrlscopeError):
    """Raised when a scan is not found or is still pending."""


class ScanDeletedError(UrlscopeError):
    """Raised when a scan has been deleted."""


class RateLimitError(UrlscopeError):
    """Raised when API rate limits are exceeded after retries."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        scope: str | None = None,
        window: str | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.scope = scope
        self.window = window


class ScanTimeoutError(UrlscopeError):
    """Raised when polling exceeds the configured timeout."""

    def __init__(self, message: str, *, uuid: str) -> None:
        super().__init__(message)
        self.uuid = uuid


class APIError(UrlscopeError):
    """Raised for unexpected API HTTP errors."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
