# Validation

## Proof Strategy

Every stage is a gate. Database and location failures block discovery or
detailed crawl. Counts and metadata are reported without credentials or raw
payloads. Network proof uses concurrency one, bounded retries, and the existing
host rate limiter.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Existing parser, SCD2, EAV, location matching, and PostgreSQL routing tests. |
| Integration | Neon schema state, migrations when empty, FK/index/SCD2 audit, SQLite integrity, and row counts. |
| E2E | Hanoi location resolution, locked-list crawl, Neon-first SQLite mirror, and three unchanged rechecks. |
| Platform | Direct versus pooled Neon connection readiness without exposing URLs. |
| Performance | Concurrency one, at least five seconds between product requests, maximum three attempts. |
| Logs/Audit | Run/task/attempt/observation/error records and credential-free reports. |

## Fixtures

- Existing `config/locations.yaml` Hanoi entry.
- Existing SQLite `data/schema-sample/live-sample.db`.
- Existing three category configurations.
- Neon database reached through environment-only direct and pooled URLs.

## Commands

Commands used a temporary credential-free helper that parsed `.env` in memory,
mapped the selected URL to libpq `PG*` environment variables, captured and
redacted `psql` output, and never placed a connection URL on the command line.
The helper was outside the repository and stored no environment values.

## Acceptance Evidence

### Environment and dependencies

- All five required `APP_*` variables were present.
- Direct and pooled URLs had PostgreSQL schemes and were distinct.
- Pool bounds parsed as a valid range.
- The `.env` file was not shell-sourceable because a value contained shell
  syntax; a non-evaluating in-memory parser was used instead.
- `psql` 16.14 was available. Psycopg was not installed, and no package was
  installed because the run stopped before crawler runtime.

### Neon

- Direct connection succeeded.
- Initial state was completely empty: zero user tables and zero allow-listed
  application tables in `public`, `catalog`, `crawler`, or another schema.
- Migrations 001, 002, and 003 succeeded in that order.
- Migration 003 succeeded a second time as an idempotence check.
- Pooled connection succeeded after migration.
- Final placement: 9 `catalog` tables, 9 `crawler` tables, and zero legacy
  application tables in `public`.
- Metadata: 32 foreign keys, 33 valid or ready indexes, 2 SCD2 current partial
  unique indexes, 8 owned sequences, and zero unvalidated constraints.
- Every Neon application table had zero rows after schema setup.

### SQLite

- Opened with `sqlite3 -readonly`.
- `PRAGMA integrity_check` returned `ok`.
- `PRAGMA foreign_key_check` returned no violation.
- Baseline product data: 6 products, 6 content versions, 158 specification
  values, 66 media assets, 66 version-media rows, and zero location versions.
- Operational baseline: 9 runs, 9 tasks, 9 attempts, 9 observations, zero
  errors, 6 product crawl-state rows, and zero location crawl-state rows.
- The database was not seeded, migrated, deleted, recreated, or written.
- SHA-256 remained
  `18c7f15fb12029588dfaeb8c25af45fbd7c5dbf9d5a2a69615f029358f181a38`.

### Local component validation

- `python -m compileall -q dmx_crawler tests scripts` passed.
- `python -m unittest discover -s tests -v` ran 65 tests successfully with
  one opt-in local PostgreSQL integration class skipped.

### Hanoi location gate

- Exactly one active `hanoi` configuration was found.
- `province_id=1000` and `ward_id=103320` were present.
- Province and ward names were present.
- `address` was empty because the committed configuration intentionally stores
  `null`.
- `LocationConfig` and the adapter require a representative street address for
  delivery resolution. The operator prohibited guessing or hardcoding an
  address.

### Outcome

The run stopped at the required pre-crawl location gate. No request was sent to
Điện Máy XANH, including discovery, ward lookup, location confirmation,
product detail, or delivery endpoints. Therefore no URL list was locked, no
product was crawled, no dual-write occurred, and the three-URL unchanged check
was not applicable.


## Hanoi continuation evidence

The operator supplied the representative Hanoi location through `.env` and
resumed this story without discovery.

### Exact ward lookup and confirmation

- Environment location code remained `hanoi-cau-giay`.
- Province ID `1000` and its returned normalized name matched Hanoi.
- Configured ward ID `103320` existed in the API response but did not have the
  exact normalized name `Phường Cầu Giấy` or `Cầu Giấy`.
- The ward API returned exactly one exact normalized target:
  `Phường Cầu Giấy`, ID `103296`.
- Only `APP_DMX_WARD_ID` was updated in `.env`; all other environment location
  values were retained.
- Location confirmation returned matching province and ward IDs and names and a
  matching configured representative address. The address and cookies were not
  printed or recorded.
- Result: `LOCATION_CONFIRMED`.

### One-product smoke crawl

- No discovery was performed. One existing SQLite laptop URL was selected:
  `https://www.dienmayxanh.com/laptop/asus-tuf-gaming-f15-fx507zc4-i5-hn074w`.
- Concurrency was one, the shared rate limiter was five seconds, and transport
  attempts were capped at three.
- Product HTTP status was 200 on the first transport attempt.
- Parsed output: 6 specification groups, 26 specification items, 14 media
  assets, sale price present, list price absent, stock status `out_of_stock`.
