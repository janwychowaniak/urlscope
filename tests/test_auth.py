import pytest

from urlscope import AuthenticationError, UrlscopeClient


def test_explicit_api_key_is_used() -> None:
    client = UrlscopeClient(api_key="explicit-key")

    assert client._transport._client.headers["API-Key"] == "explicit-key"


def test_env_var_fallback_is_used_when_no_explicit_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("URLSCAN_API_KEY", "env-key")

    client = UrlscopeClient()

    assert client._transport._client.headers["API-Key"] == "env-key"


def test_no_key_raises_authentication_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("URLSCAN_API_KEY", raising=False)

    with pytest.raises(AuthenticationError):
        UrlscopeClient()


def test_explicit_key_overrides_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("URLSCAN_API_KEY", "env-key")

    client = UrlscopeClient(api_key="explicit-key")

    assert client._transport._client.headers["API-Key"] == "explicit-key"
