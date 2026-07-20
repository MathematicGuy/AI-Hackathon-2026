# US-125 Design — Structured Storefront Chatbot Presentation

## Domain Model

`AgentPresentation` is a generic E02 view contract, not the air-conditioner M1
`RecommendationOutput` schema.

```text
AgentPresentation
  type: text | recommendation | comparison
  products: PresentedProduct[]
  comparison_rows: ComparisonRow[]
  follow_up_questions: string[]
  warnings: string[]

PresentedProduct
  sku: string
  productidweb: string | null
  name: string
  brand: string | null
  effective_price_vnd: integer | null
  list_price_vnd: integer | null
  discount_percent: number | null
  promotion_text: string | null
  badges: { code: string, label: string }[]
  highlights: { label: string, value: string | null }[]
  image_url: string | null
  product_url: string | null
  rating: number | null
  sold_count: integer | null

ComparisonRow
  label: string
  values: { sku: string, value: string | null }[]
```

Rules:

- The backend selects badges, highlights, comparison rows, and follow-ups from
  the same grounded turn result used to produce `text`.
- One product renders once per response even when it has multiple badges.
- Unknown values stay `null`; the frontend does not infer or replace them with
  static values.
- `sku` is the stable product key. If selected records lack non-empty, unique
  SKUs, the server returns a text presentation instead of rich product UI.
  `productidweb` is nullable and is not a safe catalog hydration key.

## Application Flow

```text
user message
  -> frontend typed agent client
  -> POST /api/v1/agent/respond
  -> E02 guard / understand / tools / grounded response
  -> text + structured presentation from the same verified records
  -> frontend message state
  -> text, recommendation, or comparison renderer
```

For a first-turn comparison without two selected products, the backend returns
its clarification with a `text` presentation and no products or rows. Once a
comparison tool result exists, the backend returns `comparison` with the exact
products used for the answer and rows selected from those same verified
records. A nullable row may be present even when prose omits that incomplete
attribute.

## Interface Contract

The request remains unchanged:

```json
{
  "session_id": "session-or-null",
  "message": "customer message"
}
```

The response is additive:

```json
{
  "session_id": "session-id",
  "request_id": "request-id",
  "intent": "compare_products",
  "text": "grounded fallback answer",
  "flags": [],
  "presented_ids": ["existing-agent-id"],
  "presentation": {
    "type": "text",
    "products": [],
    "comparison_rows": [],
    "follow_up_questions": [],
    "warnings": ["Cần chọn hai sản phẩm có SKU rõ ràng trước khi so sánh."]
  }
}
```

A `comparison` presentation is valid only with at least two products carrying
unique SKUs; every row then contains exactly one value (possibly null) for each
product SKU.

`presentation` is optional during the backend-first rollout. The frontend must
validate the response boundary and fall back to `text` if the field is absent
or unusable. HTTP validation and server errors keep the repository's unified
error envelope; the retry UI must not display stale presentation data.

## Data Model

No database or migration changes. The backend presentation mapper operates on
the in-memory `GenericProduct`, suggestion, and comparison results already used
by the E02 turn. Missing image, URL, rating, or sold data remains null until an
authoritative source is added through a separate decision/story.

## UI / Platform Impact

- Add a typed client boundary under `frontend/src/lib/` and response types under
  `frontend/src/types/`.
- Store the server envelope/presentation in each assistant message.
- Remove query-text comparison classification.
- Convert `ChatComparisonResult` into a pure data-driven renderer.
- Render placeholders for missing images and omit navigation when no trusted URL
  exists.
- Preserve US-124 desktop non-modal and mobile modal behavior.

## Observability

- Keep `request_id` available for sanitized operational diagnostics.
- Do not log message bodies, credentials, or customer personal data.
- Contract/E2E failures should report response type and safe identifiers, not
  raw model prompts or provider payloads.

## Alternatives Considered

1. **Embedded render-ready presentation (selected).** One grounded response and
   no browser-side data reconstruction.
2. **Return SKU then hydrate catalog APIs.** Rejected because two requests can
   disagree and raw catalog attributes do not express server-owned badges or
   selected comparison rows.
3. **Delete the table and retain text only.** Valid emergency fallback but does
   not meet the expected frontend format.
4. **Use `frontend-mvp/` or `/api/v1/advisor/respond`.** Rejected by scope and
   ADR-0015; the route is not mounted in the shipped app.
