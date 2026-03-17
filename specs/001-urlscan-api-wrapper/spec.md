# Feature Specification: urlscope — Python Wrapper for urlscan.io API

**Feature Branch**: `001-urlscan-api-wrapper`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Build a Python wrapper library for the urlscan.io REST API, intended for publication on PyPI"

## Clarifications

### Session 2026-03-15

- Q: How deeply should the library model the scan result JSON (full typed, partial typed, or minimal wrapper)? → A: Partial typed model — model common top-level sections (task, page, verdicts, stats, certificates, lists) with typed fields; expose full raw dict alongside for ad-hoc access.
- Q: What is explicitly out of scope for v1? → A: No CLI tool, no webhook/callback receiver, no batch submission orchestration, no async iterator for search pagination.
- Q: Should the client support context manager protocol for connection cleanup? → A: Yes, both async and sync clients support context manager (`async with` / `with`).
- Q: Should the library emit log messages for retries, polling, and errors? → A: Yes, use Python standard logging with NullHandler default (silent unless user configures the logger). Retries and polls logged at DEBUG/WARNING.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit and Retrieve a URL Scan (Priority: P1)

A security researcher wants to submit a suspicious URL for scanning and retrieve the full results. They initialize the library with their API key, submit the URL specifying visibility (public or private), and receive structured, validated results — either by polling until completion or by retrieving results later via UUID.

**Why this priority**: Submitting URLs and getting scan results is the core value proposition. Without this, the library has no purpose.

**Independent Test**: Can be fully tested by submitting a URL, waiting for completion, and verifying that the returned result object contains expected fields (task info, page details, verdicts). Delivers the primary value of programmatic URL scanning.

**Acceptance Scenarios**:

1. **Given** a valid API key and a URL, **When** the user submits a scan with public visibility, **Then** the library returns a submission response containing the scan UUID, result URL, and visibility confirmation.
2. **Given** a valid API key and a URL, **When** the user submits a scan with private visibility, **Then** the submission response reflects private visibility and the scan is not discoverable by other users.
3. **Given** a submitted scan UUID, **When** the user polls for results with a configurable timeout, **Then** the library automatically retries until the result is available or the timeout is exceeded.
4. **Given** a submitted scan UUID, **When** the scan completes, **Then** the library returns a fully validated result object with typed fields.
5. **Given** a submitted scan UUID, **When** the scan does not complete within the configured timeout, **Then** the library raises a clear timeout error indicating the scan is still pending.
6. **Given** a scan UUID for a deleted scan, **When** the user retrieves the result, **Then** the library raises an error indicating the scan has been removed.

---

### User Story 2 - Search Existing Scans (Priority: P2)

A CTI analyst wants to search for previously scanned URLs matching specific criteria (domain, IP, ASN, date range) using Elasticsearch query syntax. They want paginated results with easy iteration.

**Why this priority**: Search is the second most common operation — analysts need to find existing intelligence before deciding whether to submit a new scan.

**Independent Test**: Can be fully tested by executing a search query and verifying that results are returned as a list of typed objects with pagination support.

**Acceptance Scenarios**:

1. **Given** a valid API key and a search query string, **When** the user performs a search, **Then** the library returns a list of typed search result objects.
2. **Given** a search query that returns more results than the page size, **When** the user iterates through pages, **Then** the library supports cursor-based pagination using the `search_after` mechanism.
3. **Given** a search query with a custom page size, **When** the user specifies size up to the maximum allowed, **Then** the library respects the requested size.
4. **Given** an empty search query, **When** the user performs a search, **Then** the library returns recent public scans (default wildcard behavior).

---

### User Story 3 - Download Scan Artifacts (Priority: P2)

A security researcher wants to download artifacts from a completed scan — specifically the screenshot (PNG), DOM snapshot (HTML), and certificate chain data — for offline analysis or archival.

**Why this priority**: Artifact retrieval is essential for threat intelligence workflows where analysts need to preserve evidence beyond just the JSON result.

**Independent Test**: Can be fully tested by providing a valid scan UUID and verifying that binary (screenshot) and text (DOM) content is returned in the expected format.

**Acceptance Scenarios**:

1. **Given** a completed scan UUID, **When** the user downloads the screenshot, **Then** the library returns the PNG image as bytes.
2. **Given** a completed scan UUID, **When** the user downloads the DOM snapshot, **Then** the library returns the DOM content as a string.
3. **Given** a completed scan UUID, **When** the user requests certificate chain data, **Then** the library returns certificate information extracted from the scan result.
4. **Given** an invalid or pending scan UUID, **When** the user attempts to download an artifact, **Then** the library raises an appropriate error.

---

### User Story 4 - Configure Authentication Flexibly (Priority: P2)

