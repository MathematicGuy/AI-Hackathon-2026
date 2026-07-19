# DMX Sales Advisor — Golden Evaluation Bundle

Generated, verifiable golden dataset for the multi-category sales advisor bot,
spearheaded on **product recommendation + comparison**. Scope derived from
`../chat_history_buy_product.json`; product ground truth extracted from
`../Spec_cate_gia.xlsx`.

## Files

| File | What |
|---|---|
| `product-fixture.json` | 136 products across 10 categories, real DMX tool-payload shape, seeded with foils (cheap/premium, in/out-of-stock, missing-spec). Snapshot `dmx-golden-fixture-2026-07-18`. |
| `golden-conversations.jsonl` | **FULL** set: 147 scored cases / 39 conversations. One line = one turn = one scored eval case (`<conversation_id>#t<n>`). Each case has `tier: full`. |
| `golden-conversations.sample.jsonl` | **SAMPLE** set: 39 cases / 24 conversations — a fast, representative smoke slice (all atomics + all edge conversations + one full category journey; covers 45/48 axes). |
| `coverage-manifest.json` | axis -> case-id map; counts by capability/category/severity. |
| `dmx-sales-advisor-rubric-v1.md` | judge rubric referenced by every case. |
| `scripts/golden/run_eval.py` | runnable evaluation harness (see below). |

Regenerate: `python scripts/golden/build_fixture.py && python scripts/golden/build_golden.py`
Verify data: `python scripts/golden/check_golden.py` (fails on any untraceable
claim, missing product, tool-discipline or budget-filter violation).

## Running the evaluation

```
# --set sample = fast smoke (39 cases) ; --set full = everything (147 cases), default
python scripts/golden/run_eval.py --set sample --runner mock    # quick sanity -> PASS
python scripts/golden/run_eval.py --set full   --runner mock    # full oracle -> 147/147 PASS
python scripts/golden/run_eval.py --set full   --runner noisy   # perturbed -> gate FAIL
python scripts/golden/run_eval.py --set full   --runner http --url http://localhost:8000/advise --out report.json
```
`check_golden.py` also takes `--set full|sample`. Use `sample` in pre-commit /
fast CI, `full` in the release gate.

The harness replays each conversation turn-by-turn (feeding prior turns as
history) and scores per-dimension pass rates + a **P0 release gate** (tool,
grounding, guardrail, explanation must be 100%). Exit code 0 = gate PASS, 1 = FAIL.

Plug the real bot: implement an adapter returning, per turn, the prediction
schema below. `--runner http` already POSTs `{session_id, message, history}` to
your endpoint and expects this JSON back:

```
{ "intent": str, "answer_type": str,
  "tool_call": {"name": str, "args": {...}} | null,
  "product_ids": [int, ...],
  "explanation_text": str }
```

Scored dimensions — all 15 rubric dimensions, each counted only on the turns it
applies to. `kind`: **auto** = deterministic; **proxy** = offline heuristic
(a `--judge llm` hook can upgrade proxy dims to model-judged quality).

| Dimension | P0 | kind |
|---|---|---|
| tool_correct | P0 | auto |
| one_tool_per_turn | P0 | auto |
| grounding_no_fabrication | P0 | auto |
| numeric_grounding | P0 | auto |
| no_match_handled | P0 | auto |
| policy_refusal | P0 | auto |
| explanation_grounded | P0 | proxy |
| comparison_quality | P0 | proxy |
| disclose_missing | P0 | proxy |
| explanation_quality_judged | P0 | judge (`--judge`) |
| comparison_quality_judged | P0 | judge (`--judge`) |
| intent_correct | | auto |
| answer_type_correct | | auto |
| filter_correct | | auto |
| multi_turn_state | | auto |
| clarify_decision | | proxy |
| language_mirroring | | proxy |
| robustness | | proxy |

