# Execution Plan

Self-contained plan for US-107. Legacy provenance only:
`docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md` (cannot authorize
scope, file ownership, or RED/GREEN commands).

Depends on: US-106 (raw catalog records and `source_snapshot`), US-121/US-100
(frozen `NormalizedAirConditioner` / `EvidenceRef` contracts).

1. Write all normalization tests and record RED:
   - golden `normalized_fixture` equality for every catalog record;
   - per-field evidence path presence and `source_snapshot` correctness;
   - null preservation for absent fields;
   - malformed rejection (bad numerics, snapshot mismatch, wrong category,
     missing identity/source);
   - `normalize_catalog` shared-snapshot enforcement.
2. Implement `evidence.py` (container + evidence builder) and
   `normalization.py` (parsers + `normalize_air_conditioner` /
   `normalize_catalog`) — the smallest code that passes.
3. Run targeted unit tests and the M1 contract regression.
4. Complete a separate spec/quality review.
5. Record durable proof and a trace.
