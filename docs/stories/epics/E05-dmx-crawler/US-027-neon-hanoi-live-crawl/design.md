# Design

## Domain Model

The existing catalog/crawler split remains authoritative. `catalog` owns
products, versions, specifications, media, locations, and location offers.
`crawler` owns discovery, run/task/attempt/observation/error records and
incremental state. SQLite mirrors the same 18 relations with flat names.

The only allowed location is the existing active `hanoi` configuration. It
must contain valid province, ward, and required address fields, and the remote
site must resolve the same province and ward before product crawling begins.

## Application Flow

1. Load `.env` without printing values and map the direct/pooled URLs only in
   process memory.
2. Use the direct URL for schema classification, migration, and audit.
3. Initialize only a completely empty Neon database with 001, 002, then 003.
4. For an already split database, verify it and optionally rerun only 003.
5. Run SQLite integrity and foreign-key checks without replacing the file.
6. Validate the single Hanoi configuration and remote location resolution.
7. Discover inventory, lock a balanced list of at most 100 URLs, and write a
   credential-free selection report.
8. Fetch each locked URL once with concurrency one and a minimum five-second
   interval.
9. Commit the parsed payload to Neon, then the same payload to SQLite.
10. Reconcile current product/location data and run three unchanged checks.

## Interface Contract

Secrets are accepted only from `app/dmx-crawler/.env`. Commands and reports
must never print the connection strings. The direct Neon URL is an operator
channel; the pooled URL is the crawler runtime channel.

The run stops before detailed product requests when schema state is partial or
unknown, SQLite integrity fails, Hanoi configuration is incomplete, location
resolution mismatches, or the implementation cannot guarantee fetch-once
dual-write semantics.

## Data Model

No schema changes are allowed. Neon must contain exactly the nine application
tables in each of `catalog` and `crawler`, with no allow-listed legacy table in
`public`. Existing keys, foreign keys, indexes, sequences, and SCD2 partial
unique indexes must remain valid.

SQLite remains `data/schema-sample/live-sample.db`; it is never deleted,
recreated, or replaced.

## UI / Platform Impact

No frontend or UI behavior changes. Neon is an external managed PostgreSQL
platform and Điện Máy XANH is an external provider.

## Observability

Reports may contain counts, canonical product URLs, brands, categories, price
bands, hashes, HTTP status, warnings, and reconciliation identities. They must
not contain database URLs, passwords, cookies, authentication headers, private
addresses, or raw response bodies.

## Alternatives Considered

1. Run existing single-database CLI twice. Rejected because it requests and
   parses every product twice and violates fetch-once dual-write.
2. Use SQLite as primary and copy later. Rejected because Neon must commit
   first.
3. Supply a guessed Hanoi address. Rejected because the operator explicitly
   prohibited personal or inferred addresses.
4. Continue when location resolution is incomplete. Rejected because offers
   could be attributed to the wrong province.