A developer integrating urlscope into an automation pipeline wants to provide the API key either directly in code or via an environment variable, with clear precedence rules.

**Why this priority**: Flexible authentication is critical for adoption — developers need to support both interactive use (explicit key) and CI/CD pipelines (environment variable).

**Independent Test**: Can be tested by initializing the client with an explicit key, verifying it is used, then initializing without a key and verifying the environment variable is read.

**Acceptance Scenarios**:

1. **Given** an API key passed to the constructor, **When** the client is initialized, **Then** the explicit key is used for all requests regardless of environment variables.
2. **Given** no API key in the constructor but `URLSCAN_API_KEY` set in the environment, **When** the client is initialized, **Then** the environment variable value is used.
3. **Given** no API key in the constructor and no environment variable set, **When** the client is initialized, **Then** the library raises a clear error indicating no API key was found.

---

### User Story 5 - Handle Rate Limits Automatically (Priority: P2)

A developer running batch operations wants the library to automatically handle rate limiting (HTTP 429 responses) with exponential backoff, without needing to implement retry logic themselves.

**Why this priority**: Rate limiting is a common pain point with API wrappers. Automatic handling removes friction and prevents users from being blocked.

**Independent Test**: Can be tested by simulating 429 responses and verifying the library retries with increasing delays and eventually succeeds or raises an error after max retries.

**Acceptance Scenarios**:

1. **Given** an API call that receives a 429 response, **When** the library handles the response, **Then** it waits and retries with exponential backoff.
2. **Given** a 429 response with rate limit headers, **When** the library retries, **Then** it respects the `X-Rate-Limit-Reset-After` header for wait duration when available.
3. **Given** repeated 429 responses exceeding the maximum retry count, **When** the retry limit is reached, **Then** the library raises a rate limit error with details about when the limit resets.

---

### User Story 6 - Check Account Quotas and Limits (Priority: P3)

A developer wants to check their current API quota usage and remaining limits before running batch operations, to plan their workload accordingly.

**Why this priority**: Useful for operational planning but not core to the scanning workflow. Most users will rely on automatic rate limit handling instead.

**Independent Test**: Can be tested by calling the quota endpoint and verifying the response contains usage counts and limits for each rate window.

**Acceptance Scenarios**:

1. **Given** a valid API key, **When** the user queries account quotas, **Then** the library returns a typed object with current usage and limits per time window (minute, hour, day).

---

### User Story 7 - Use Sync Convenience Wrappers (Priority: P3)

A developer writing a simple script or working in a synchronous context wants to use the library without dealing with async/await syntax.

**Why this priority**: While the library is async-first, synchronous wrappers reduce the barrier to entry for simple scripts and REPL usage.

**Independent Test**: Can be tested by calling sync wrapper methods and verifying they return the same results as their async counterparts.

**Acceptance Scenarios**:

1. **Given** any async operation available in the library, **When** the user calls its sync equivalent, **Then** the operation completes and returns the same typed result as the async version.
2. **Given** a synchronous context, **When** the user uses the sync client, **Then** no event loop management is required from the user.

---

### Edge Cases

- What happens when the API key is invalid or expired? The library raises an authentication error with a clear message on the first request that returns HTTP 401/403.
- What happens when a submitted URL is rejected by urlscan.io (e.g., blocked domain, invalid URL format)? The library raises a validation error containing the API's error message and description.
- What happens when the network connection is lost mid-request? The library raises a connection error without masking the underlying cause.
- What happens when the API returns an unexpected response structure (missing fields)? The library handles missing optional fields gracefully via model defaults, rather than crashing. Fields not covered by the typed model remain accessible through the raw response dict.
- What happens when a user submits a scan with optional parameters (custom user agent, referer, tags, country)? These are passed through to the API correctly.
- What happens when pagination reaches the end of results? The library indicates there are no more results without raising an error.
- What happens when a user provides more than 10 tags? The library validates the tag count and raises a validation error before sending the request.

## Out of Scope (v1)

