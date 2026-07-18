# Exec Plan

## Goal

Produce a controlled, credential-safe Hanoi catalog sample in Neon and the
existing SQLite mirror, or stop at the earliest failed safety gate with
concrete evidence and no product crawl.

## Scope

In scope:

- Neon empty/split/invalid schema classification.
- Explicit migrations only for a completely empty database.
- Neon and SQLite metadata/integrity baselines.
- Existing Hanoi configuration and remote resolution validation.
- Balanced discovery and locked-list reporting.
- Fetch-once, Neon-first dual persistence when safely supported.
- Current-data reconciliation and three unchanged rechecks.

Out of scope:

- Other provinces.
- Schema redesign or migration edits.
- Anti-bot bypass.
- Cross-database atomicity.
- More than 100 selected products.
- Git history or remote changes.

## Risk Classification

Risk flags:

- Data model.
- Audit/security.
- External systems.
- Existing behavior.
- Weak proof.

Hard gates:

- Database migration.
- Credentials and external provider access.

## Work Phases

1. Inspect runtime/config capabilities without exposing environment values.
2. Classify and validate Neon; migrate only when completely empty.
3. Validate SQLite integrity and capture row-count baselines.
4. Validate the existing Hanoi location locally and remotely.
5. Prove or implement fetch-once dual-write orchestration.
6. Discover and lock a diverse bounded sample.
7. Crawl sequentially with stop conditions.
8. Reconcile Neon/SQLite and verify unchanged behavior.
9. Record credential-free evidence and Harness trace.

## Stop Conditions

Stop before detailed product requests if:

- Neon is missing tables, partially split, or otherwise unknown.
- SQLite integrity or foreign keys fail.
- Hanoi province, ward, or required address is absent.
- Remote location resolution does not match Hanoi.
- Fetch-once Neon-first dual-write cannot be guaranteed.
- CAPTCHA, challenge, repeated 403, repeated location mismatch, or unstable
  Neon persistence occurs.
- Validation requirements would need to be weakened.

## Current Status

Stopped before provider access because the existing active Hanoi configuration
has `address: null`. Neon setup and SQLite read-only validation completed
successfully. Discovery, detailed crawl, dual-write, reconciliation, and
unchanged rechecks remain blocked until an approved non-personal representative
address is supplied through the existing location configuration.


The environment-based continuation resolved the exact `Phường Cầu Giấy` ID,
confirmed the representative address, and completed one Neon-first and SQLite
smoke product successfully. The broader balanced discovery and batch crawl
remain pending; the one-off helper does not replace the production dual-write
runtime tracked in Backlog 2.


The subsequent balanced discovery locked 84 URLs with the requested 36/24/24 category split. Detail execution stopped after two HTTP-200 laptop payloads could not create a PostgreSQL task: the temporary orchestration used task type `hanoi_product`, which violates the existing migration-001 task-type check. The failure happened before catalog persistence and therefore did not create partial product data. Do not resume the checkpoint until the helper uses the existing `location_product` task type and the operator explicitly authorizes refetching the two failed URLs.
