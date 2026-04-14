# Tasks: urlscope — Python Wrapper for urlscan.io API

**Input**: Design documents from `/specs/001-urlscan-api-wrapper/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-api.md

**Tests**: Included — spec requires 100% public API coverage (SC-006).

**Organization**: Tasks grouped by user story. Each story independently implementable after foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US7)
- Exact file paths in every task description

---

## Phase 1: Setup

**Purpose**: Project scaffolding — pyproject.toml, src layout, empty modules, tooling config

- [ ] T001 Create project directory structure: `src/urlscope/`, `src/urlscope/models/`, `tests/`, and marker files `src/urlscope/py.typed`, `LICENSE` (MIT). Create empty `__init__.py` in `src/urlscope/` and `src/urlscope/models/`. Ref: plan.md project structure.
- [ ] T002 Create `pyproject.toml` with hatchling build backend, project metadata (name=urlscope, requires-python>=3.10), runtime dependencies (httpx, pydantic>=2), dev dependencies (pytest, pytest-asyncio, respx, mypy, ruff), and tool config sections for ruff (select=ALL or curated set), mypy (strict=true), pytest (asyncio_mode=auto). Ref: research.md R5.
  **Done when**: `pip install -e ".[dev]"` succeeds and `python -c "import urlscope"` works.

---

## Phase 2: Foundational

**Purpose**: Exception hierarchy + HTTP transport with auth — MUST complete before any user story

- [ ] T003 [P] Implement exception hierarchy in `src/urlscope/_exceptions.py`. Classes: `UrlscopeError` (base), `AuthenticationError`, `ValidationError`, `NotFoundError`, `ScanDeletedError`, `RateLimitError` (with `.retry_after`, `.scope`, `.window` attrs), `ScanTimeoutError` (with `.uuid` attr), `APIError` (with `.status_code`, `.message` attrs). All per contracts/public-api.md Exception Hierarchy. FR-017.
  **Done when**: All exception classes importable, each has correct attributes, inheritance chain is `UrlscopeError → Exception`.

- [ ] T004 [P] Implement HTTP transport layer in `src/urlscope/_http.py`. Internal class wrapping `httpx.AsyncClient` with: `base_url`, `API-Key` header injection, configurable `timeout`, `_request()` method that handles response status codes (maps 400→ValidationError, 401/403→AuthenticationError, 404→NotFoundError, 410→ScanDeletedError, 429→retry with backoff, other 4xx/5xx→APIError). Constructor must resolve API key: 1) explicit `api_key` param (preferred), 2) `URLSCAN_API_KEY` env var fallback, 3) raise `AuthenticationError` at construction time if neither is present. FR-012. Retry logic: parse `X-Rate-Limit-Reset-After` header, fall back to exponential backoff (base 2s, factor 2x, jitter ±25%), max `max_retries` attempts, raise `RateLimitError` on exhaustion. Logger: `logging.getLogger("urlscope")` with `NullHandler`. Log retries at DEBUG, rate limit exhaustion at WARNING. Context manager support (`__aenter__`/`__aexit__` delegating to inner httpx client). FR-012, FR-013, FR-017, FR-019, FR-020. Ref: research.md R1, R4, contracts/public-api.md Rate Limit Handling, API Key Resolution.
  **Done when**: Constructor resolves API key per precedence rules (raises `AuthenticationError` when neither source provides a key); `_request("GET", "/some-path")` correctly sends authenticated requests, retries on 429 with backoff, raises mapped exceptions for error status codes, supports `async with`.

**Checkpoint**: Foundation ready — exceptions, HTTP transport with retry, and auth resolution all working.

---

## Phase 3: User Story 1 — Submit and Retrieve a URL Scan (P1) — MVP

**Goal**: Users can submit a URL for scanning and retrieve the full typed result, either by polling or by UUID.

**Independent Test**: Submit URL → poll → receive typed `ScanResult` with task/page/verdicts fields.

### Models for US1

- [ ] T005 [P] [US1] Implement submission models in `src/urlscope/models/_submission.py`. Classes: `SubmissionResponse` (fields: message, uuid, result, api, visibility, url, country, options). Use `ConfigDict(extra="allow", populate_by_name=True)`. FR-003, FR-016, FR-018. Ref: data-model.md SubmissionResponse.
  **Done when**: `SubmissionResponse.model_validate(sample_json)` parses correctly; unknown fields preserved in `model_extra`.

- [ ] T006 [P] [US1] Implement scan result models in `src/urlscope/models/_result.py`. Classes: `TaskInfo`, `PageInfo`, `Verdicts`, `BrandMatch`, `ScanLists`, `CertificateInfo`, `ScanResult`. All with `ConfigDict(extra="allow", populate_by_name=True)`. Use `Field(alias=...)` for camelCase→snake_case mapping (e.g., `apex_domain` aliased to `apexDomain`). Optional fields default to `None`. FR-005, FR-010, FR-016, FR-018. Ref: data-model.md ScanResult + sub-entities.
  **Done when**: `ScanResult.model_validate(sample_result_json)` parses all typed sections; `model_extra` captures unmodeled fields.

- [ ] T007 [US1] Create models package `__init__.py` at `src/urlscope/models/__init__.py` — re-export model classes from `_submission` and `_result` only. Do NOT add import lines for `_search` or `_quota` at this stage (those modules do not exist yet).
  **Done when**: `from urlscope.models import SubmissionResponse, ScanResult, TaskInfo, PageInfo, Verdicts, BrandMatch, ScanLists, CertificateInfo` works without `ImportError`. No imports from `_search` or `_quota` at this stage.

### Client for US1

- [ ] T008 [US1] Implement async client in `src/urlscope/_client.py`. Class `UrlscopeClient` with constructor (`api_key`, `base_url`, `timeout`, `max_retries`), context manager (`__aenter__`/`__aexit__`/`aclose()`), and methods: `submit(url, *, visibility, tags, custom_agent, referer, override_safety, country) → SubmissionResponse` (POST `/api/v1/scan/`, validates tags<=10), `get_result(uuid) → ScanResult` (GET `/api/v1/result/{uuid}/`), `submit_and_wait(url, *, ..., poll_interval=5.0, initial_wait=10.0, poll_timeout=300.0) → ScanResult` (submit then poll: wait initial_wait, poll every poll_interval, 404=pending, 200=done, 410=ScanDeletedError, timeout=ScanTimeoutError). FR-001, FR-002, FR-003, FR-004, FR-005, FR-014, FR-019. Ref: contracts/public-api.md UrlscopeClient, Polling Behavior.
  **Done when**: All three methods (`submit`, `get_result`, `submit_and_wait`) work end-to-end against the HTTP transport; visibility uses `Literal["public","unlisted","private"] | None`; tags validated; polling handles 404/200/410 correctly.

- [ ] T009 [US1] Create package `__init__.py` at `src/urlscope/__init__.py` — re-export public API: `UrlscopeClient`, all model classes, all exception classes. Add `__version__` string. FR-014. Ref: contracts/public-api.md Package Exports.
  **Done when**: `from urlscope import UrlscopeClient, ScanResult, UrlscopeError` all work.

### Tests for US1

- [ ] T010 [US1] Create test fixtures in `tests/conftest.py`. Fixtures: `api_key` (returns test key string), `mock_client` (async fixture returning `UrlscopeClient` with test key + test base_url), sample JSON response dicts for submission response, scan result (with task/page/verdicts/lists populated), 429 response with rate limit headers, 400/401/404/410 error responses. Use `respx` for HTTP mocking.
  **Done when**: Fixtures importable by all test files; sample JSON matches data-model.md field names.

- [ ] T011 [P] [US1] Write tests in `tests/test_submit.py`. Test cases: submit with public visibility returns `SubmissionResponse` with correct fields; submit with private visibility; submit with all optional params (tags, custom_agent, referer, override_safety, country); submit with >10 tags raises `ValueError`; submit with invalid URL returns `ValidationError` (mock 400). Use respx to mock `POST /api/v1/scan/`. FR-001, FR-002, FR-003.
  **Done when**: All tests pass with `pytest tests/test_submit.py`.

- [ ] T012 [P] [US1] Write tests in `tests/test_result.py`. Test cases: get_result with valid UUID returns `ScanResult` with typed fields; get_result with pending scan raises `NotFoundError` (mock 404); get_result with deleted scan raises `ScanDeletedError` (mock 410); submit_and_wait polls until 200 and returns result; submit_and_wait times out raises `ScanTimeoutError`; submit_and_wait with deleted scan raises `ScanDeletedError` during poll. Use respx to mock `GET /api/v1/result/{uuid}/` with sequential responses. FR-004, FR-005.
  **Done when**: All tests pass with `pytest tests/test_result.py`.

- [ ] T013 [P] [US1] Write tests in `tests/test_auth.py`. Test cases: explicit api_key used; env var fallback when no explicit key (mock env); no key raises `AuthenticationError`; explicit key overrides env var. FR-012.
  **Done when**: All tests pass with `pytest tests/test_auth.py`.

- [ ] T014 [P] [US1] Write tests in `tests/test_errors.py`. Test cases: 400 → `ValidationError` with message; 401 → `AuthenticationError`; 403 → `AuthenticationError`; 404 → `NotFoundError`; 410 → `ScanDeletedError`; 500 → `APIError` with status_code; missing optional fields in response don't crash (partial JSON); `httpx.ConnectError` propagates as-is (not wrapped or masked); `httpx.TimeoutException` propagates as-is. Use respx `side_effect` to raise these exceptions from the mock. FR-017 (covers spec edge case: network connection lost mid-request raises connection error without masking cause), FR-018.
  **Done when**: All tests pass with `pytest tests/test_errors.py`.

- [ ] T015 [P] [US1] Write tests in `tests/test_context.py` (async and sync context managers). Test cases: async context manager opens/closes properly; aclose() works without context manager; double-close doesn't raise. Add sync context manager tests: `SyncClient()` works as context manager via `with SyncClient(api_key=...) as client:`; no exception on `__exit__`; `close()` is callable without error. FR-019.
  **Done when**: All tests pass with `pytest tests/test_context.py`.

**Checkpoint**: MVP complete — submit, retrieve, and poll for URL scans with full typed results, error handling, and auth.

---

## Phase 4: User Story 2 — Search Existing Scans (P2)

**Goal**: Users can search scans using Elasticsearch query syntax with paginated results.

**Independent Test**: Execute search query → receive typed `SearchResponse` with items and pagination.

- [ ] T016 [P] [US2] Implement search models in `src/urlscope/models/_search.py`. Classes: `SearchResultItem` (fields: id aliased from `_id`, score aliased from `_score`, sort, page, task, stats, submitter, result, screenshot), `SearchResponse` (fields: results as `list[SearchResultItem]`, total as `int`, took as optional `int`, has_more as `bool`). Keep `page`, `task`, `stats`, and `submitter` as `dict | None`; preserve less consistent live API sections such as `verdicts`, `dom`, `frames`, `canonical`, `scanner`, `links`, and `text` via `ConfigDict(extra="allow", populate_by_name=True)`. FR-016. Ref: data-model.md SearchResponse/SearchResultItem.
  **Done when**: `SearchResponse.model_validate(sample_search_json)` parses live-shaped search payloads, including empty results and unmodeled optional sections preserved in `model_extra`.

- [ ] T017 [US2] Update `src/urlscope/models/__init__.py` to re-export `SearchResponse`, `SearchResultItem`. Add `search()` method to `UrlscopeClient` in `src/urlscope/_client.py`: `search(query="*", *, size=100, search_after=None, datasource=None, collapse=None) → SearchResponse` (GET `/api/v1/search/` with query params `q`, `size`, comma-serialized `search_after`, optional `datasource`, and optional `collapse`). Update `src/urlscope/__init__.py` exports. FR-006, FR-007.
  **Done when**: `client.search("domain:example.com", size=10)` returns typed `SearchResponse`; pagination via comma-serialized `search_after` works; optional `datasource` and `collapse` are passed through.

- [ ] T018 [P] [US2] Write tests in `tests/test_search.py`. Test cases: search with query returns typed live-shaped results; search with custom size; pagination via comma-serialized `search_after`; optional `datasource` and `collapse`; empty query defaults to wildcard; empty results (total=0, has_more=False); unmodeled optional sections remain available in `model_extra`. Mock `GET /api/v1/search/`. FR-006, FR-007.
  **Done when**: All tests pass with `pytest tests/test_search.py`.

**Checkpoint**: Search with pagination working independently.

---

## Phase 5: User Story 3 — Download Scan Artifacts (P2)

**Goal**: Users can download screenshot (PNG), DOM snapshot (HTML), and certificate data from a completed scan.

**Independent Test**: Provide UUID → receive bytes (screenshot) and string (DOM).

- [ ] T019 [US3] Add artifact methods to `UrlscopeClient` in `src/urlscope/_client.py`: `get_screenshot(uuid) → bytes` (GET `/screenshots/{uuid}.png`, return raw bytes), `get_dom(uuid) → str` (GET `/dom/{uuid}/`, return text). Certificate chain data: extract from `ScanResult.lists.certificates` (no separate endpoint — documented in assumptions). FR-008, FR-009, FR-010.
  **Done when**: `get_screenshot` returns PNG bytes; `get_dom` returns HTML string; certificate data accessible via `result.lists.certificates`.

- [ ] T020 [P] [US3] Write tests in `tests/test_artifacts.py`. Test cases: get_screenshot returns bytes; get_dom returns string; screenshot for invalid UUID raises error (mock 404); certificate chain accessible from ScanResult.lists.certificates model. Mock screenshot/DOM endpoints. FR-008, FR-009, FR-010.
  **Done when**: All tests pass with `pytest tests/test_artifacts.py`.

**Checkpoint**: Artifact download working independently.

---

## Phase 6: User Story 4 — Configure Authentication Flexibly (P2)

**Goal**: API key resolved from explicit param or `URLSCAN_API_KEY` env var with clear precedence.

**Independent Test**: Already covered by T004 (implementation) and T013 (tests) in earlier phases.

No additional tasks — FR-012 fully satisfied by T004 + T013.

---

## Phase 7: User Story 5 — Handle Rate Limits Automatically (P2)

**Goal**: Library automatically retries 429 responses with exponential backoff.

**Independent Test**: Already implemented in T004. Tests needed.

- [ ] T021 [US5] Write tests in `tests/test_retry.py`. Test cases: 429 with `X-Rate-Limit-Reset-After` header retries after specified duration; 429 without header uses exponential backoff; multiple 429s then 200 succeeds; max retries exceeded raises `RateLimitError` with retry_after/scope/window attrs; verify jitter is applied (backoff not deterministic); verify DEBUG logging on retry. Use respx `side_effect` with sequential 429→200 responses. FR-013.
  **Done when**: All tests pass with `pytest tests/test_retry.py`.

**Checkpoint**: Rate limit handling verified.

---

## Phase 8: User Story 6 — Check Account Quotas (P3)

**Goal**: Users can query their API quota and rate limit status.

**Independent Test**: Call quota endpoint → receive typed `QuotaInfo` with raw `limits` plus flattened `quotas` windows.

- [ ] T022 [P] [US6] Implement quota models in `src/urlscope/models/_quota.py`. Classes: `QuotaWindow` (fields: scope, action, window, limit, used, remaining, percent, reset) and `QuotaInfo` (fields: `scope` and raw `limits`, plus computed flattened `quotas` as `list[QuotaWindow]`). Use `ConfigDict(extra="allow", populate_by_name=True)`. `QuotaInfo` must accept live top-level `scope`, preserve the raw `limits` structure including metadata entries, and flatten only minute/hour/day windows. FR-016. Ref: data-model.md QuotaInfo/QuotaWindow.
  **Done when**: `QuotaInfo.model_validate(sample_quota_json)` parses a live-shaped quota payload correctly and preserves raw metadata under `limits`.

- [ ] T023 [US6] Update `src/urlscope/models/__init__.py` to re-export `QuotaInfo`, `QuotaWindow`. Add `get_quotas()` method to `UrlscopeClient` in `src/urlscope/_client.py`: `get_quotas() → QuotaInfo` (GET `/api/v1/quotas`). Update `src/urlscope/__init__.py` exports. FR-011.
  **Done when**: `client.get_quotas()` returns typed `QuotaInfo` with raw `limits` and flattened `quotas` windows.

- [ ] T024 [P] [US6] Write tests in `tests/test_quota.py`. Test cases: get_quotas returns typed `QuotaInfo` with flattened quota windows from a canonical sanitized live-shaped fixture; verify quota fields (`scope`, `action`, `window`, `limit`, `used`, `remaining`, `percent`, `reset`) from the computed `quotas` list; verify non-window metadata remains in raw `limits` and is not flattened into quota windows. Mock `GET /api/v1/quotas`. FR-011.
  **Done when**: All tests pass with `pytest tests/test_quota.py`.

**Checkpoint**: Quota queries working independently.

---

## Phase 9: User Story 7 — Sync Convenience Wrappers (P3)

**Goal**: All async operations available as sync equivalents via `SyncClient`.

**Independent Test**: Call sync methods → receive same typed results as async.

- [ ] T025 [US7] Implement `SyncClient` in `src/urlscope/_sync.py`. Stores constructor params only (`_api_key`, `_base_url`, `_timeout`, `_max_retries`). Each method creates a fresh `UrlscopeClient` inside `asyncio.run()` with `async with`, runs the operation, and closes. Methods: `submit`, `get_result`, `submit_and_wait`, `search`, `get_screenshot`, `get_dom`, `get_quotas` — all mirroring `UrlscopeClient` signatures minus async. Implement `__enter__` / `__exit__` / `close()` as no-ops on SyncClient. `__enter__` returns self, `__exit__` does nothing, `close()` does nothing. Purpose: API symmetry with UrlscopeClient; no connection state to clean up. FR-015. Ref: research.md R2 (pattern per method), contracts/public-api.md SyncClient.
  **Done when**: `SyncClient(api_key="test").get_result("uuid")` runs synchronously and returns typed `ScanResult`; `with SyncClient(api_key="test") as client:` works without error.

- [ ] T026 [US7] Update `src/urlscope/__init__.py` to export `SyncClient`.

- [ ] T027 [P] [US7] Write tests in `tests/test_sync.py`. Test cases: each sync method returns same typed result as async counterpart (test submit, get_result, search, get_screenshot, get_dom, get_quotas); SyncClient does not hold persistent connection state (verify fresh client per call). Use respx mocking. FR-015.
  **Done when**: All tests pass with `pytest tests/test_sync.py`.

**Checkpoint**: Full sync API working; SC-005 satisfied.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: README, full validation, final exports check

- [ ] T028 Create `README.md` at repository root. Sections: project description, installation (`pip install urlscope`), quickstart (async submit-and-wait, sync usage, search, error handling — adapted from quickstart.md), API reference summary, license (MIT). SC-007.
  **Done when**: README renders correctly in markdown; quickstart code examples are syntactically valid.

- [ ] T029 Run full validation: `pytest tests/` (all pass), `ruff check src/ tests/` (no errors), `mypy src/` in strict mode (no errors). Fix any issues. SC-006.
  **Done when**: All three commands pass with zero errors.

- [ ] T030 Verify package exports completeness in `src/urlscope/__init__.py`: confirm all public classes from contracts/public-api.md are exported: `UrlscopeClient`, `SyncClient`, `SubmissionResponse`, `ScanResult`, `TaskInfo`, `PageInfo`, `Verdicts`, `BrandMatch`, `ScanLists`, `CertificateInfo`, `SearchResponse`, `SearchResultItem`, `QuotaInfo`, `QuotaWindow`, `UrlscopeError`, `AuthenticationError`, `NotFoundError`, `ScanDeletedError`, `ValidationError`, `RateLimitError`, `ScanTimeoutError`, `APIError`.
  **Done when**: `from urlscope import <each_class>` works for every listed class.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phases 3–9 (User Stories)**: All depend on Phase 2 completion
  - US1 (Phase 3): No story dependencies — MVP
  - US2 (Phase 4): No story dependencies (uses same HTTP transport)
  - US3 (Phase 5): No story dependencies
  - US4 (Phase 6): Fully covered by Phase 2 tasks
  - US5 (Phase 7): Implementation in Phase 2; only tests here
  - US6 (Phase 8): No story dependencies
  - US7 (Phase 9): Depends on all client methods being implemented (US1+US2+US3+US6)
- **Phase 10 (Polish)**: Depends on all story phases being complete

### Within Each Phase

- Models before client methods (within same story)
- Client methods before tests
- Tests marked [P] can run in parallel

### Parallel Opportunities

- T003 + T004 (exceptions + HTTP transport) — different files
- T005 + T006 (submission models + result models) — different files
- T011 + T012 + T013 + T014 + T015 (all US1 test files) — different files
- T016 + T022 (search models + quota models) — different files, different stories
- T018 + T020 + T021 + T024 (test files across stories) — different files

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T004)
3. Complete Phase 3: User Story 1 (T005–T015)
4. **STOP and VALIDATE**: `pytest tests/` — all US1 tests pass
5. Library can submit URLs, retrieve results, poll for completion

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (submit/result/poll) → Test → **MVP ready**
3. Add US2 (search) → Test → Search capability added
4. Add US3 (artifacts) + US5 (retry tests) → Test → Full data access
5. Add US6 (quotas) → Test → Operational visibility
6. Add US7 (sync wrappers) → Test → Sync users supported
7. Polish → README, lint, type check → **PyPI ready**

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story
- US4 (auth) and US5 (rate limits) are implemented in Phase 2 (foundational); their phases only add tests
- Each story can be tested independently after Phase 2
- Commit after each task or logical group
- Total: 30 tasks (2 setup, 2 foundational, 11 US1/MVP, 3 US2, 2 US3, 1 US5, 3 US6, 3 US7, 3 polish)
