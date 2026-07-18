# US-118 SQLite Catalog API Contract

## Status

implemented

## Lane

normal

## Product Contract

The frontend can consume crawler-backed catalog data through a stable HTTP v1
contract without reading SQLite directly. Product facts come from crawler
tables; homepage editorial content and collection ordering are stored
separately. Existing frontend mock data has an idempotent seed and
reconciliation strategy.

## Relevant Product Docs

- `docs/product/dmx-catalog-api.md`
- `docs/contracts/dmx-catalog-api-v1.yaml`

## Acceptance Criteria

- The contract defines homepage, product list/detail, category, location, and
  health endpoints.
- One product with multiple location rows is returned as one product containing
  `locations[]` and an explicit nullable `selected_location`.
- Null/unknown price is preserved and never converted to zero by the API.
- Frontend crawler facts are mapped separately from UI view-model fields.
- Editorial mock data has tables distinct from crawler version/history tables.
- Mock products are matched by canonical URL hash, and crawler data wins over
  temporary frontend seeds.
- Runtime implementation can later replace SQLite without changing v1 FE DTOs.

## Design Notes

- Commands: future idempotent migration and mock seed commands.
- Queries: current content plus bounded media/spec/location queries.
- API: OpenAPI 3.1 at `docs/contracts/dmx-catalog-api-v1.yaml`.
- Tables: existing crawler schema plus `site_content_entries`,
  `product_collections`, and `product_collection_items`.
- Domain rules: crawler owns product facts; editorial collections own
  presentation and ordering.
- UI surfaces: home, category, search, and product detail.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-118 --unit 1 --integration 0 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Parse OpenAPI YAML; validate DTO examples and mapping rules |
| Integration | Temporary SQLite fixture returns contract-conformant responses |
| E2E | Home, category, search, and detail render from API |
| Platform | SQLite volume remains readable across API restart |
| Release | Crawler-backed and mock-seed reconciliation smoke test |

## Harness Delta

Added a product contract and a normal-lane story so API implementation has a
bounded source of truth and explicit proof expectations.

## Evidence

- Source inspection confirmed crawler SQLite schema and
  `Database.export_current()`.
- Source inspection confirmed the frontend currently uses synchronous static
  catalog data plus a simulated async delay.
- OpenAPI YAML parsed successfully with 6 paths and 20 schemas.
- `git diff --check` passed for the contract changes.
