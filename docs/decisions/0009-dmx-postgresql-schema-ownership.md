# 0009 DMX PostgreSQL Schema Ownership

Date: 2026-07-18

## Status

Accepted

## Context

The DMX crawler stores product data used by frontend and agent consumers
together with crawler runs, tasks, attempts, errors, and incremental state.
Creating a separate clean catalog snapshot would introduce a second source of
truth and make crawler updates diverge from the data served to consumers.

PostgreSQL provides schemas for ownership and privilege boundaries. SQLite does
not, and the local sample database must remain a single unchanged file.

## Decision

Use one production PostgreSQL database with two explicit schemas:

- `catalog` owns the nine product-facing relations.
- `crawler` owns the nine crawler-operational relations.

Move legacy `public` relations in place with an idempotent migration based on
an exact 18-table allow-list. Preserve object identity, data, constraints,
indexes, sequences, and cross-schema foreign keys.

Runtime PostgreSQL SQL must use explicit schema qualification. SQLite continues
to use the same flat relation names and schema file. PostgreSQL migrations are
operator-controlled and never run automatically during crawl startup.

Frontend roles receive `USAGE` and read privileges on `catalog` only. Crawler
roles require access to both schemas. Migration SQL does not hardcode role
names or grant privileges broadly.

## Alternatives Considered

1. Create a separate catalog database or snapshot. Rejected because it creates
   multiple sources of truth.
2. Keep every relation in `public`. Rejected because operational ownership and
   consumer privileges remain coupled.
3. Use `search_path` without explicit qualification. Rejected because behavior
   depends on session configuration and is harder to audit.
4. Rebuild tables in new schemas. Rejected because in-place relation moves are
   safer and preserve PostgreSQL dependencies by object identity.

## Consequences

Positive:

- Crawler and consumers share one current product source.
- Operational relations have a clear privilege boundary.
- Existing SCD2 history and cross-schema references are preserved.
- SQLite development remains compatible.

Tradeoffs:

- Deployment needs a coordinated migration window because table moves take
  exclusive locks.
- Existing table grants do not imply `USAGE` on new schemas; deployment must
  grant schema privileges separately.
- Two catalog version tables retain foreign keys to crawler tasks because all
  existing foreign keys must remain intact.

## Follow-Up

- Keep integration proof for migration reruns, role isolation, sequence
  defaults, and catalog-only export.
- Provision deployment-specific role grants outside migration 003.
