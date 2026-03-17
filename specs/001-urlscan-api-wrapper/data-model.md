# Data Model: urlscope

**Branch**: `001-urlscan-api-wrapper`
**Date**: 2026-03-15

All models use Pydantic v2 with `ConfigDict(extra="allow")` to capture typed fields while preserving extra/unknown fields in `model_extra`.

## Entity: SubmissionRequest

Internal model for building the POST body to `POST /api/v1/scan/`.

| Field            | Type                              | Required | Notes                                      |
|------------------|-----------------------------------|----------|--------------------------------------------|
| url              | str                               | Yes      | Target URL to scan                         |
| visibility       | Literal["public","unlisted","private"] | No | Defaults to API-side user preference       |
| custom_agent     | str                               | No       | Override browser User-Agent                |
| referer          | str                               | No       | Override HTTP Referer                      |
| tags             | list[str]                         | No       | Max 10 items, validated client-side        |
| override_safety  | bool                              | No       | Disable PII reclassification               |
| country          | str                               | No       | ISO 3166-1 alpha-2 country code            |

**Validation**: `tags` length <= 10 (raises `ValueError` before request).

## Entity: SubmissionResponse

Returned from `POST /api/v1/scan/`.

| Field      | Type   | Required | Notes                              |
|------------|--------|----------|------------------------------------|
| message    | str    | Yes      | e.g. "Submission successful"       |
| uuid       | str    | Yes      | Scan identifier                    |
| result     | str    | Yes      | Human-readable result URL          |
| api        | str    | Yes      | API result endpoint URL            |
| visibility | str    | Yes      | Confirmed visibility level         |
| url        | str    | Yes      | Submitted URL                      |
| country    | str    | No       | Scan country if specified          |
| options    | dict   | No       | Confirmed scan options             |

## Entity: ScanResult

Returned from `GET /api/v1/result/{uuid}/`. Partial typed model — common sections are typed, full raw dict accessible via `.raw` / `model_extra`.

| Field    | Type            | Required | Notes                                |
|----------|-----------------|----------|--------------------------------------|
| task     | TaskInfo        | Yes      | Scan task metadata                   |
| page     | PageInfo        | Yes      | Page-level information               |
| verdicts | Verdicts        | No       | Maliciousness scoring and categories |
| stats    | dict            | No       | Computed stats (loosely typed)       |
| lists    | ScanLists       | No       | Aggregated lists (IPs, domains, etc) |
| data     | dict            | No       | Raw request/cookie/console data      |
| meta     | dict            | No       | Processor annotations                |

**Raw access**: `scan_result.model_extra` for any field not explicitly modeled.

### Sub-entity: TaskInfo

| Field       | Type       | Required | Notes                              |
|-------------|------------|----------|------------------------------------|
| uuid        | str        | Yes      | Scan UUID                          |
| url         | str        | Yes      | Tasked URL                         |
| domain      | str        | No       | Extracted from task.url            |
| apex_domain | str        | No       | Registered second-level domain     |
| time        | datetime   | Yes      | Scan creation timestamp (ISO-8601) |
| method      | str        | No       | "api", "manual", or "automatic"    |
| visibility  | str        | Yes      | Visibility level                   |
| tags        | list[str]  | No       | User-supplied tags                 |
| options     | dict       | No       | Scan options                       |

### Sub-entity: PageInfo

| Field          | Type   | Required | Notes                          |
|----------------|--------|----------|--------------------------------|
| url            | str    | Yes      | Final page URL                 |
| domain         | str    | No       | Page hostname                  |
| apex_domain    | str    | No       | Second-level domain            |
| ip             | str    | No       | Primary request IP             |
| asn            | str    | No       | Autonomous System number       |
| asnname        | str    | No       | AS name                        |
| country        | str    | No       | GeoIP country                  |
| city           | str    | No       | GeoIP city                     |
| server         | str    | No       | HTTP Server header             |
| title          | str    | No       | Page title                     |
| status         | str    | No       | HTTP status code (as string)   |
| mime_type      | str    | No       | Response MIME type              |
| tls_issuer     | str    | No       | TLS certificate issuer         |
| tls_valid_from | datetime | No     | Certificate valid-from         |
| tls_valid_days | int    | No       | Certificate validity period    |
| tls_age_days   | int    | No       | Certificate age in days        |
| umbrella_rank  | int    | No       | Cisco Umbrella rank            |
| redirected     | str    | No       | Redirect info                  |
| ptr            | str    | No       | DNS PTR record                 |

### Sub-entity: Verdicts

| Field      | Type           | Required | Notes                              |
|------------|----------------|----------|------------------------------------|
| score      | int            | No       | Maliciousness score (-100 to 100)  |
| categories | list[str]      | No       | Threat categories                  |
| brands     | list[BrandMatch] | No     | Detected brand impersonation       |
| malicious  | bool           | No       | Overall malicious verdict          |

### Sub-entity: BrandMatch

