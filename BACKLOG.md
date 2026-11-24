# Backlog

## Future Enhancements

- Verify the non-`scans` search datasources: `search(datasource=...)` already accepts `hostnames`, `certificates`, `incidents`, and `notifications`, but the models are verified only against `scans` results. Check whether their results parse (for example, `SearchResultItem.id` requires `_id`) and which account plans can use them.
- Evaluate optional endpoint support for response/download artifacts and discovery helpers: `/responses/{fileHash}/`, `/downloads/{fileHash}`, `/api/v1/hostname/{hostname}`, `/api/v1/availableCountries`, and `/api/v1/userAgents`.
- Consider keyless use where urlscan allows it (see "Live API quirks" in docs/design.md).
