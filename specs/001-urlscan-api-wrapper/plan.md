# Implementation Plan: urlscope

**Branch**: `001-urlscan-api-wrapper` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-urlscan-api-wrapper/spec.md`

## Summary

Build `urlscope`, an async-first Python wrapper library for the urlscan.io REST API (v1). Uses httpx for HTTP transport with automatic rate limit handling, Pydantic v2 for validated response models with partial typing (common fields typed, raw dict access for the rest), and provides sync convenience wrappers. Packaged for PyPI publication with hatchling/src layout.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: httpx (async HTTP client), pydantic v2 (data validation/models)
**Storage**: N/A (stateless API wrapper)
**Testing**: pytest + respx (httpx mocking), mypy (strict), ruff (lint/format)
**Target Platform**: Any platform with Python 3.10+ (cross-platform library)
**Project Type**: Library (PyPI package)
**Performance Goals**: N/A (bound by upstream API latency; library adds negligible overhead)
**Constraints**: No unnecessary dependencies; async-first with sync wrappers; full type annotations
**Scale/Scope**: Single-user client library; concurrency bounded by upstream rate limits

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is unconfigured (template placeholders only). No gates to enforce. Proceeding without violations.

**Post-Phase 1 re-check**: No violations. Library design is simple — single package, no unnecessary abstractions, no over-engineering.

## Project Structure

### Documentation (this feature)

```text
specs/001-urlscan-api-wrapper/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Usage examples
├── contracts/
│   └── public-api.md    # Phase 1: Public API contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/urlscope/
├── __init__.py          # Public API re-exports
├── py.typed             # PEP 561 type marker
├── _client.py           # UrlscopeClient (async) — submit, get_result, submit_and_wait, search, artifacts, quotas
├── _sync.py             # SyncClient — sync wrappers via asyncio.run()
├── _http.py             # HTTP transport layer — httpx.AsyncClient wrapper, request method, retry/backoff logic
├── _exceptions.py       # Exception hierarchy (UrlscopeError → AuthenticationError, RateLimitError, etc.)
└── models/
    ├── __init__.py      # Re-export all models
    ├── _submission.py   # SubmissionResponse
    ├── _result.py       # ScanResult, TaskInfo, PageInfo, Verdicts, BrandMatch, ScanLists, CertificateInfo
    ├── _search.py       # SearchResponse, SearchResultItem
    └── _quota.py        # QuotaInfo, QuotaWindow

tests/
├── conftest.py          # Shared fixtures: mock client factory, sample JSON responses
├── test_submit.py       # Submission API (FR-001, FR-002, FR-003)
├── test_result.py       # Result retrieval + polling (FR-004, FR-005)
├── test_search.py       # Search + pagination (FR-006, FR-007)
├── test_artifacts.py    # Screenshot, DOM, certificates (FR-008, FR-009, FR-010)
├── test_quota.py        # Quota endpoint (FR-011)
├── test_auth.py         # API key resolution (FR-012)
├── test_retry.py        # Rate limit / 429 / backoff (FR-013)
├── test_sync.py         # Sync wrapper parity (FR-015)
├── test_errors.py       # Error handling / edge cases (FR-017, FR-018)
└── test_context.py      # Context manager lifecycle (FR-019)

pyproject.toml           # Build config (hatchling), dependencies, tool config (ruff, mypy, pytest)
README.md                # Quickstart, installation, badges
LICENSE                  # MIT
```

**Structure Decision**: Single-package src/ layout. This is a focused library with no CLI, no web service, no sub-projects. All source lives under `src/urlscope/`. Models are in a sub-package for organizational clarity but the package is flat enough to not warrant further nesting.

## Complexity Tracking

No constitution violations to justify. Design is minimal:
- 5 source modules + 1 models sub-package
- Single external integration (urlscan.io API)
- No database, no state, no background tasks
