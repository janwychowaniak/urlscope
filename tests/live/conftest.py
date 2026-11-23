"""Fixtures and reporting for tests against the live urlscan.io API.

The tests under tests/live carry the ``live`` marker and are deselected by default
(``addopts`` in pyproject.toml). Run them with the real key from ``.env``::

    uv run --env-file .env pytest -m live

They never print the key. Do not add ``--showlocals``: a traceback through the
transport's constructor could then show it.
"""

import os
from collections import defaultdict
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
from pydantic import BaseModel

from urlscope import UrlscopeClient

# Sections urlscan returns only for some scans, in shapes that vary between scans.
# The models keep them untyped on purpose (they stay reachable via model_extra),
# so the summary leaves them out and lists only names that are not here: a name in
# the summary is a field the models have not seen before.
KNOWN_UNMODELED: dict[str, frozenset[str]] = {
    "ScanResult": frozenset({"metatags"}),
    "SearchResponse.results[]": frozenset(
        {
            "clipboard",
            "dom",
            "frames",
            "image",
            "links",
            "meta",
            "scanner",
            "team",
            "text",
            "verdicts",
            "websockets",
        }
    ),
}

_unmodeled: dict[str, set[str]] = defaultdict(set)
_notes: list[str] = []


def _collect_unmodeled(model: BaseModel, path: str) -> None:
    extra = set(model.model_extra or {}) - KNOWN_UNMODELED.get(path, frozenset())
    if extra:
        _unmodeled[path].update(extra)
    for name in type(model).model_fields:
        value = getattr(model, name)
        if isinstance(value, BaseModel):
            _collect_unmodeled(value, f"{path}.{name}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, BaseModel):
                    _collect_unmodeled(item, f"{path}.{name}[]")


@pytest.fixture(autouse=True, scope="session")
def _require_api_key() -> None:
    # Fail rather than skip: a live run without a key must not look green.
    if not os.environ.get("URLSCAN_API_KEY"):
        pytest.fail(
            "URLSCAN_API_KEY is not set; run: uv run --env-file .env pytest -m live"
        )


@pytest.fixture
def record_unmodeled() -> Callable[[BaseModel, str], None]:
    """Record keys a live response carried beyond the typed model (report only)."""
    return _collect_unmodeled


@pytest.fixture
def note() -> Callable[[str], None]:
    """Add a line to the live API section of the terminal summary."""
    return _notes.append


@pytest_asyncio.fixture
async def live_client() -> AsyncIterator[UrlscopeClient]:
    async with UrlscopeClient() as client:
        yield client


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    if not _unmodeled and not _notes:
        return
    terminalreporter.section("live urlscan API")
    for line in _notes:
        terminalreporter.write_line(line)
    for path in sorted(_unmodeled):
        keys = ", ".join(sorted(_unmodeled[path]))
        terminalreporter.write_line(f"unmodeled at {path}: {keys}")
