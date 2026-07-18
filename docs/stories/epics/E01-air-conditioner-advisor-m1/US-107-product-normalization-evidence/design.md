# Design

## Placement

- `backend/app/domain/air_conditioner/normalization.py` — pure normalization
  logic and field parsers.
- `backend/app/domain/air_conditioner/evidence.py` — `EvidenceRef` construction
  and the `NormalizedProduct` container returned to callers.
- Reuse the frozen `NormalizedAirConditioner`, `EvidenceRef`, and `StockStatus`
  contracts from `backend/app/contracts/schemas.py`. This story implements
  against that shape; it does not redefine it.

## Contract of the normalizer

- `normalize_air_conditioner(record: dict) -> NormalizedProduct` normalizes one
  raw catalog record.
- `normalize_catalog(records: list[dict]) -> list[NormalizedProduct]` normalizes
  a page/search result and enforces a single shared `source_snapshot`.
- `NormalizedProduct` is a frozen dataclass holding `product`
  (`NormalizedAirConditioner`), `evidence` (`dict[str, EvidenceRef]` keyed by
  normalized field name), and `missing_fields` (`tuple[str, ...]`).

## Source-to-field mapping

- Structured top-level fields: `sale_price` → `sale_price_vnd`,
  `list_price` → `list_price_vnd`, `discount_percent`, `region_code`,
  `stock_status`, `rating`, `sold_count`, `url` → `source_url`,
  `source_snapshot`, plus identity fields (`product_id`, `external_key`,
  `name`, `brand`, `model`).
- Labeled technical specs (`technical_specifications.sections[].attributes`,
  Vietnamese keys) parsed into numbers: HP, BTU, room-area range, CSPF, energy
  stars, rated power (W), annual energy (kWh), noise min/max (dB), warranty
  months, installation cost (VND), inverter (`Có`/`Không` → bool).

## Evidence

- Every populated field gets an `EvidenceRef(path, source_snapshot)`. Paths are
  JSONPath strings rooted at `$`, consistent with the catalog's own
  `evidence_paths` (e.g. `$.sale_price`,
  `$.technical_specifications.sections[1]`).
- A field whose source is absent is added to `missing_fields`, left `null`, and
  gets no evidence entry.

## Derived and empty fields

- `promotion_text` is not a raw source field. It is a deterministic template
  over the factual discount, `f"Giảm {discount_percent}% trong dữ liệu tổng hợp"`,
  and its evidence points at `$.discount_percent` (the fact behind the text). If
  `discount_percent` is absent, `promotion_text` is `null`.
- `technical_specifications` and `product_information` stay as the contract
  default `{}` for M1. Their raw content is reachable through evidence paths, so
  the normalized product carries only typed scalar fields, not the raw nested
  blobs.

## Parsing and rejection rules

- Numeric parsers strip Vietnamese unit suffixes and grouping separators
  (`12.000 BTU`, `1.200.000 đ`, `650 kWh/năm`, `18 dB`, `5 sao`).
- Room area `"15 - 20 m²"` → `(15.0, 20.0)`; a single value fills both bounds.
- Unparseable numerics, snapshot mismatch across a page, a non
  `air_conditioner` category, or a missing required identity/source field raise
  `ValueError`. Malformed is never silently coerced.

## Determinism

- No I/O, no randomness, no model calls. Same record in → same normalized
  output and evidence out. The committed per-record `normalized_fixture` is the
  golden oracle for all 14 M1 products.
