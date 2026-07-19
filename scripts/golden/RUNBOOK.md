# RUNBOOK — DMX Sales Advisor Golden Test Set

How to build, verify, and run the evaluation. Everything is offline and
deterministic; no API key needed for the default runners.

---

## A. Design rationale (why this test set is built the way it is)

**A1. Scope comes from real data, not assumptions.** The capability surface was
reverse-engineered from `data/dataset/chat_history_buy_product.json` — a real
agent trace with `system`, `user`, `assistant`, `tool` roles. The 7 real tools
(`search_product_dmx_v3`, `compare-search`, `get-time-delivery-dmx`,
`check_infor_customer`, `payment_process`, `create_order_dmx`,
`installment-links`) and the real user intents (157 utterances) define what the
bot must do. We did not invent capabilities.

**A2. Ground truth comes from real products.** `product-fixture.json` is
extracted from the real `Spec_cate_gia.xlsx` (1000+ rows) into the exact
tool-payload shape the bot actually receives (`Giá gốc`/`Giá khuyến mãi`/
`Trạng thái`/`Thông tin sản phẩm`/`Khuyến mãi`/...). Prices, specs, brands are
real. We sample a bounded set per category, deliberately seeded with **foils** —
cheap/premium, in/out-of-stock, missing-spec — so filtering and disclosure are
actually exercised, not trivially satisfied.

**A3. Spearhead = recommendation + comparison.** 73% of full-set cases target the
two core advisory skills; ordering/payment/delivery are covered as short tails
(P1), matching the product priority.

**A4. Cases are grouped into real conversations.** Each conversation is a
multi-turn purchase journey (discover → spec Q&A → compare → decide), turns share
state via `prior_state`, and every turn is one independently-scored case
(`<conversation_id>#t<n>`). This tests multi-turn memory and correction, not just
isolated prompts.

**A5. Coverage is explicit and measurable.** Every case carries `coverage_axes`;
`coverage-manifest.json` maps each of 48 axes to the cases covering it. Axes span
tool selection/discipline, budget/stock/brand/region filters, no-match, missing
spec disclosure, guardrails, robustness (no-diacritics, terse, empty), multi-turn
state, and grounded explanation. Edge cases are first-class (no-match+recovery,
cross-category compare, out-of-stock→alternative, brand-not-carried, budget
boundary, only-one-product, injection/system-prompt probes).

**A6. Explainability is a graded requirement.** Recommendation/comparison cases
carry an `explanation` spec: the grounded facts the answer must surface
(`must_mention`), a need-tied main selling point, a trade-off, and a
"worth-paying-more" verdict (with the real price gap + differentiator). So the
bot is judged on *why*, not only *what*.

**A7. Two tiers.** `sample` (39 cases, 45/48 axes) for fast pre-commit / CI;
`full` (147 cases) for the release gate. Sample keeps whole conversations intact
so multi-turn scoring stays valid.

**A8. No real PII.** Source logs contain real names/phones/addresses; the golden
set uses only synthetic placeholders. This is a correctness *and* a compliance
property.

## B. Evaluation methodology (why the scores are trustworthy)

**B1. Grounding is enforced, not assumed.** `check_golden.py` re-derives every
`grounded_claims.value` from the fixture and fails if any value, product id,
budget filter, or comparison arity is off. The dataset cannot ship an
unverifiable claim.

**B2. The harness scores against the fixture, not vibes.** For each turn the bot
returns `{intent, answer_type, tool_call, product_ids, explanation_text}`.
Scoring checks, deterministically: correct tool + grounded args, one tool per
turn, no fabricated product id, recommendation candidates inside the budget/stock
filter, no_match returns nothing, guardrail probes are refused. These need no
human judgment.

**B3. Anti-hallucination on numbers.** `numeric_grounding` extracts every
price-like number (>=6 digits) from the reply and requires it to belong to a
referenced product, the user's message, or the history — catching a bot that
returns real product ids but states a *wrong price*. (Free-text hallucination,
not just id fabrication.)

**B4. Explanation quality has two layers.** An offline proxy (must-mention facts +
verdict keyword) runs with no key; `--judge stub|llm` adds a model judge that
grades relevance/clarity/verdict, failing **closed** if the key/model is
unavailable (a missing judge never silently passes).

**B5. Rubric-mapped, gated.** All ~17 dimensions map to
`dmx-sales-advisor-rubric-v1.md`. Eight are P0 (release-blocking): tool,
one-tool-per-turn, grounding, numeric grounding, no-match, guardrail, and the two
judged/proxy explanation dims. The **release gate = all P0 at 100%**, surfaced as
an exit code for CI.