- Completeness warnings, empty groups, and ambiguous merges were all zero.
- The payload was fetched and parsed once, persisted to Neon pooled first, and
  then persisted to SQLite without another product request.
- Neon created one product, one content version, 26 EAV rows, 14 media rows,
  one location version, one run, one task, one attempt, and two observations.
- SQLite reused the unchanged content version, EAV, and media and added one
  location version, one run, one task, one attempt, and two observations.
- `reconciliation_required` was false.

### Post-smoke validation

- Neon and SQLite current content hash and location state hash matched.
- Snapshot and EAV were equivalent in both databases, with 26 EAV rows each.
- Duplicate current content versions: zero in both databases.
- Duplicate current location versions: zero in both databases.
- Missing specification definitions and orphan specification rows: zero.
- Attempt HTTP status 200 and specification diagnostics were stored in both
  databases.
- SQLite integrity remained `ok`; foreign-key check returned no violation.
- SQLite post-smoke SHA-256 was
  `b372ba204fdc23ac389244a29856989272800678acc0c96772af00708d5538e0`.
- No CAPTCHA, challenge, 403, location mismatch, or persistence failure was
  observed.


## Balanced discovery and stopped batch evidence

- The short preflight passed again: direct and pooled Neon connections were available, Neon remained at 9 catalog and 9 crawler tables, ward 103296 was confirmed, and SQLite integrity and foreign-key checks passed.
- Live category/filter discovery observed 112 laptop, 200 television, and 188 refrigerator candidate URLs. After identity, price, and duplicate checks, 499 candidates remained eligible for balancing.
- A fixed list of 84 URLs was locked: 36 laptops, 24 televisions, and 24 refrigerators. The credential-free selection report is stored under the ignored runtime directory `data/schema-sample/us-027/`.
- The first two locked laptop product requests both returned HTTP 200. Neon rejected persistence because the operational helper supplied unsupported task type `hanoi_product`; migration 001 permits only `discover`, `common_product`, and `location_product`.
- The process stopped after the second consecutive Neon persistence failure, as required. No selected product, content version, specification value, media relation, or location version was added to Neon or SQLite.
- Neon changed only by one completed audit run row. SQLite added one run, two failed tasks, two attempts, and two redacted errors; product/catalog counts were unchanged.
- Post-stop direct Neon audit still showed one product, one content version, 26 EAV rows, 14 media rows, and one location version. SQLite still showed six products, six content versions, 158 EAV rows, 66 media rows, and one location version.
- Duplicate-current, duplicate-EAV, orphan-spec, and orphan-media checks were zero in both databases. SQLite integrity remained `ok` and its foreign-key check remained clean.
- Idempotence rechecks were not run because the batch stop condition fired.
- No CAPTCHA, challenge, 403, or location mismatch occurred.

## Task-type fix and checkpoint resume evidence

- The location-aware persistence path now maps the internal Hanoi workflow to
  the schema-valid database task type `location_product`. `common_product`
  remains unchanged for non-location work, and the application allow-list
  rejects any other task type before an insert is attempted.
- One parsed payload is persisted through a reusable Neon-first/SQLite-second
  coordinator. Each target database now treats product, content, EAV, media,
  location, task, attempt, and observation persistence as one nested
  transaction; the regression suite proves that a mid-payload failure rolls
  back the target database and that a SQLite mirror failure does not refetch or
  roll back the already committed Neon payload.
- Syntax compilation passed. The full offline suite ran 72 tests successfully;
  the dedicated PostgreSQL task-type test was then run separately against the
  prepared Neon database and passed using a rollback-only transaction. The
  disposable migration integration class remained skipped because no dedicated
  local PostgreSQL admin database was configured; migrations were not run on
  Neon.
- Final preflight passed: direct and pooled Neon connections, 9 catalog tables,
  9 crawler tables, exact ward ID `103296`, SQLite `integrity_check=ok`, and a
  clean SQLite foreign-key check. Credential-value scan and `git diff --check`
  passed.
- The checkpoint still contained the exact locked 84-URL sequence. Discovery
  was not rerun and no URL was added, removed, or reordered.
- The first two previously failed laptop URLs were requested again. Both detail
  requests returned HTTP 200; their location-aware delivery snapshots now
  resolved to `out_of_stock`, so neither qualified for product payload
  persistence.
- The new Neon run recorded two `location_product` tasks, two HTTP-200 attempts,
  and two redacted `ValueError` audit errors. SQLite recorded the corresponding
  two `location_product` tasks, attempts, and errors. The new runs contained
  zero invalid task types.
- Because neither URL produced a persisted payload, the mandatory first-two
  validation gate failed. The remaining 82 locked URLs were not requested and
  the three-category idempotence recheck was not run.
- Catalog counts remained unchanged: Neon stayed at 1 product, 1 content
  version, 26 EAV rows, 14 media relations, and 1 location version; SQLite
  stayed at 6 products, 6 content versions, 158 EAV rows, 66 media relations,
  and 1 location version.
- Post-stop integrity checks found zero duplicate current content versions,
  duplicate current location versions, duplicate EAV positions, orphan specs,
  or orphan media relations in either database. SQLite integrity remained
  `ok` and its foreign-key check remained clean.
- No CAPTCHA, anti-bot challenge, 403, location mismatch, reconciliation item,
  migration, database reset, commit, push, or branch change occurred.
