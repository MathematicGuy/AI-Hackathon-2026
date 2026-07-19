# Local Postgres setup for the live-Postgres integration test

**Date:** 2026-07-19
**Related:** `backend/tests/integration/api/test_catalog_endpoints.py`
**Related stories:** US-207, US-116 (observability work surfaced this as a
cross-cutting deferred item; the test itself is data-platform / US-206
territory).

## Context

The catalog-endpoints integration test was deferred in
`docs/team/now/THANH-NOW.md` because its fixtures require a running Postgres
server with the catalog ingested. This report records the exact reproduction
commands so any teammate can stand up the same environment.

## Steps

1. Start Postgres on the loopback interface (dev override publishes port 55432
   on `127.0.0.1` only — do not use this override on a shared host):

   ```powershell
   docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d db
   ```

   Image: `pgvector/pgvector:pg16`. Health check: `pg_isready -U advisor -d advisor`.
   Wait for `docker inspect --format '{{.State.Health.Status}}' advisor-data-platform-db-1`
   to report `healthy`.

2. Migrate the schema:

   ```powershell
   $env:PYTHONPATH="$PWD"; .venv\Scripts\python.exe -m backend.app.db.migrate
   ```

   Expected: `migrate target: 127.0.0.1:55432/advisor` → `database up to date`.

3. Ingest the catalog (8,746 products across 14 categories):

   ```powershell
   $env:PYTHONPATH="$PWD"; .venv\Scripts\python.exe -m backend.app.ingestion.run --source data/dataset
   ```

   Expected: `inserted=8746 updated=0 skipped=0 errors=0`, with per-sheet counts
   for Tủ Lạnh, Máy lạnh, Máy giặt, … Máy tính bảng.

4. Run the test:

   ```powershell
   $env:PYTHONPATH="$PWD"; .venv\Scripts\python.exe -m pytest -p no:cacheprovider `
     backend/tests/integration/api/test_catalog_endpoints.py -v
   ```

   Expected: **13 passed** (health, categories=8746, category attributes,
   unknown-category 404, brands, search, attribute filter + detail, numeric
   filter bound, unknown attribute key rejected, attribute filter without
   category rejected, page_size over max rejected, batch found/missing,
   compare same category).

## Gotcha — `localhost` vs `127.0.0.1`

On Windows, `localhost` typically resolves to IPv6 `::1` first. Docker's
loopback port publish (`127.0.0.1:55432:5432`) is IPv4-only, so a psycopg
connection to `localhost:55432` hangs until the connect timeout. The fix is
to set `POSTGRES_HOST=127.0.0.1` in the root `.env` (git-ignored).

## Teardown

```powershell
docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml down     # stop, keep volume
docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml down -v  # stop + drop data
```

## Result

`backend/tests/integration/api/test_catalog_endpoints.py` — **13/13 passed**
in ~1.5s against the local Postgres container.