Release gate = all P0 dimensions at 100%. Sanity: `mock` -> 89/89, gate PASS
(exit 0); `noisy` -> ~75%, gate FAIL (exit 1), demonstrating the harness
discriminates (drops grounded facts, fabricates a product, injects a fake price,
misses a guardrail).

- `numeric_grounding` (auto, P0): any price-like number (>=6 digits) in the reply
  must belong to a referenced product, the user's message, or the history — so a
  bot that returns real product ids but states a wrong price is caught.
- `--judge {none,stub,llm}` adds model-judged explanation/comparison quality:
  - `stub` — offline coherence proxy (facts + length + verdict); runs with no key.
  - `llm` — grades via OpenRouter; set `OPENROUTER_API_KEY` and optional
    `JUDGE_LLM_MODEL` (default `deepseek/deepseek-v4-flash`). Fails **closed**
    (judged dims fail) if the key is missing or the call errors.
  Judged dims add `explanation_quality_judged` / `comparison_quality_judged` (P0).

## Composition (verified)

- Capability: recommend 44, compare 17 (spearhead = 61/89 ≈ 69%), support 14,
  guardrail/property 14.
- Categories (10): Máy lạnh, Tủ Lạnh, Máy giặt, Màn hình, Máy tính để bàn,
  Máy tính bảng, Máy nước nóng, Đồng hồ thông minh (+ mixed/atomic).
- Severity: P0 41, P1 48. Distinct coverage axes: 48.

## Case schema

```
eval_case_id, conversation_id, turn_index, category,
capability,                       # recommend | compare | support | guardrail | property
input { message, user_info?, prior_state? },
expected {
  intent,
  tool_call { name, args } | null,   # exactly one tool per turn, or null (text)
  slots_extracted {},
  candidate_product_ids [],          # eligible set for recommendation (budget/stock/brand filtered)
  grounded_claims [ { product_id, field, value } ],   # each value == fixture field, checker-enforced
  answer_type,                       # recommendation | comparison | clarification | no_match | text | guardrail_block | delivery_info | order_confirmation
  explanation? {                     # recommend/comparison only (31 cases)
    must_mention [],                 # grounded facts the reply must surface (price, spec, ...)
    main_selling_point_hint,         # need-tied selling point (recommend)
    worth_paying_more { cheaper_id, pricier_id, price_gap_vnd, differentiator_field },  # compare
    verdict_required, tradeoffs_min
  }
},
assertions [], judge_rubric_id, severity_if_failed, coverage_axes [],
catalog_snapshot, is_golden, note
```

## Coverage highlights

- Recommendation: need-input variety, clarify-vs-answer, budget/brand/stock/region
  filters, change-constraints, show-more (exclude shown), edge no-match, budget
  boundary (inclusive), brand-not-carried, out-of-stock -> alternative.
- Comparison: two-by-name/id, second-pair, energy dimension, only-one-given -> ask,
  cross-category -> decline, missing-spec -> disclose, compare -> recommend.
- Properties: grounding/anti-hallucination (checker-enforced), tool selection &
  discipline (one tool/turn, no double-call), guardrails (secret/system-prompt/
  source-code/hate), refuse-on-uncertainty, conflict handling, language mirroring,
  robustness (no-diacritics, terse "1"/"ok", empty message).

## Guarantees & limits

- Every `grounded_claims.value` is copied from `product-fixture.json` and
  re-verified by `check_golden.py` — no fabricated prices/specs/stock.
- All PII is synthetic (e.g. "Nguyễn Văn A", 0900000000). No real PII from the
  source logs was copied.
- `Trạng thái` (stock) is synthesized as deterministic foils (the xlsx has no
  live stock); treat stock as fixture-defined, not real-time.
- The fixture samples ~8-22 products/category from the xlsx (bounded for review),
  not the full 1000+ rows. Widen in `scripts/golden/build_fixture.py` (`CATS`).

## Governance note

`data/` is gitignored (`.gitignore:57`) — these files need `git add -f` to
commit. This bundle was produced directly from the data per request; formal
harness intake / story registration was not run.
