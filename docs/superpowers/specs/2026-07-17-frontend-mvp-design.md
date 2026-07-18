# Frontend MVP (Testing Harness) — Design Spec

> **Legacy provenance artifact:** Retained for historical context. It is not
> current authority. Follow `docs/README.md` and do not add new files under
> `docs/superpowers/`.

- Date: 2026-07-17
- Status: Approved (brainstorming)
- Sources of truth:
  `docs/product/requirements/air-conditioner-advisor-m1-prd.md`,
  `docs/product/architecture/air-conditioner-advisor-m1.md`
- Owner: Đinh Nhật Thành

## 1. Purpose and scope

Build `frontend-mvp/`, a **testing-only** frontend for the Milestone 1 air-conditioner
(máy lạnh) shopping advisor. It exists to exercise the end-to-end conversational
flow with **mock data** while the backend is unfinished, and to be **ready for API
plugin** — swapping mock for the real backend must require changing one env var
(and, if the shipped JSON differs, the parse in one branch of one file).

In scope:

- A single chat route that renders every one of the 8 `RecommendationOutput.answer_type`
  states from mock fixtures.
- All 13 UI components named in
  `docs/product/architecture/air-conditioner-advisor-m1.md` §5.1.
- A single typed API module (`lib/advisor-api.ts`) that branches mock vs. live.
- Keyword-matched mock scenarios so any `answer_type` can be reached by typing.

Out of scope:

- Any backend, real LLM calls, persistence, or auth.
- Client-side ranking, price math, eligibility, badge computation, or evidence
  selection. The frontend renders server-owned fields only.
- Renaming an existing `frontend/` folder — none exists, so the harness is created
  fresh at `frontend-mvp/`.

## 2. Stack and conventions

- **Next.js 15 (App Router) + TypeScript**, **Tailwind CSS**, **shadcn/ui** primitives
  (copied into `components/ui/`, not a black-box dependency).
- Package manager: **npm**.
- UI copy: **Vietnamese** (matches the Điện Máy XANH domain). Missing fields render as
  `"không có" / "chưa rõ"`, never inferred.
- Default run mode: `NEXT_PUBLIC_ADVISOR_MODE=mock` — runs with zero backend.

## 3. Directory layout

```
frontend-mvp/
  app/
    layout.tsx
    page.tsx            # renders <ChatPanel />
    globals.css
  components/
    chat/
      ChatPanel.tsx     # owns conversation state, calls sendMessage
      MessageList.tsx
      MessageInput.tsx
    advisor/
      AnswerRenderer.tsx        # switch on answer_type
      ClarificationCard.tsx
      AssumptionBanner.tsx
      RecommendationSummary.tsx
      ProductCard.tsx
      PricePremiumPanel.tsx
      SourceDrawer.tsx
      MoreProductsAction.tsx
      ComparisonView.tsx
      ProductDetailView.tsx
      AvailabilityState.tsx
      NoMatchState.tsx
      GuardrailState.tsx
    ui/                 # shadcn primitives
  lib/
    advisor-api.ts      # THE swap point
    types.ts            # TS mirror of the Pydantic contract
    ids.ts              # client-side session_id / request_id generation
    mock/
      scenarios.ts      # ordered keyword matchers -> fixture selector
      fixtures.ts       # one canned AdvisorResponse per answer_type
      products.ts       # normalized AC mock products
  .env.example
  README.md
```

## 4. Type contract (`lib/types.ts`)

Direct TypeScript mirror of the real Pydantic models so the live swap needs **no type
changes**. Field names and optionality match the source docs exactly.

- `AdvisorRequest` — `{ session_id?, request_id?, user_id?, message, region_code? }`
- `AdvisorResponse` — `{ session_id, request_id, trace_id, data: RecommendationOutput }`
- `AdvisorError` — `{ session_id?, request_id?, trace_id?, error_code, message, retryable }`
- `RecommendationOutput` — full shape from
  `docs/product/architecture/air-conditioner-advisor-m1.md` §8.3:
  `answer_type` (the 8 literals), `session_id`, `request_id`, `trace_id`, `intent`,
  `customer_need`, `assumption_summary`, `clarification_question`, `role_winners`,
  `product_cards`, `price_premium_verdicts`, `next_question`, `citations`,
  `has_more_products`, `next_cursor`, `warnings`.
- `RoleWinners` / `RoleWinner` — exactly the **3** roles (`best_overall`, `best_value`,
  `cheapest_qualified`); `RoleWinner` = `{ product_id, role, score?, evidence[], reason_codes[] }`.
- `BadgeKind` — the 3 roles **plus** `best_for_primary_priority` (display badge only,
  never a 4th role).