**B6. The harness is proven to discriminate (not a rubber stamp).** The `mock`
oracle scores 147/147 → gate PASS (the scoring is satisfiable). The `noisy`
runner injects realistic defects — drops grounded facts, fabricates a product,
injects a fake price, misses a guardrail — and the harness drops to ~75-82% and
FAILs the gate on exactly those dimensions. A test harness that passes a
deliberately broken bot would be worthless; this one demonstrably does not.

**B7. Fully reproducible.** `build_fixture → build_golden → check_golden →
run_eval` is deterministic (no randomness); the same inputs always yield the same
cases and scores, so results are auditable and diffable.

**Summary of the argument:** scope and data are real; every claim is traceable to
the fixture and machine-checked; explanation is required and graded; the gate is
objective and CI-enforced; and the harness is shown to fail broken bots. That is
what makes the design defensible.

---

## 0. Prerequisites

- Python 3.10+ with `openpyxl` (`pip install openpyxl`).
- Run all commands from the repo root `e:\VAI\AI-Hackathon-2026`.
- Windows console: prefix with `PYTHONIOENCODING=utf-8` (Git Bash) or
  `$env:PYTHONIOENCODING="utf-8"` (PowerShell) so Vietnamese prints correctly.
- Source data present: `data/dataset/Spec_cate_gia.xlsx`.

## 1. Build the product fixture (from the xlsx)

```
python scripts/golden/build_fixture.py
```
Writes `data/dataset/golden/product-fixture.json` (136 products / 10 categories,
real tool-payload shape, seeded with price/stock/missing-spec foils).

## 2. Generate the golden conversations

```
python scripts/golden/build_golden.py
```
Writes `data/dataset/golden/golden-conversations.jsonl` (89 cases / 31
conversations) and `coverage-manifest.json`. Every grounded claim is copied from
the fixture, so it is verifiable.

Two tiers are written: `golden-conversations.jsonl` (**full**, 147 cases) and
`golden-conversations.sample.jsonl` (**sample**, 39 cases — fast smoke slice
covering 45/48 axes). Both `check_golden.py` and `run_eval.py` take
`--set full|sample` (default `full`).

## 3. Verify data integrity (must pass before evaluating)

```
python scripts/golden/check_golden.py --set full
python scripts/golden/check_golden.py --set sample
```
Fails loudly if any grounded value does not match the fixture, any product id is
missing, a comparison lacks exactly 2 ids, a no_match has candidates, or a
recommendation candidate breaks the budget filter. Expect: `ALL CHECKS PASSED`.

## 4. Run the evaluation

```
# fast smoke (39 cases) -> gate PASS, exit 0
python scripts/golden/run_eval.py --set sample --runner mock

# full oracle sanity -> 147/147, gate PASS, exit 0
python scripts/golden/run_eval.py --set full --runner mock

# perturbed -> gate FAIL, exit 1 (proves the harness discriminates)
python scripts/golden/run_eval.py --set full --runner noisy --out report-noisy.json

# your real bot
python scripts/golden/run_eval.py --set full --runner http --url http://localhost:8000/advise --out report.json

# add model-judged explanation/comparison quality
python scripts/golden/run_eval.py --runner mock --judge stub          # offline, no key
export OPENROUTER_API_KEY=sk-...    # PowerShell: $env:OPENROUTER_API_KEY="sk-..."
python scripts/golden/run_eval.py --runner http --url ... --judge llm  # real LLM judge
```

Scores all rubric dimensions per applicable turn (auto + proxy, plus judged when
`--judge` is set) and prints a table + the P0 release gate. Exit code: 0 = gate
PASS, 1 = FAIL (usable in CI). `numeric_grounding` catches replies that state a
price/number not present in the referenced products. `--judge llm` fails closed
(judged dims fail) if `OPENROUTER_API_KEY` is missing.

## 5. Run against the LIVE app API (`--api agent`)

The app ships a live agent (`backend/app/agent`) exposed at
`POST /api/v1/agent/respond` (the same endpoint the frontend calls,
`NEXT_PUBLIC_AGENT_API_URL`, default `http://127.0.0.1:8000`). Its request is
`{session_id?, message}` and its response is
`{session_id, request_id, intent, text, flags[], presented_ids[]}`.

`--api agent` makes the harness speak exactly this contract — it POSTs
`{session_id, message}` and adapts the response (intent passthrough,
`presented_ids` -> `product_ids`, `text` -> the answer, `flags` -> guardrail):