| Field     | Type       | Required | Notes                         |
|-----------|------------|----------|-------------------------------|
| key       | str        | Yes      | Brand identifier              |
| name      | str        | Yes      | Brand name                    |
| country   | list[str]  | No       | Associated countries          |
| vertical  | list[str]  | No       | Industry verticals            |

### Sub-entity: ScanLists

| Field        | Type       | Required | Notes                          |
|--------------|------------|----------|--------------------------------|
| ips          | list[str]  | No       | All contacted IPs              |
| domains      | list[str]  | No       | All contacted domains          |
| urls         | list[str]  | No       | All requested URLs             |
| countries    | list[str]  | No       | GeoIP countries                |
| asns         | list[int]  | No       | AS numbers                     |
| servers      | list[str]  | No       | HTTP Server headers            |
| hashes       | list[str]  | No       | SHA256 response body hashes    |
| certificates | list[CertificateInfo] | No | TLS certificates          |
| link_domains | list[str]  | No       | Domains found in page links    |

### Sub-entity: CertificateInfo

| Field       | Type     | Required | Notes                           |
|-------------|----------|----------|---------------------------------|
| subject     | str      | No       | Certificate subject CN          |
| issuer      | str      | No       | Certificate issuer              |
| valid_from  | datetime | No       | Valid-from date                 |
| valid_to    | datetime | No       | Valid-to / expiry date          |
| san_list    | list[str]| No       | Subject Alternative Names       |

**Note**: Exact certificate field names will be confirmed against live API responses during implementation. `extra="allow"` ensures forward compatibility.

## Entity: SearchResponse

Returned from `GET /api/v1/search/`.

| Field    | Type                 | Required | Notes                          |
|----------|----------------------|----------|--------------------------------|
| results  | list[SearchResultItem] | Yes    | List of matching scan summaries |
| total    | int                  | Yes      | Total matching results count, server-enforced |
| has_more | bool                 | Yes      | Whether more results exist     |

## Entity: SearchResultItem

Individual item within search results.

| Field  | Type   | Required | Notes                                |
|--------|--------|----------|--------------------------------------|
| id     | str    | Yes      | Scan UUID (from `_id`)               |
| sort   | list   | No       | Pagination cursor for `search_after` |
| page   | dict   | No       | Page summary info                    |
| task   | dict   | No       | Task summary info                    |
| stats  | dict   | No       | Stats summary                        |

**Note**: Search result items have lighter structure than full ScanResult. Typed as dicts at this level since the search API returns abbreviated fields.

## Entity: QuotaInfo

Returned from `GET /api/v1/quotas`.

| Field   | Type           | Required | Notes                                                     |
|---------|----------------|----------|-----------------------------------------------------------|
| scope   | str            | No       | Top-level quota scope; live API currently returns `scope` |
| limits  | dict           | Yes      | Raw quota structure from urlscan                          |
| quotas  | list[QuotaWindow] | Yes   | Computed flattened convenience view of minute/hour/day windows |

### Sub-entity: QuotaWindow

| Field     | Type   | Required | Notes                          |
|-----------|--------|----------|--------------------------------|
| scope     | str    | No       | Copied from top-level quota scope |
| action    | str    | Yes      | "search", "public", etc.       |
| window    | str    | Yes      | "minute", "hour", "day"        |
| limit     | int    | Yes      | Maximum requests allowed       |
| used      | int    | No       | Requests already used          |
| remaining | int    | No       | Remaining in current window    |
| percent   | float  | No       | Percentage of window consumed  |

**Note**: urlscan's live quota response is nested under `limits`. The library preserves that raw structure in `QuotaInfo.limits` and also exposes a flattened `QuotaInfo.quotas` convenience list for iterating per action/window.

## Entity Relationships

```
UrlscopeClient
  ├── submit(url, ...) → SubmissionResponse
  ├── get_result(uuid) → ScanResult
  │     ├── .task → TaskInfo
  │     ├── .page → PageInfo
  │     ├── .verdicts → Verdicts
  │     │     └── .brands → list[BrandMatch]
  │     └── .lists → ScanLists
  │           └── .certificates → list[CertificateInfo]
  ├── submit_and_wait(url, ...) → ScanResult
  ├── search(query, ...) → SearchResponse
  │     └── .results → list[SearchResultItem]
  ├── get_screenshot(uuid) → bytes
  ├── get_dom(uuid) → str
  └── get_quotas() → QuotaInfo
        └── .quotas → list[QuotaWindow]
```

## Field Naming Convention

API JSON uses camelCase (e.g., `apexDomain`, `asnname`, `tlsIssuer`). Pydantic models use snake_case with `alias` for deserialization:

- `model_config = ConfigDict(extra="allow", populate_by_name=True)`
- Fields use `Field(alias="camelCaseName")` where names differ

This lets users access fields as `result.page.apex_domain` (Pythonic) while the model correctly deserializes from `{"apexDomain": "..."}`.