- `ProductCard` — `{ product_id, badges: BadgeKind[], selection_reason?, ...explanation, ...specs }`:
  - explanation fields (§8.2 / §4.15): `why_it_fits`, `main_selling_point`,
    `practical_benefit`, `price`, `trade_offs[]`, `when_not_to_choose`,
    `evidence` refs, optional `alternative_comparison`.
  - spec fields from `NormalizedAirConditioner` (§5.6): `name`, `brand`, `model?`,
    `sale_price_vnd?`, `list_price_vnd?`, `discount_percent?`, `stock_status`,
    `horsepower_hp?`, `cooling_capacity_btu?`, room-area range, `inverter?`, `cspf?`,
    `energy_label_stars?`, noise range, `warranty_months?`, `rating?`, `sold_count?`,
    `source_url`.
- `PricePremiumVerdict` — includes `worth_paying_more: WorthPayingMore`
  (`"yes" | "no" | "conditional" | "insufficient_data"`) plus the two product ids and
  what the price difference buys.
- `ProductCitation`, `Assumption`, `AirConditionerNeed` — mirrored as used by the
  rendered fields.

## 5. API layer (`lib/advisor-api.ts`) — the single swap point

```ts
export async function sendMessage(req: AdvisorRequest): Promise<AdvisorResponse>
```

- Fills `session_id` / `request_id` client-side when absent (`lib/ids.ts`).
- Branches on `NEXT_PUBLIC_ADVISOR_MODE`:
  - `mock` → `resolveScenario(req.message)` returns a fixture; a small artificial delay
    (~400ms) makes loading/skeleton states visible.
  - `live` → `fetch(NEXT_PUBLIC_ADVISOR_API_URL + "/api/v1/advisor/respond", { method: "POST", headers, body: JSON.stringify(req) })`,
    parse into `AdvisorResponse`.
- Components import **only** `sendMessage` for data. Backend integration = flip
  `NEXT_PUBLIC_ADVISOR_MODE` to `live` and set `NEXT_PUBLIC_ADVISOR_API_URL`.


## 6. Mock scenarios (`lib/mock/`)

Ordered keyword matchers on `message`; first match wins; fall-through → `recommendation`.

| Trigger (VN / EN) | `answer_type` |
| --- | --- |
| `so sánh` / `compare` | `comparison` |
| vague need / no budget / `phòng` alone | `clarification` |
| rude / off-topic / injection markers | `guardrail_block` |
| `xem thêm` / `more` | `more_products` (advances `next_cursor`, honors shown ids) |
| `chi tiết` / a product name | `product_detail` |
| impossible constraints (e.g. `5 triệu` for a large room) | `no_match` |
| `cảm ơn` / `dừng` / `stop` | `stop` |
| default | `recommendation` |

Fixtures use realistic normalized AC products. At least one fixture has a **multi-role
winner** (one product wins `best_overall` + `best_value`) so UI dedup is exercised, plus
a third card carrying `best_for_primary_priority` with `selection_reason:
"useful_distinct_alternative"`.

## 7. Components (`docs/product/architecture/air-conditioner-advisor-m1.md` §5.1)

`AnswerRenderer` switches on `answer_type` and dispatches to the right component each turn:

- **clarification** → `ClarificationCard` (renders `clarification_question`, ≤1 question).
- **recommendation** → `AssumptionBanner` + `RecommendationSummary` (role_winners) +
  deduped `ProductCard`s + `PricePremiumPanel` + `MoreProductsAction` + `next_question`.
- **comparison** → `ComparisonView`.
- **more_products** → appended `ProductCard`s + updated `MoreProductsAction`.
- **product_detail** → `ProductDetailView`.
- **no_match** → `NoMatchState`.
- **guardrail_block** → `GuardrailState`.
- **stop** → terminal message, no next_question.
- `SourceDrawer` opens from any card to show `citations` / evidence.
- `AvailabilityState` is a sub-component used inside product rendering to surface a
  card's `stock_status` (available / unavailable / unknown). It is not a top-level
  `answer_type`; the `product_detail` and `recommendation` fixtures include an
  `unavailable` and an `unknown` stock case so this state is exercised.

Rules enforced in the UI: dedup by `product_id` with merged badges; a product appears
once even with multiple badges; the useful alternative shows its explicit
`selection_reason`; no chain-of-thought exposure; render only server-owned fields.

## 8. Verification

- `npm run build` and `npm run typecheck` pass.
- `npm run dev`, then type each trigger phrase and confirm the correct component renders
  for all 8 `answer_type`s.
- Confirm the multi-role product renders **once** with two badges, and the alternative
  card shows its `selection_reason`.
- Confirm flipping `NEXT_PUBLIC_ADVISOR_MODE=live` changes only the data source (no
  component or type changes).

Optional (say if in scope): a Playwright smoke test that drives all 8 states.

## 9. Decisions made without asking

- **UI language: Vietnamese** — matches the Điện Máy XANH domain.
- **Package manager: npm** — no repo lockfile dictates otherwise.

## 10. Open questions

- None blocking. Playwright smoke test is optional and deferred unless requested.
