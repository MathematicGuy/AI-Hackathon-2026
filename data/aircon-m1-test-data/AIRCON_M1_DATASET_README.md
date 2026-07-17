# Air Conditioner Advisor M1 — Synthetic Test Data

## Purpose

This bundle supplies a small deterministic catalog and evaluation dataset for the
Milestone 1 Vietnamese máy lạnh advisor.

All products, prices, stock values, URLs, ratings, sales counts, and specifications
are **synthetic test fixtures**. They must not be presented as current Điện Máy XANH data.

## Files

- `aircon-m1-catalog-enriched.json`
  - 14 synthetic products.
  - Follows the enriched structure of the supplied template.
  - Includes `normalized_fixture` with the exact numeric fields needed by the MVP.
- `aircon-m1-eval-cases.jsonl`
  - 26 line-delimited evaluation cases for CI and Langfuse import.
- `aircon-m1-eval-cases.json`
  - The same cases as one JSON array for manual inspection.
- `aircon-m1-ranking-fixture.json`
  - Simple deterministic scoring policy used only to produce golden role winners.
- `aircon-m1-data-validation.json`
  - Integrity and coverage checks.

## Main MVP example

Input:

```text
Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m², tiết kiệm điện, ít ồn.
```

Expected deterministic fixture result:

```json
{
  "best_overall": "AC-M1-002",
  "best_value": "AC-M1-003",
  "cheapest_qualified": "AC-M1-006"
}
```

The fixture treats `energy_saving` as primary because it appears first and
`low_noise` as secondary. The expected eligible set is:

```json
[
  "AC-M1-001",
  "AC-M1-002",
  "AC-M1-003",
  "AC-M1-004",
  "AC-M1-005",
  "AC-M1-006",
  "AC-M1-007",
  "AC-M1-008"
]
```

## Evaluation coverage

The dataset covers all eight supported intents:

```text
change_constraints, check_availability, compare_products, more_recommendations, new_search, product_detail, stop, unsupported
```

It also covers:

- complete requests;
- missing room size, budget, and location;
- energy-saving and low-noise priorities;
- conflicting and impossible constraints;
- comparison, show-more, product detail, and availability;
- changed budget and room size;
- missing CSPF and noise evidence;
- unavailable stock;
- duplicate role winners and UI deduplication;
- prompt injection and oversized input;
- malformed product data;
- output-validation fallback;
- stop and recommendation rejection;
- unsupported product category.

## Suggested use

### Unit tests

Use `normalized_fixture` directly when testing:

- capacity eligibility;
- hard budget;
- evidence requirements;
- role calculations;
- deduplication;
- pagination exclusions.

### Integration tests

Load the enriched raw fields and verify that normalization reproduces
`normalized_fixture`.

### Langfuse dataset

Import each JSONL row as one dataset item:

- input: `input`
- expected output/rubric: `expected`
- metadata: the remaining top-level fields

### Important ranking note

`m1-simple-ranking-v1` is a **test fixture**, not the final business ranking formula.
Replace its weights only after the production ranking policy is approved, then
regenerate golden role winners and version the fixture.
