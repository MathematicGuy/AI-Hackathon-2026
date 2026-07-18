# Design

## Domain Model

Catalog relations are the product source of truth:

- `categories`
- `products`
- `product_content_versions`
- `spec_definitions`
- `product_spec_values`
- `media_assets`
- `product_version_media`
- `locations`
- `product_location_versions`

Crawler relations contain operational state:

- `product_urls`
- `crawl_runs`
- `crawl_tasks`
- `crawl_attempts`
- `crawl_observations`
- `crawl_errors`
- `product_crawl_state`
- `product_location_crawl_state`
- `discovery_sources`

## Application Flow

The database adapter resolves an allow-listed logical table name by backend:

- SQLite renders the existing flat name.
- PostgreSQL renders either `catalog.<table>` or `crawler.<table>`.

Frontend export reads only catalog relations. Crawler commands may join both
schemas. PostgreSQL startup verifies readiness and fails fast when the schema
has not been migrated; it does not run migrations.

## Interface Contract

No public API shape changes. The CLI `init-db` description will clarify that
PostgreSQL migrations are an explicit operator action while SQLite
initialization remains automatic.

## Data Model

Migration 003 uses an exact 18-table allow-list and ignores unrelated
`public` relations. It supports exactly three states:

1. All 18 legacy relations are in `public` and none are split: move them.
2. All 18 relations are in their destination schemas and none remain in
   `public`: validate and finish successfully.
3. Every mixed or incomplete state: raise an exception and roll back.

Existing tables move with `ALTER TABLE ... SET SCHEMA`; no data is copied and
constraints or indexes are not recreated. PostgreSQL object identity preserves
foreign keys, including cross-schema references. Postconditions verify table,
constraint, index, foreign-key, owned-sequence, and column-default placement.

## UI / Platform Impact

Deployment must apply migrations 001, 002, and 003 explicitly on a fresh
PostgreSQL database, or migration 003 on a fully prepared legacy database.
`ALTER TABLE ... SET SCHEMA` requires a short exclusive lock window.

Existing table grants remain attached to the moved objects, but schema
`USAGE` is separate. Deployment automation must grant frontend roles access
only to `catalog` and crawler roles access to both schemas.

## Observability

Migration failures report the exact missing, misplaced, or colliding
allow-listed relations. Integration tests record metadata counts before and
after the first and second migration applications.

## Alternatives Considered

1. Copy catalog data to a second database. Rejected because it creates two
   sources of truth.
2. Keep all PostgreSQL tables in `public` and rely on naming conventions.
   Rejected because product and crawler ownership remain unclear.
3. Use PostgreSQL `search_path`. Rejected because relation ownership would be
   implicit and frontend isolation would be harder to prove.
4. Recreate tables in new schemas. Rejected because it increases data-loss and
   constraint-drift risk.
