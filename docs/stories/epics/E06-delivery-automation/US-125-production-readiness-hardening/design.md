# Design

## Domain Model

No new domain entities. The story reuses the existing evidence-based dimension
registry in `backend/app/agent/catalog/dimensions.py` (`Dimension`,
`dimension_display`, `dimension_value`, `better_of`, `rankable`,
`dimensions_for`) and the existing `Comparison` / `ComparisonItem` value objects
in `backend/app/agent/tools/compare.py`.

The one new value object is a presentation projection of an existing
comparison, not new business logic:

- `ComparisonView` — the rows the UI renders.
- `ComparisonProduct` — id, name, brand, effective/list price, discount
  percent, gift.
- `ComparisonRow` — dimension label, unit, explanation, per-product display
  value, and the winning product id where the dimension is rankable.

Placeholder spec values are already excluded by `dimension_display`, which
returns `None` for anything in `PLACEHOLDERS`. The projection keeps that
behavior: a row is emitted only when every compared product has a real value.

## Application Flow

`_compare_flow` in `backend/app/agent/graph.py` already computes exactly the
data the frontend table needs while building its text lines. The change is to
build the structured view from that same computation and attach it to the
reply, instead of discarding it after formatting.

1. `_compare_flow` resolves the two product ids and calls `compare_products`.
2. It iterates `dimensions_for(state.need.category_code)` — dimension-driven
   per category, as the accepted behavior requires.
3. The same loop now also appends a `ComparisonRow`.
4. `AgentReply` carries `comparison: ComparisonView | None`.
5. The API layer serializes it on both `/respond` and the `done` event of
   `/respond/stream`.

Text output is unchanged. The structured block is strictly additive, so a
client that ignores the field sees exactly today's behavior.

## Interface Contract

`POST /api/v1/agent/respond` response gains one optional field:

```json
{
  "session_id": "...", "request_id": "...", "intent": "compare_products",
  "text": "...", "flags": [], "presented_ids": ["...", "..."],
  "comparison": {
    "price_delta": 1500000,
    "products": [
      {"id": "...", "name": "...", "brand": "...", "effective_price": 8990000,
       "list_price": 10490000, "discount_percent": 14.3, "gift": null}
    ],
    "rows": [
      {"label": "Độ ồn", "unit": "dB", "explain": "...",
       "values": {"<id>": "24 dB", "<id2>": "27 dB"}, "winner_id": "<id>"}
    ]
  }
}
```

`comparison` is `null` for every non-comparison turn. The `done` event of the
streaming endpoint carries the same object.

New error responses on the agent endpoints:

- `413` when the request body exceeds the configured maximum message length.
- `429` when the per-client rate limit is exceeded, with `Retry-After`.

## Data Model

No schema change and no migration. `REQUIRE_POSTGRES` becomes a recognized
environment flag: when true, `postgres_available()` failing is fatal at startup
rather than a silent fallback to the Excel workbook.

## UI / Platform Impact

- `ChatComparisonResult` stops owning product data. It becomes a pure
  presentational component driven by the `comparison` payload, and renders
  nothing when the payload is absent. The keyword heuristic
  (`isComparisonQuery`) is removed.
- `ChatbotAssistant` gains an `AbortController` with a request timeout, a
  user-visible error state, and a retry affordance.
- Login, checkout, and account-order screens gain an explicit demo banner; the
  login screen no longer prints the mock OTP to the user.
- Deployment: production compose reads a dedicated environment file; the stale
  root compose file is removed and the documented deploy path points at
  `docker-compose.production.yml`.

## Observability

- Replace `print` with module-level `logging.getLogger(__name__)` in
  `backend/app/agent/api.py`, `backend/app/db/migrate.py`, and
  `backend/app/ingestion/run.py`.
- Feedback logging records session id, message index, and rating only — never
  the customer's message text.
- The Postgres adapter logs the underlying exception before failing or falling
  back, so a degraded data source is never silent.
- The LLM client logs provider attempt failures that it currently swallows and
  retries once with backoff on transient errors before moving to the next
  candidate.

## Alternatives Considered

1. **Keep the hardcoded frontend table and only correct its prices.** Rejected:
   it stays out of sync with the catalog and can still contradict the agent's
   own answer, which is the actual defect.
2. **Have the frontend re-query a separate comparison endpoint.** Rejected: it
   duplicates the agent's product-selection logic and adds a second round trip
   and a second source of truth.
3. **Parse the comparison table out of the reply text.** Rejected: brittle and
   would break the moment the copy changes.
4. **Add authentication to the agent endpoints instead of rate limiting.**
   Deferred by explicit human direction: the storefront has no real auth, so
   rate limiting plus payload caps is the proportionate control for this phase.
