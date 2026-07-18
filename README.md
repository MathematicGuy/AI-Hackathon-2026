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
- [Product requirements (Stale)](docs/product/stale-requirements/business-viability-pilot-pathway-m1.md)
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
  backend/app/agent/         Constrained single-agent pipeline (LangGraph)
  backend/app/api/           FastAPI routes, schemas, and error handlers
  backend/app/services/      Application service layer (catalog, advisor)
  backend/app/guardrails/    Input/output guardrails and intent extraction
  backend/app/graph/         LangGraph graph definitions
  backend/app/tools/         Agent tool implementations
data/aircon-m1-test-data/    Synthetic Milestone 1 fixtures
data/dataset/                Provided product catalog (Spec_cate_gia.xlsx) and policies
frontend/                    Next.js decision UI (M1.8)
docs/
  product/                   Product contract, stale-requirements, architecture, discovery
  stories/                   Bounded story packets and evidence
  team/now/                  Parallel workstream ownership and coordination
  decisions/                 Accepted durable decisions
  references/                Partner-provided source material
infra/                       Docker Compose files and backend Dockerfile
scripts/                     Harness and repository validation tools
```

Only `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`,
`PROJECT_MANAGEMENT.md`, and `ARCHITECTURE_v2.md` are allowed as root Markdown files. The placement and
conflict rules for every other document are defined in
[docs/README.md](docs/README.md).

## Local Environment

Copy `.env.example` to `.env` and fill only the values needed by your local
task. `.env` files are ignored; example templates remain trackable. Never
commit, print, or copy credentials into AI logs.

The environment template documents backend provider credentials and frontend
interface variables (`NEXT_PUBLIC_ADVISOR_MODE`, `NEXT_PUBLIC_ADVISOR_API_URL`).
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

# 2. Apply schema migrations
docker compose -f infra/docker-compose.yml run --rm --no-deps backend \
  python -m backend.app.db.migrate

# 3. Ingest the catalog (ingestion service requires --profile tools)
docker compose -f infra/docker-compose.yml --profile tools run --rm ingestion
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

## Production Deployment

`docker-compose.production.yml` runs nginx, the frontend, the backend, and the
database as one project on one network, so the stack has a single lifecycle,
health gate, and rollback unit. It reads `.env.production`, never the developer
`.env`.

```bash
bash scripts/deploy-preflight.sh   # checks the env file, creates the volume
docker compose -f docker-compose.production.yml up -d --build
```

Nginx is the only container published to the host, and by default it binds to
`127.0.0.1:8080` (`HTTP_BIND`, `HTTP_PORT`). Ports 3000 and 8000 are not
published and must not be accessed directly. The container nginx routes `/api/`
and `/health` to the backend and everything else to the frontend, so the browser
talks to one origin and no CORS configuration is involved.

TLS and the public domain belong to a host nginx in front of this stack. It
terminates HTTPS and proxies to the loopback port above; the container nginx
keeps the `/api/` routing so that rule stays versioned with the code rather
than living only on the server. The host server block needs:

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    # The agent waits on an upstream LLM call; the 60s default truncates it.
    proxy_read_timeout 120s;
}
```

Set `HTTP_BIND=0.0.0.0` and `HTTP_PORT=80` only when no host nginx is involved
and this stack is the outermost edge.

### First deploy on a new host

Two steps are easy to miss. `scripts/deploy-preflight.sh` checks both and
refuses to pass until they are satisfied:

```bash
# Production credentials live in their own file. Any key that has been in a
# working tree is considered exposed — rotate it before it goes in here.
cp .env.production.example .env.production   # set POSTGRES_PASSWORD + a provider key

# Checks the env file and creates the external catalog volume, which Compose
# will not invent for itself (`up` would abort: external volume ... not found).
bash scripts/deploy-preflight.sh

docker compose -f docker-compose.production.yml up -d --build

# Migrations run automatically; the catalog load does not. Run it once,
# or every catalog endpoint returns an empty result.
docker compose -f docker-compose.production.yml run --rm ingestion
```

The volume is external on purpose: `docker compose down -v` cannot delete it,
so a redeploy cannot wipe the catalog.

The backend runs with `REQUIRE_POSTGRES=true`, forced in the compose file: if
the database is unreachable it fails to start instead of quietly serving the
read-only Excel workbook. The agent endpoints are unauthenticated, so nginx
rate limits `/api/v1/agent/` and the application caps message length
(`AGENT_MAX_MESSAGE_CHARS`) and request rate (`AGENT_RATE_LIMIT_REQUESTS`).

The frontend calls the agent at the relative path `/api/v1/agent/respond`. No
backend hostname is baked into the client bundle, and there is no
`NEXT_PUBLIC_AGENT_API_URL`. For host-side development, `next dev` proxies
`/api/*` to `BACKEND_ORIGIN` (default `http://127.0.0.1:8000`); that variable is
read on the server only and never reaches the browser.

The stack attaches to the existing `advisor-data-platform_pgdata` volume, which
is declared external so `docker compose down -v` cannot delete the catalog.
Never combine this file with `infra/docker-compose.dev.yml`: that override
publishes PostgreSQL on the host and is for local development only.

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