- CLI tool or command-line interface
- Webhook or callback receiver for scan completion notifications
- Batch submission orchestration (submitting multiple URLs in a single call)
- Async iterator / async generator interface for search pagination

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to submit a URL for scanning with configurable visibility (public, unlisted, private).
- **FR-002**: System MUST support optional scan submission parameters: custom user agent, referer, tags (up to 10), override safety flag, and country code.
- **FR-003**: System MUST return a typed submission response object containing scan UUID, result URL, API URL, visibility, and submitted URL.
- **FR-004**: System MUST allow users to poll for scan results with a configurable timeout and polling interval.
- **FR-005**: System MUST allow users to retrieve a completed scan result by UUID, returning a typed result object.
- **FR-006**: System MUST allow users to search existing scans using Elasticsearch query string syntax.
- **FR-007**: System MUST support cursor-based pagination for search results via the `search_after` mechanism.
- **FR-008**: System MUST allow users to download a scan's screenshot as PNG bytes.
- **FR-009**: System MUST allow users to download a scan's DOM snapshot as text.
- **FR-010**: System MUST allow users to retrieve certificate chain information from a scan result.
- **FR-011**: System MUST allow users to query their account quota and rate limit status.
- **FR-012**: System MUST accept an API key via explicit constructor parameter (preferred) or `URLSCAN_API_KEY` environment variable (fallback).
- **FR-013**: System MUST automatically handle HTTP 429 responses with exponential backoff, respecting rate limit headers when available.
- **FR-014**: System MUST provide an async-first interface using async/await patterns.
- **FR-015**: System MUST provide synchronous convenience wrappers for all async operations.
- **FR-016**: System MUST return validated, typed response objects for all API operations.
- **FR-017**: System MUST raise specific, descriptive errors for authentication failures, validation errors, timeouts, rate limit exhaustion, deleted scans, and connection issues.
- **FR-018**: System MUST handle missing optional fields in API responses gracefully without crashing.
- **FR-019**: System MUST support context manager protocol (async and sync) for proper cleanup of HTTP connections.
- **FR-020**: System MUST use standard logging under a library-specific logger, silent by default (NullHandler). Retry attempts and polling status are logged at DEBUG level; rate limit exhaustion and unexpected errors at WARNING level.

### Key Entities

- **Client**: The main entry point for interacting with the urlscan.io API. Holds the API key, HTTP configuration, and rate limit settings. Exists in both async and sync variants. Supports context manager protocol for connection lifecycle management.
- **Scan Submission**: Represents a request to scan a URL, including the target URL, visibility setting, and optional parameters (user agent, referer, tags, country).
- **Submission Response**: The API's acknowledgment of a scan request, containing the scan UUID, result URLs, and confirmed settings.
- **Scan Result**: The full result of a completed scan. Common top-level sections (task, page, verdicts, stats, certificates, resource lists) are modeled with typed fields. The complete raw response dict is also exposed for ad-hoc access to less common or newly-added fields.
- **Search Result**: A collection of scan summaries returned from a search query, with pagination metadata (total count, has_more flag).
- **Search Result Item**: An individual scan summary within search results, containing page info, task info, and statistics.
- **Quota Info**: The account quota response returned by urlscan, preserving the raw nested `limits` structure while also exposing a flattened list of per-action/per-window quota entries for convenience.
- **Account Quota**: Current API usage and limits across time windows (minute, hour, day) for the authenticated user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a URL and retrieve its scan result in a single method call (submit-and-wait), completing the full workflow with no more than two lines of code beyond client initialization.
- **SC-002**: All public operations return typed, validated response objects — users never need to manually parse raw JSON or handle untyped dictionaries.
- **SC-003**: Rate-limited requests are handled automatically — the library detects HTTP 429 responses, respects rate limit headers, and retries with exponential backoff without requiring user intervention.
- **SC-004**: The library handles scan polling transparently — users specify a timeout and receive either a result or a clear error, with no manual retry logic required.
- **SC-005**: Users can switch between async and sync usage with no change to business logic — only import and await syntax differ.
- **SC-006**: 100% of the library's public interface is covered by automated tests using mocked HTTP responses, with no live API calls required.
- **SC-007**: A new user can install the library and execute their first scan within 5 minutes using the quickstart documentation.
- **SC-008**: The library is installable via a single `pip install` command with no system-level dependencies beyond Python 3.10+.

## Assumptions

- The urlscan.io API (v1) will remain stable and backward-compatible for the foreseeable future. The library targets the current documented endpoints.
- Certificate chain data is available as part of the full scan result JSON (under the result's certificate/TLS fields), not as a separate download endpoint.
- The default polling interval for scan results is 5 seconds, with an initial wait of 10 seconds, matching the API documentation's recommendation.
- The maximum number of retries for rate-limited requests defaults to 5, with exponential backoff starting at the reset time indicated by rate limit headers.
- Search results default to 100 items per page, matching the API default. Maximum page size is determined by API documentation and enforced server-side.
- The sync wrappers run the async code in a new event loop, suitable for scripts and simple applications but not for use within an already-running async context.
- Tags submitted with a scan are limited to 10 per the API's constraint; the library validates this before sending the request.
- The library must support multiple API key tiers (Free, Professional and above) transparently — rate limits differ significantly between tiers but the retry/backoff mechanism is tier-agnostic.
- The library's only runtime dependencies are httpx (for HTTP) and pydantic (for data validation). Test dependencies are development-only.
