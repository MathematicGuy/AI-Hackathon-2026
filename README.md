# AI Product Comparison Advisor

This repository builds an **AI Product Comparison Advisor** for Điện Máy XANH: a
Vietnamese decision-support advisor that understands a customer's real needs,
asks the missing questions, and compares products by practical benefit instead
of raw specs. The product is designed for the retailer's full catalog —
điện thoại, tai nghe, máy lạnh, tủ lạnh, laptop, robot, and more.

**Air conditioners (máy lạnh) are the example use case for Milestone 1**, the
first vertical slice. M1 is deliberately scoped to one category (see ADR-001) so
the general advisor framework — guardrails, need extraction, state, deterministic
ranking, grounded explanation, evaluation — is proven end-to-end before later
milestones extend it to the other categories. Files and schemas named
`air-conditioner`/`aircon` are M1's category-specific slice artifacts, not the whole
product's scope.

The current backend foundation defines the accepted request, response, product,
state, catalog, and graph contracts. Product work is story-gated and uses
synthetic Milestone 1 data; the repository does not claim that those fixtures
are live Điện Máy XANH catalog facts.

## Start Here

Human navigation:

- [Documentation authority registry](docs/README.md)
- [Milestone overview](PROJECT_MANAGEMENT.md)
- [Accepted product contract](docs/product/air-conditioner-advisor-m1-contract.md)
- [Product requirements](docs/product/requirements/air-conditioner-advisor-m1-prd.md)
- [Product architecture](docs/product/architecture/air-conditioner-advisor-m1.md)
- [Story index](docs/stories/README.md)
- [Active workstream trackers](docs/team/now/README.md)

Coding agents must start with [AGENTS.md](AGENTS.md). It requires identity and
AI-log preflight, documentation and tracker checks, and then the appropriate
Harness workflow before implementation.

## Repository Layout

```text
ai-logs/                     AI session policy, member guides, and logs
backend/                     Python application contracts and tests
data/aircon-m1-test-data/    Synthetic Milestone 1 fixtures
docs/
  product/                   Product contract, requirements, architecture, discovery
  stories/                   Bounded story packets and evidence
  team/now/                  Parallel workstream ownership and coordination
  decisions/                 Accepted durable decisions
  references/                Partner-provided source material
scripts/                     Harness and repository validation tools
```

Only `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, and
`PROJECT_MANAGEMENT.md` are allowed as root Markdown files. The placement and
conflict rules for every other document are defined in
[docs/README.md](docs/README.md).

## Local Environment

Copy `.env.example` to `.env` and fill only the values needed by your local
task. `.env` files are ignored; example templates remain trackable. Never
commit, print, or copy credentials into AI logs.

The environment template documents planned provider and frontend interfaces.
It does not imply that every variable is already consumed by application code,
and this repository does not automatically load `.env` during validation.
Provider variable conventions follow the official
[OpenAI quickstart](https://platform.openai.com/docs/quickstart/make-your-first-api-request),
[OpenRouter authentication reference](https://openrouter.ai/docs/api/reference/authentication),
and
[Langfuse SDK guidance](https://langfuse.com/docs/observability/sdk/troubleshooting-and-faq).

## Local Data Platform (PostgreSQL + pgvector)

A local, Dockerized data platform stores the provided product catalog
(`data/dataset/Spec_cate_gia.xlsx`) in PostgreSQL with the `pgvector` extension.
Rationale and scope: see
[docs/decisions/0012-postgres-pgvector-data-platform.md](docs/decisions/0012-postgres-pgvector-data-platform.md).

Prerequisites: Docker + Docker Compose, and a `.env` (copy from `.env.example`)
with `POSTGRES_PASSWORD` set. Run every command from the repository root. The
database has **no host port**: it is reachable only inside the compose network.

Start the database, then apply migrations and ingest the catalog:

```bash
# 1. Start Postgres (internal to the compose network)
docker compose -f infra/docker-compose.yml up -d db

# 2. Migrate + ingest via the ingestion container (in-network)
docker compose -f infra/docker-compose.yml run --rm ingestion \
  sh -c "python -m backend.app.db.migrate && python -m backend.app.ingestion.run --source /app/data/dataset"
```

Ingestion is idempotent (upsert keyed by `sku`); running it again reports every
row as skipped and creates no duplicates.

Everyday operations:

```bash
# Logs
docker compose -f infra/docker-compose.yml logs -f db

# Inspect with psql (example: row counts)
docker compose -f infra/docker-compose.yml exec db \
  psql -U advisor -d advisor -c "SELECT count(*) FROM products;"

# Stop (keep data)
docker compose -f infra/docker-compose.yml down

# Reset (drop the database volume)
docker compose -f infra/docker-compose.yml down -v
```

Optional host-side development — expose Postgres on loopback so `uv` tooling and
host tests can reach it (never use on a shared host):

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d db
# with POSTGRES_HOST=localhost and POSTGRES_PORT=55432 in .env:
uv run python -m backend.app.db.migrate
uv run python -m backend.app.ingestion.run --source data/dataset
uv run python -m pytest backend/tests/unit/ingestion -q
```

## Product Catalog API

A FastAPI service gives read-only HTTP access to the ingested catalog. Agents and
frontends call this API; they never query PostgreSQL directly. Interactive docs
live at `/docs`. Layering is `api/routes → services → repositories`, and all SQL
(parameterized) lives in the repository.

Run it (database must be up, migrated, and ingested):

```bash
# In Docker — serves on http://localhost:8000 (set BACKEND_PORT to change the host port)
docker compose -f infra/docker-compose.yml up -d --build backend

# Or on the host, against the loopback database (dev override running)
uv run uvicorn backend.app.api.main:app --reload
```

Endpoints — every response uses the unified error envelope
`{"error": {"code", "message", "details"}}`:

| Method & path | Agent tool | Purpose |
|---|---|---|
| `GET /health` | — | liveness + database check |
| `GET /api/v1/categories` | `list_categories` | categories with product counts |
| `GET /api/v1/categories/{category_code}/attributes` | `list_category_attributes` | valid attribute-filter keys |
| `GET /api/v1/brands?category_code=` | `list_brands` | brands, optionally per category |
| `GET /api/v1/products/{sku}` | `get_product_detail` | product detail by SKU |
| `POST /api/v1/products/search` | `search_products` | query, category, brands, attribute_filters, sort, paging |
| `POST /api/v1/products/batch` | — | many products by SKU (max 100) |
| `POST /api/v1/products/compare` | `compare_products` | compare up to 5 SKUs |

SKU is the identifier. `attribute_filters` operators: `eq, neq, contains, in,
gte, lte, exists`; keys are validated against the target category; page size max
100. Example:

```bash
curl -s localhost:8000/api/v1/categories
curl -s -X POST localhost:8000/api/v1/products/search \
  -H 'Content-Type: application/json' -d '{
    "category_code": "36",
    "attribute_filters": [{"key": "Loại Gas", "op": "eq", "value": "R-32"}],
    "sort": [{"field": "giá khuyến mãi", "direction": "asc", "numeric": true}],
    "page_size": 5
  }'
```

## Validation

The project requires Python 3.12 or newer. Run the isolated regression suite
without loading local environment files:

```powershell
uv run --no-project --isolated --python 3.12 --with-editable ".[test]" --no-env-file python -m pytest -q
```

Validate repository documentation, tracker ownership, AI logging, local links,
and environment safety:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-repository-governance.ps1
```

For Harness commands and bootstrap details, see
[scripts/README.md](scripts/README.md) and [docs/HARNESS.md](docs/HARNESS.md).
