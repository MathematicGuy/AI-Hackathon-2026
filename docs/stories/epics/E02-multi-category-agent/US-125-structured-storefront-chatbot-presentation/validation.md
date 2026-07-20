# US-125 Validation — Structured Storefront Chatbot Presentation

## Proof Strategy

Contract tests prove the server owns the presentation payload; component and
browser proof establish that `frontend/` renders only supplied data. Cross-stack
checks compare response product keys/values with visible cards and rows. The
story is `in_progress`; its registered verification command is
`scripts/verify-us125.ps1`. No proof column may become true until the applicable
checks have run successfully.

## Acceptance Criteria

- `frontend/` continues to call `POST /api/v1/agent/respond`; no code uses
  `frontend-mvp/` or `/api/v1/advisor/respond`.
- The API keeps existing response fields and adds a validated `presentation`
  payload shaped for text, recommendation, and comparison rendering.
- Recommendation/comparison products include stable SKU and server-owned
  nullable presentation fields; badges and comparison rows are not computed in
  the browser.
- `ChatbotAssistant` does not classify response type from the user's query.
- `ChatComparisonResult` contains no static products, prices, badges, rows,
  ratings, links, or follow-up prompts.
- A first-turn comparison clarification displays no comparison table.
- Missing image/link/rating/sold/spec values remain visibly unavailable and do
  not become invented defaults.
- A product with multiple badges renders once.
- Absent/invalid presentation data falls back to grounded `text` without stale
  cards; HTTP failure preserves retry behavior.
- Desktop independent browsing and mobile modal/focus behavior from US-124 stay
  unchanged.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Backend presentation mapper; frontend response parser; nullable values; product dedupe; discriminator rendering. |
| Integration | Shipped FastAPI route returns additive recommendation/comparison payloads from the same records as text; session ID round-trips; errors keep their envelope. |
| E2E | Clarification → recommendation → comparison; response products/rows match visible UI; text fallback; missing data; error/retry; reset starts a new session. |
| Platform | Desktop non-modal browsing plus 320/400px mobile modal, focus, scrolling, and comparison overflow. |
| Performance | Record response payload size and ensure one agent request per turn; no browser hydration waterfall. |
| Logs/Audit | Safe `request_id` diagnostics only; no message bodies, secrets, or provider payloads in proof artifacts. |

## Fixtures

- Deterministic category with at least three products and two role badges on one
  product.
- Two comparable products with stable SKUs, prices, promotions, and shared
  attributes.
- One product missing image, URL, rating, sold count, and an optional attribute.
- Text-only clarification, policy/guardrail, no-result, and server-error cases.

## Commands

Existing checks to retain:

```powershell
uv run --no-project --isolated --python 3.12 --with-editable ".[test]" --no-env-file python -m pytest backend/tests/contract/test_agent_api_contract.py backend/tests/integration/api/test_agent_endpoint.py -q
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

`scripts/verify-us125.ps1` is the registered Harness verification entrypoint.
It must include the implemented backend integration and frontend browser checks
before the story can be completed.

## Acceptance Evidence

None yet. Implementation is in progress; no product proof is claimed until the
registered verification entrypoint and required visual checks pass.
