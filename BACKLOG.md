# Backlog

## Future Enhancements

- Investigate support for non-`scans` search datasources: `hostnames`, `certificates`, `incidents`, and `notifications`. These are documented by urlscan but may require higher-tier account access.
- Evaluate optional endpoint support for response/download artifacts and discovery helpers: `/responses/{fileHash}/`, `/downloads/{fileHash}`, `/api/v1/hostname/{hostname}`, `/api/v1/availableCountries`, and `/api/v1/userAgents`.
- Consider keyless use: urlscan answers `search` and `quotas` (with limits scoped to the client's IP address) without an `API-Key` header, while `UrlscopeClient` requires a key at construction.
