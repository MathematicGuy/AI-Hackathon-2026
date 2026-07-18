# US-107 Product Normalization and Evidence

## Current Behavior

`search_air_conditioners` (US-106) returns raw catalog records as `dict`s with a
shared `source_snapshot`. Nothing converts those raw records into the frozen
`NormalizedAirConditioner` contract shape, and no evidence path is attached to a
normalized field. Downstream hard-constraint filtering and ranking cannot run
against raw records.

## Target Behavior

Provide a deterministic normalizer (air-conditioner slice) that turns one raw
catalog record into a `NormalizedAirConditioner` plus a per-field evidence map:

- Derive typed fields from the raw source: prices to integer VND, HP, BTU,
  recommended room-area range, CSPF, energy-label stars, rated power, annual
  energy, indoor-noise range, warranty months, installation cost, inverter,
  and stock status.
- Attach an `EvidenceRef` (JSONPath rooted at `$`, carrying the record's
  `source_snapshot`) for every field the normalizer populates.
- Preserve genuinely missing fields as `null`; never invent a value.
- Reject malformed values (unparseable numbers, snapshot mismatch, wrong
  category) instead of guessing.
- Normalize every product in the M1 catalog to exactly its committed
  `normalized_fixture`.

## Non-Goals

- Hard-constraint filtering, eligibility, availability, ranking, deduplication,
  graph wiring, or provider calls (US-108 onward).
- Treating synthetic fixtures as live Điện Máy XANH product data.
- Data-confidence scoring beyond preserving nulls and disclosing missing fields.
