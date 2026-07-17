# Air Conditioner Advisor M1 Contract

## Status and authority

This contract freezes M1.0 interfaces derived from the approved
`WORKFLOW-MVP(4).md`. Decision
`docs/decisions/0009-m1-explanation-model-routing.md` overrides the former
GPT-5.4 Mini explainer references.

Fixture data under `data/aircon-m1-test-data/` is synthetic. It must never be
presented as current Điện Máy XANH data.

## Runtime ownership

- GPT-5.4 Nano classifies intent and extracts a structured need patch.
- Deterministic code normalizes, filters, ranks, selects role winners, and
  deduplicates display cards.
- `deepseek/deepseek-v4-flash` through OpenRouter explains verified results
  only and cannot rerank.
- LangGraph owns workflow execution and state persistence.
- Langfuse owns turn traces, datasets, and evaluation scores.

## Frozen enums

Supported intents, exactly:

`new_search`, `change_constraints`, `more_recommendations`,
`compare_products`, `product_detail`, `check_availability`, `stop`,
`unsupported`.

Formal roles, exactly:

`best_overall`, `best_value`, `cheapest_qualified`.

Answer types, exactly:

`clarification`, `recommendation`, `comparison`, `more_products`,
`product_detail`, `no_match`, `guardrail_block`, `stop`.

## API envelope

Request fields:

- `session_id: str | null`
- `request_id: str | null`
- `user_id: str | null`
- `message: str`
- `region_code: str | null`

Response fields:

- `session_id: str`
- `request_id: str`
- `trace_id: str`
- `data: RecommendationOutput`

The response key is `data`, never `result`.

Error fields:

- `session_id: str | null`
- `request_id: str | null`
- `trace_id: str | null`
- `error_code: str`
- `message: str`
- `retryable: bool`

Request, trace, and session IDs live only in the outer success or error
envelope. They are not duplicated inside `RecommendationOutput`.

## Canonical graph order

`input_guardrail` → `intent_classifier` → `state_merge` →
`intent_router` → `clarification_decision` or `product_search` →
`product_normalization` → `hard_constraint_filter` →
`availability_decision` → `constraint_recovery` or the three independent
role-ranking nodes → `ui_deduplication` → `response_generation` →
`output_validation` → `next_question_selection` → `memory_write`.

Every user turn is one `advisor_turn` trace. No fourth formal role-ranking
node exists. The canonical trace tuple describes the common path;
`constraint_recovery` is asserted separately as a conditional span.

## Guardrail order

Input:

`word_count` → `regex_payload` → `nemo_input` → `scope` →
`intent_classifier`.

Output:

`instructor` → `pydantic` → `grounding` → `business_rules` →
`nemo_output` → structured response.

Input blocks at 150 words or more. Output generation receives at most one
retry, followed by deterministic fallback.

## State and product invariants

- New explicit corrections override all older values.
- Unknown product values remain null; malformed values are rejected, not
  guessed.
- Hard constraints execute before ranking and cannot be overridden by score.
- Shown, rejected, retrieved, eligible, and displayed product IDs are explicit
  state fields.
- Shown IDs and product cards are unique.
- Cursor advances only after successful product presentation.
- Duplicate role winners retain their roles and render once with merged badges.
- `best_for_primary_priority` is a display-only badge for a useful distinct
  alternative. It is not a fourth formal recommendation role.
- Product cards may include `selection_reason` to identify such alternatives.
- Each response has at most one clarification or next-action question.
- Each clarification cycle has at most three questions.
- Every factual product claim points to evidence from the active source
  snapshot.

## Search and pagination

Search accepts `filters`, `limit`, `cursor`, and
`exclude_product_ids`. It returns `products`, `next_cursor`,
`total_candidates`, `has_more`, and `source_snapshot`.

Default count is three, maximum count per response is ten, and already shown
products are excluded from show-more results.

## M1 fixture contract

- Catalog: `aircon-m1-catalog-enriched.json`, exactly 14 synthetic products.
- Evaluation cases: `aircon-m1-eval-cases.jsonl`, exactly 26 valid JSON rows.
- Validation manifest: `aircon-m1-data-validation.json`, status `pass`.
- Golden case `AIRCON-M1-001`:
  - Best Overall: `AC-M1-002`
  - Best Value: `AC-M1-003`
  - Cheapest Qualified: `AC-M1-006`

`aircon-m1-ranking-fixture.json` is test-only. It is not the production
ranking policy.

## M1.0 exit proof

- Contract schemas import and validate a renderable recommendation payload.
- Frozen enums, model routes, graph nodes, graph ordering, and guardrail
  ordering pass deterministic tests.
- The catalog, JSONL cases, validation manifest, supported-intent coverage, and
  golden role winners pass fixture-integrity tests.
- No M1.1–M1.4 runtime behavior is implemented by this story.
