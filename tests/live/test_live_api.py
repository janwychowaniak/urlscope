"""Tests against the live urlscan.io API (marker ``live``, see conftest.py).

Each run makes two private scans of https://example.com, tagged
``urlscope-live-test``: one through ``submit``, one through the sync client's
``submit_and_wait``. The tests fail on HTTP errors and on responses that no longer
fit the models; fields the models do not type are only reported in the summary.

urlscan sometimes produces no screenshot for a finished scan and answers its
screenshot URL with 404 and a placeholder PNG. The screenshot test then checks the
endpoint on recent public scans instead and notes it in the summary.
"""

import uuid
from collections.abc import Callable

import pytest
from pydantic import BaseModel

from urlscope import (
    AuthenticationError,
    NotFoundError,
    QuotaInfo,
    ScanResult,
    SearchResponse,
    SubmissionResponse,
    SyncClient,
    UrlscopeClient,
)

pytestmark = pytest.mark.live

LIVE_URL = "https://example.com"
LIVE_TAG = "urlscope-live-test"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

Recorder = Callable[[BaseModel, str], None]


@pytest.fixture(scope="module")
def live_result() -> ScanResult:
    """One private scan through the sync client, shared by the tests below."""
    with SyncClient() as client:
        return client.submit_and_wait(LIVE_URL, visibility="private", tags=[LIVE_TAG])


async def test_submit_returns_submission_response(
    live_client: UrlscopeClient,
    record_unmodeled: Recorder,
    note: Callable[[str], None],
) -> None:
    submission = await live_client.submit(
        LIVE_URL, visibility="private", tags=[LIVE_TAG]
    )
    record_unmodeled(submission, "SubmissionResponse")
    note(f"submitted scan {submission.uuid} (private, not awaited)")

    assert isinstance(submission, SubmissionResponse)
    assert submission.visibility == "private"
    assert submission.url.startswith(LIVE_URL)
    uuid.UUID(submission.uuid)
    assert submission.result.endswith(f"/result/{submission.uuid}/")
    assert submission.api.endswith(f"/api/v1/result/{submission.uuid}/")


def test_submit_and_wait_returns_private_scan_result(
    live_result: ScanResult,
    record_unmodeled: Recorder,
    note: Callable[[str], None],
) -> None:
    record_unmodeled(live_result, "ScanResult")
    note(f"awaited scan {live_result.task.uuid} (private, sync client)")

    assert live_result.task.visibility == "private"
    assert live_result.task.url.startswith(LIVE_URL)
    assert live_result.page.url.startswith(LIVE_URL)
    assert LIVE_TAG in (live_result.task.tags or [])


async def test_get_result_returns_the_same_scan(
    live_client: UrlscopeClient, live_result: ScanResult
) -> None:
    result = await live_client.get_result(live_result.task.uuid)

    assert result.task.uuid == live_result.task.uuid


async def _public_scan_screenshot(client: UrlscopeClient) -> tuple[str, bytes]:
    """Screenshot of a recent public example.com scan that has one."""
    response = await client.search("domain:example.com", size=5)
    for item in response.results:
        try:
            return item.id, await client.get_screenshot(item.id)
        except NotFoundError:
            continue
    pytest.fail("no screenshot for 5 recent public example.com scans either")


async def test_get_screenshot_returns_png(
    live_client: UrlscopeClient,
    live_result: ScanResult,
    note: Callable[[str], None],
) -> None:
    scan_id = live_result.task.uuid
    try:
        screenshot = await live_client.get_screenshot(scan_id)
    except NotFoundError:
        public_id, screenshot = await _public_scan_screenshot(live_client)
        note(f"no screenshot for scan {scan_id}; checked public scan {public_id}")

    assert screenshot.startswith(PNG_SIGNATURE)


async def test_get_dom_returns_html(
    live_client: UrlscopeClient, live_result: ScanResult
) -> None:
    dom = await live_client.get_dom(live_result.task.uuid)

    # urlscan serialises the document without its <html> wrapper
    assert "<head" in dom.lower()


async def test_search_returns_typed_results_and_paginates(
    live_client: UrlscopeClient, record_unmodeled: Recorder
) -> None:
    query = "domain:example.com"
    first = await live_client.search(query, size=2)
    record_unmodeled(first, "SearchResponse")

    assert isinstance(first, SearchResponse)
    assert first.has_more, "expected more than one page of public example.com scans"
    assert first.results and first.results[-1].sort

    second = await live_client.search(
        query, size=2, search_after=first.results[-1].sort
    )
    record_unmodeled(second, "SearchResponse")

    assert second.results
    assert {item.id for item in first.results}.isdisjoint(
        item.id for item in second.results
    )


async def test_get_quotas_flattens_windows(
    live_client: UrlscopeClient, record_unmodeled: Recorder
) -> None:
    info = await live_client.get_quotas()
    record_unmodeled(info, "QuotaInfo")

    assert isinstance(info, QuotaInfo)
    assert info.quotas
    assert {quota.window for quota in info.quotas} <= {"minute", "hour", "day"}
    assert any(quota.action == "private" for quota in info.quotas)


async def test_unknown_scan_raises_not_found(live_client: UrlscopeClient) -> None:
    with pytest.raises(NotFoundError):
        await live_client.get_result(str(uuid.uuid4()))


async def test_unknown_api_key_raises_authentication_error() -> None:
    # a well-formed key that does not exist: urlscan answers 401
    async with UrlscopeClient(api_key=str(uuid.uuid4())) as client:
        with pytest.raises(AuthenticationError):
            await client.get_quotas()


async def test_malformed_api_key_raises_authentication_error() -> None:
    # a malformed key: urlscan answers 400 "Invalid API key format", which the
    # transport maps by its message; this fails if urlscan rewords it
    async with UrlscopeClient(api_key="not-a-valid-key-format") as client:
        with pytest.raises(AuthenticationError, match="Invalid API key format"):
            await client.get_quotas()