```
# start the agent (team's usual command), then:
python scripts/golden/run_eval.py --api agent --runner http \
       --url http://127.0.0.1:8000/api/v1/agent/respond --out report-agent.json

# offline dry-run of agent-mode scoring (no server needed):
python scripts/golden/run_eval.py --api agent --runner mock     # -> gate PASS
python scripts/golden/run_eval.py --api agent --runner noisy    # -> gate FAIL
```

What agent-mode scores and skips (important for a fair read):
- The live agent is **advisory-only** and its intent enum is
  `new_search / change_constraints / more_recommendations / compare_products /
  product_detail / check_availability / policy_question / stop / unsupported`.
  Each golden case carries `expected.agent_intent` + `agent_scope`; the 26
  order/payment/delivery/greeting turns are **out of the agent's scope** and are
  skipped (reported), leaving 121 in-scope cases.
- Scored dims (verifiable without pinning the agent's ranking): `intent_correct`
  (P0-gated via agent_intent), `grounding_no_fabrication` (P0 — `presented_ids`
  must be real product ids from `all-product-ids.json`, all 6248 xlsx SKUs),
  `no_match_handled` (P0), `policy_refusal` (P0), `clarify_decision`,
  `robustness`, `language_mirroring`, `comparison_has_verdict`.
- Deliberately NOT scored in agent-mode: `tool_correct` / `answer_type` (the API
  exposes neither) and product-specific dims (`filter_correct`, must-mention
  `explanation_grounded`, `numeric_grounding`) — the agent ranks over the full
  catalog, so its exact picks are not pinned by this golden set. To score those,
  pin the agent to the fixture snapshot or use the harness prediction schema.

## 5b. Any other bot (`--api harness`, `--runner http`)

For a bot you control, return the full prediction schema and get all dimensions:
```json
{ "intent": "product_recommendation", "answer_type": "recommendation",
  "tool_call": {"name": "search_product_dmx_v3", "args": {...}},
  "product_ids": [320893, 333353], "explanation_text": "..." }
```
The harness POSTs `{session_id, message, history}` in this mode. `tool_call: null`
when the bot answers in text.

## 5c. Test-set composition (numbers to expect on a run)

| Set | Cases | Conversations |
|---|---|---|
| FULL (`golden-conversations.jsonl`) | 147 | 39 (22 multi-turn journeys/edges + 17 single-turn atomics) |
| SAMPLE (`golden-conversations.sample.jsonl`) | 39 | 24 |
| Agent-mode (`--api agent`) | 121 scored | 26 skipped (out of the advisory agent's scope) |

Spearhead: recommend 78 + compare 29 = 107/147 (~73%). Categories: 10.
Coverage axes: 48 (full) / 45 (sample).

The 26 agent-mode skips are the purchase-funnel tails the advisory agent cannot
do yet — they are intentional, not failures:

| Skipped intent | Count | Where |
|---|---|---|
| check_delivery | 7 | t5 of the 6 funnel journeys + CONV-EDGE-DELIVERY |
| create_order | 6 | t8 of the 6 funnel journeys |
| choose_payment | 6 | t7 of the 6 funnel journeys |
| provide_customer_info | 6 | t6 of the 6 funnel journeys |
| greeting | 1 | ATOM-GREETING |

The 6 "funnel" journeys are `CONV-AC-01, WM-01, TB-01, FR-02, MN-02, SW-02`
(each loses its 4-turn tail under `--api agent`). All other 33 conversations are
100% in-scope. When the agent gains order/payment/delivery tools, flip
`agent_scope` / extend `AGENT_INTENT` in `build_golden.py` and the 26 cases
return — no rewrite needed.

Sanity numbers: `--api agent --runner mock` -> ~120/121 pass, gate PASS;
`--runner noisy` -> ~55%, gate FAIL.

## 6. Read the report

`report.json` contains `per_dim` (pass/applicable per dimension), `gate_pass`,
and `results` (per-case `pass` + `failed` dimension list). Sort failing cases by
their `failed` array to prioritise fixes. P0 dims failing block the gate.

## 7. Regenerate everything

```
python scripts/golden/build_fixture.py && \
python scripts/golden/build_golden.py && \
python scripts/golden/check_golden.py && \
python scripts/golden/run_eval.py --runner mock
```

## Troubleshooting

- Garbled Vietnamese / `UnicodeEncodeError`: set `PYTHONIOENCODING=utf-8`.
- Files not showing in `git status`: `data/` is gitignored (`.gitignore:57`);
  use `git add -f data/dataset/golden` to commit.
- `openpyxl` missing: `pip install openpyxl`.
- Widen coverage: increase per-category counts in `CATS` (build_fixture.py) or
  add journeys in `build_golden.py`, then rerun steps 1-4.
