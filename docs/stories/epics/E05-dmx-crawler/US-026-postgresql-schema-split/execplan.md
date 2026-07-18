# Exec Plan

## Goal

Split the existing PostgreSQL crawler database in place into `catalog` and
`crawler` schemas while preserving all data, SCD2 behavior, constraints,
indexes, sequences, and flat-table SQLite compatibility.

## Scope

In scope:

- Add migration 003 with exact-state validation and idempotent rerun behavior.
- Schema-qualify every PostgreSQL relation reference in component raw SQL.
- Keep all SQLite SQL unqualified.
- Make PostgreSQL runtime initialization readiness-only.
- Add SQLite regressions and a disposable PostgreSQL integration test.
- Document migration order, locks, grants, and role boundaries.

Out of scope:

- Network crawling or product discovery.
- Changes to parser, models, fixtures, or sample data.
- Changes to migrations 001/002 or `sqlite_schema.sql`.
- Automatic PostgreSQL migration execution during crawl.
- Git commit, push, or branch changes.

## Risk Classification

Risk flags:

- Data model.
- Authorization.
- Existing behavior.
- Weak PostgreSQL integration proof.
- Data migration.

Hard gates:

- In-place data migration.
- Schema-level authorization boundary.

## Work Phases

1. Inventory every raw SQL relation reference and current DDL object.
2. Implement migration 003 and backend-specific relation resolution.
3. Add SQLite and PostgreSQL integration proof.
4. Update component documentation.
5. Run syntax, SQLite, PostgreSQL, compose-config, and whitespace checks.
6. Record Harness proof and the final session trace.

## Stop Conditions

Pause for human confirmation if:

- Migration would need to copy, delete, or rewrite application data.
- Any required primary key, foreign key, unique/check constraint, index, or
  sequence cannot be preserved.
- Validation would require a shared PostgreSQL database.
- The schema allocation differs from the confirmed 9/9 table allow-list.
