# Validation

## Proof Strategy

Use the existing SQLite unit suite for backward compatibility and a dedicated,
disposable PostgreSQL database for migration metadata, SCD2, crawler tracking,
sequence, idempotency, and catalog-only authorization proof. Network adapters
must be fake; no test may contact the product website.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | SQLite relation names remain flat; unknown relation identifiers fail; existing database and spec persistence tests pass. |
| Integration | Apply 001/002/003; verify exact 9/9 placement; crawl synthetic A/A/B; verify unchanged/changed SCD2; rerun 003; compare data and metadata; verify sequences and inserts. |
| E2E | Not applicable; no user interface changes. |
| Platform | `docker compose config --quiet`; PostgreSQL 16 disposable database when available. |
| Performance | Not benchmarked; migration uses in-place metadata moves and takes exclusive table locks. |
| Logs/Audit | Migration errors enumerate only allow-listed application relations; no secrets or payloads logged. |

## Fixtures

- Synthetic `ProductContent` A and B.
- Fake HTTP adapter responses.
- Unrelated `public` table proving the migration does not require an empty
  schema.
- Temporary PostgreSQL role with catalog-only privileges.

## Commands

```text
cd app/dmx-crawler
python -m compileall -q dmx_crawler tests scripts
python -m unittest discover -s tests -v
DMX_TEST_POSTGRES_ADMIN_URL=<dedicated-local-admin-dsn> \
  python -m unittest tests.test_postgres_schema_split -v
docker compose config --quiet

cd ../..
git diff --check
git status --short
```

## Acceptance Evidence

- Syntax compilation: passed with no output.
- SQLite/default suite: `python -m unittest discover -s tests -v` ran 65 tests successfully; the opt-in PostgreSQL class was skipped without a test DSN.
- Pytest: 65 passed, 3 PostgreSQL cases skipped by default, and 19 subtests passed.
- PostgreSQL 16 disposable integration: 3/3 tests passed in 1.122 seconds.
- Placement after migration: 9 tables in `catalog`, 9 tables in `crawler`; unrelated `public.unrelated_fixture` remained unchanged.
- Metadata before/after first migration and after the second migration: 18 primary keys, 32 foreign keys, 7 table unique constraints, 3 check constraints, 33 indexes, and 8 owned sequences/defaults; OIDs, definitions, sequence options, sequence state, and data snapshots were equal.
- Sequence proof: inserts omitting all eight generated IDs succeeded after the move.
- Three-state proof: complete legacy split passed; already-split rerun passed as an exact no-op; partial and missing-table layouts raised and rolled back.
- Runtime proof: synthetic A/A/B produced one version, no duplicate on unchanged, then a closed old/current new version with matching EAV history; attempts, observations, and state remained in `crawler`.
- Authorization proof: a temporary role with `USAGE`/`SELECT` on `catalog` and no `USAGE` on `crawler` successfully ran `Database.export_current()` and was denied `SELECT` on `crawler.crawl_runs`.
- Cleanup proof: no disposable database, temporary role, or PostgreSQL container remained.
- Compose validation: `docker compose config --quiet` passed.
- SQLite sample proof: `live-sample.db` and its round-2 backup retained their baseline SHA-256 hashes; no catalog snapshot database was created.

## Gaps

- Production deployment role names are environment-specific and intentionally remain outside migration 003. Operators must grant schema `USAGE`, table privileges, and crawler sequence privileges explicitly.
- Migration takes `ACCESS EXCLUSIVE` locks while moving tables, so production rollout requires a coordinated maintenance window.
