# Neon Hanoi Controlled Live Crawl

## Current Behavior

The crawler supports PostgreSQL or SQLite through one `Database` instance,
three configured locations, sitemap/category discovery, common-product crawls,
and location crawls. PostgreSQL runtime expects `DMX_DATABASE_URL`; deployment
configuration provides separate `APP_DATABASE_URL_DIRECT` and
`APP_DATABASE_URL_POOLED` values. The committed Hanoi location has province and
ward identifiers but intentionally has no address.

## Target Behavior

Validate or initialize Neon through the direct connection, use the pooled
connection for runtime, preserve the existing SQLite mirror, and only proceed
to a conservative Hanoi-only discovery and dual-write crawl when every
database, location, transport, and persistence preflight passes.

Each selected product must be fetched and parsed once. The parsed payload is
committed to Neon first and then to SQLite in a separate transaction. A failure
after the Neon commit is reconciliation-required rather than cross-database
atomicity.

## Affected Users

- Crawler operators.
- Frontend and agent consumers reading `catalog`.
- Reviewers validating catalog/crawler separation and mirrored current data.

## Affected Product Docs

- `app/dmx-crawler/README.md`
- `app/dmx-crawler/docs/catalog-schema.md`
- `docs/decisions/0009-dmx-postgresql-schema-ownership.md`

## Non-Goals

- Crawling a province other than Hanoi.
- Recreating or deleting the SQLite sample database.
- Creating a separate catalog snapshot database.
- Bypassing CAPTCHA, challenge, rate limits, or location validation.
- Modifying migrations 001, 002, or 003.
- Treating Neon and SQLite as one atomic transaction.
- Git commit, push, or branch changes.
