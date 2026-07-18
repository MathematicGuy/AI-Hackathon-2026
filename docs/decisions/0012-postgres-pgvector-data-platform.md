# 0012 Local PostgreSQL + pgvector Data Platform

Date: 2026-07-18

## Status

Accepted

## Context

Milestone 1 was deliberately fixture-based and in-memory: no application
database, catalog served from a committed JSON snapshot, and conversation
checkpointing on LangGraph `AsyncSqliteSaver` (see the product architecture and
ADR-014). The partner has now provided real source data in `data/dataset/`
(a 14-category product catalog as XLSX, six policy/FAQ Markdown files, and two
chat-history JSON files). We need a persistent, queryable data foundation that
runs entirely on a local Ubuntu machine, is packaged with Docker Compose, and
can later move to an Ubuntu server with minimal change — without deploying,
configuring a domain, or enabling HTTPS yet.

`data/aircon-m1-test-data/` is explicitly out of scope for this work and is not
used as a schema or design source.

## Decision

Introduce a local data platform as an **additive** layer, alongside — not
replacing — the existing M1 runtime:

1. **PostgreSQL 16 with the `pgvector` extension** is the durable store for the
   product catalog, a knowledge base (policy/FAQ chunks + embeddings), and
   imported chat scenarios. It is packaged with Docker Compose and reachable
   only inside the Docker network (no host port) during local development.
2. **`pgvector` is used only for the knowledge base** (RAG over policy/FAQ).
   Product filtering and role ranking remain deterministic Python. This
   preserves ADR-014 ("no vector store for product ranking in Milestone 1").
3. **Schema migrations are plain, numbered SQL files** under
   `backend/migrations/`, applied by a small idempotent Python runner
   (`backend/app/db/migrate.py`) tracked in a `schema_migrations` table. This
   matches the existing numbered-SQL convention (`scripts/schema/*.sql`) and
   avoids adding an ORM.
4. **Product specifications are stored as JSONB.** The 14 category sheets share
   only a small set of columns and otherwise have disjoint spec columns;
   per-category nullable columns would be unworkable. Relational tables model
   the shared entities (brands, categories, products, offers) and lineage.
5. **Ingestion logic lives in `backend/app/ingestion/`** and is reused by a thin
   CLI entrypoint (`scripts/ingest.py`). It validates, normalizes, computes a
   `content_hash`, upserts idempotently, records an `import_run`, and reports
   per-file ok/skipped/error counts. Source files under `data/dataset/` are
   treated as read-only and are never modified.
6. **Chat PII is masked before storage.** Phone numbers, emails, and national
   ID patterns in Vietnamese free text are masked; raw PII is never written to
   the database, logs, or exceptions. Any intermediate artifacts go under
   `data/processed/`, which is git-ignored.
7. **Embeddings are generated through a configurable API** (OpenAI/OpenRouter
   via the existing `openai` client and env-owned settings). When no key is
   configured the chunk is still stored with a `NULL` embedding, so local runs
   are never blocked.
8. **A minimal FastAPI service** exposes `/health`, `/health/db`, and a
   deterministic, Postgres-backed `POST /api/v1/advisor/respond` for the
   air-conditioner slice. It performs no LLM ranking and returns the frozen
   backend Pydantic contract (`backend/app/contracts/schemas.py`). Frontend
   integration is deferred; the endpoint is verified with `curl` and `pytest`.

Conversation checkpointing stays on LangGraph `AsyncSqliteSaver`; the new
Postgres platform is separate and does not change it.

## Alternatives Considered

1. Alembic + SQLAlchemy for migrations. Rejected for this phase: it adds an ORM
   the project does not otherwise use and is heavier than the numbered-SQL
   convention already present.
2. Hundreds of nullable per-spec columns. Rejected: category spec columns are
   disjoint; JSONB keeps the schema stable across all 14 categories.
3. Local embedding model (sentence-transformers). Considered for on-premise
   alignment but not chosen for this phase; the operator selected API
   embeddings. The vector column and RAG path are provider-agnostic.
4. Using `pgvector` for product ranking. Rejected to preserve ADR-014;
   deterministic ranking remains authoritative.

## Consequences

Positive:

- Real, queryable catalog/knowledge/scenario data with source lineage and
  idempotent re-imports.
- Portable Docker Compose that carries to an Ubuntu server by changing
  environment values only.
- Deterministic ranking and the frozen M1 contract are preserved.

Tradeoffs:

- API embeddings depend on an external provider and a key; without one, vector
  search is unavailable until embeddings are backfilled.
- The minimal advisor endpoint is a demo slice, not the full M1.5 graph; it
  omits guardrails, clarification, and grounded LLM explanation.
- There is a known shape drift between the backend contract and the current
  `frontend-mvp/lib/types.ts`; reconciling it is deferred until frontend
  integration.

## Follow-Up

- Reconcile backend contract vs. frontend types before wiring the frontend to
  live mode.
- Backfill knowledge-base embeddings once an embedding provider is configured.
- Register the corresponding story/tracker for this data-platform workstream;
  the current identity is not yet mapped to a tracker in `docs/team/now/`.
- Best-effort repair of the malformed `chat_history_buy_product.json` is
  tracked with explicit error counts rather than silent skips.
