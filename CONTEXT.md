# notion-cli Context

## Architecture

```
notion_cli/
  cli.py           # Typer CLI — all commands
  client.py        # NOTION_TOKEN auth, Client factory
  formatters.py    # Notion property extractors, flatten_page
  schemas.py       # Runtime JSON-Schema definitions per command
  lib/
    output.py      # JSON-First output (sys.stdout.write, not print)
    validate.py    # Input hardening (control chars, unicode, UUID)
    fields.py      # --fields masking for context window discipline
```

## Notion API Quirks (notion-client 3.0.0)

- `databases.query` removed. Use `data_sources.query(data_source_id=...)` instead.
- `search` API returns `data_source` objects with ID different from URL's database ID.
  Use the search result `id` for `db query` and `db schema`.
- Integration must be explicitly shared with each page/DB in Notion UI
  (page `...` > Add connections).
- `data_sources.retrieve` vs `databases.retrieve` — try data_sources first, fall back.

## Constraints

| Limit | Value |
|-------|-------|
| Rate limit | 3 req/s average |
| Page size | max 100 per request |
| Rich text | max 2000 chars |
| Children per create | max 100 blocks |
| Payload size | max 500 KB |
| Nested filter depth | max 2 levels |

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| object_not_found | 404 | Wrong ID or Integration not shared |
| unauthorized | 401 | Invalid NOTION_TOKEN |
| rate_limited | 429 | Too many requests, check Retry-After header |
| validation_error | 400 | Invalid request body |
| INVALID_INPUT | - | CLI-level input validation failure |
| PATH_TRAVERSAL | - | Attempted path traversal in ID |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API error or general error |
| 2 | Auth error |
