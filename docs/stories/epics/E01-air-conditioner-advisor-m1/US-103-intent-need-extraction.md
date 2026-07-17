# US-103 Vietnamese Intent and Need Extraction

## Status

planned

## Lane

normal

## Product Contract

The intent node classifies a Vietnamese message into exactly one of the eight
frozen intents and extracts a validated `AirConditionerNeed` patch, using
`INTENT_MODEL` (GPT-5.4 Nano) through an injected adapter with structured
output, one retry, and Pydantic validation. Unknown values stay `null`; the
model never invents numeric values. On provider or schema failure the node
returns a deterministic keyword fallback and flags `intent_model_degraded`. The
node never filters, ranks, or selects role winners.

## Relevant Product Docs

- `docs/product/air-conditioner-advisor-m1-contract.md` — frozen enums, runtime ownership.
- `docs/product/requirements/air-conditioner-advisor-m1-prd.md` §4.3, §10.1.
- `docs/product/architecture/air-conditioner-advisor-m1.md` §5.4, §6.

## Acceptance Criteria

- The golden Vietnamese request extracts `new_search`, `budget_max_vnd=20000000`,
  `room_size_m2=18`, `energy_saving` primary + `low_noise` secondary (explicit).
- All eight intents classify correctly through the injected extractor.
- Extraction preserves `null`, rejects extra keys, and enforces confidence∈[0,1]
  and requested count∈[1,10].
- Provider error and schema-invalid output both fall back deterministically with
  `intent_model_degraded`; the fallback never invents numbers.
- The deterministic keyword fallback reaches ≥ 90% intent accuracy on the
  curated Vietnamese scenario set.
- `INTENT_MODEL` is exactly `gpt-5.4-nano`; no ranking model is used.

## Design Notes

- Domain rules: `IntentExtractor` Protocol; `OpenAIIntentExtractor` (injected
  client); `classify_and_extract(message, *, extractor) -> tuple[IntentOutput, list[str]]`;
  `fallback_intent(message)` keyword classifier.
- API: none public. Files: `backend/app/models/__init__.py`,
  `backend/app/models/openai_intent.py`, `backend/app/graph/nodes/intent.py`,
  plus the two unit test modules.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Golden need; eight intents; null-preserving; extra-key rejection; bounds; provider/schema fallback + degraded flag; keyword-fallback ≥90% accuracy; exact model id. |
| Integration | None (injected fake; real call is US-101). |
| E2E | None. |
| Platform | None. |
| Release | Contract suite stays green (no enum/schema drift). |

## Harness Delta

Registered normal-lane story; verify command runs the intent unit tests plus the
contract suite. Intake #9 recorded 2026-07-18.

## Evidence

Pending implementation.
