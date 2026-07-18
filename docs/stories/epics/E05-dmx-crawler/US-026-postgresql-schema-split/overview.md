# PostgreSQL Catalog/Crawler Schema Split

## Current Behavior

The DMX crawler keeps catalog data and crawler operational data in one database.
SQLite uses flat table names for local samples. PostgreSQL migrations 001 and
002 also create all 18 application tables as unqualified relations in
`public`. Runtime SQL is currently unqualified, and PostgreSQL initialization
can replay migration 001 during crawler startup.

## Target Behavior

PostgreSQL stores the nine product-facing tables in `catalog` and the nine
crawler-operational tables in `crawler`. Migration 003 moves the existing
relations in place, preserves data and object identity, accepts an already
complete split, and rejects every partial or missing-table state.

SQLite remains a single database with the existing flat table names. Crawler
runtime never applies PostgreSQL migrations automatically.

## Affected Users

- Frontend and agent consumers reading current catalog data.
- Crawler operators applying PostgreSQL migrations and running crawl jobs.
- Developers using the local SQLite sample and offline tests.

## Affected Product Docs

- `app/dmx-crawler/README.md`
- `docs/decisions/0009-dmx-postgresql-schema-ownership.md`

## Non-Goals

- Creating a catalog snapshot database.
- Moving or rewriting `live-sample.db`.
- Changing migrations 001 or 002.
- Changing the SQLite schema.
- Crawling the network or changing parsing behavior.
- Hardcoding deployment role names in migrations.
