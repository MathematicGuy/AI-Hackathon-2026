# US-123 Business KPIs, Viability, and Pilot Pathway Baseline (Vietnamese)

## Status

implemented

## Lane

normal

## Product Contract

A Vietnamese-language, judge- and partner-facing baseline exists at
`docs/product/requirements/business-viability-pilot-pathway-m1.md` covering:
measurable business KPIs mapped to the partner brief's D1 outcomes and the
M1.9 release targets; explicit business-viability hypotheses with pilot
verification methods; and a pilot pathway aligned to the brief's D3
definition (scope, phases, signing conditions, RACI, data/security
requirements, multi-category expansion roadmap). The document is additive and
changes no frozen contract behavior.

## Relevant Product Docs

- `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md`
- `docs/product/air-conditioner-advisor-m1-contract.md`
- `PROJECT_MANAGEMENT.md` §5

## Acceptance Criteria

- Every D1 outcome maps to at least one measurable KPI with a measurement
  source and target.
- Viability hypotheses each name a concrete pilot verification method.
- The pilot pathway states scope, duration, phases with gates, signing
  conditions, RACI, and required partner data exactly consistent with the
  brief's D3/E sections.
- The multi-category expansion order follows the brief's H2 category logic.
- No frozen contract, PRD behavior, or architecture rule is modified.

## Design Notes

- Commands: none (documentation story).
- Domain rules: none changed; references frozen release-gate thresholds only.
- UI surfaces: none.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | n/a |
| Integration | n/a |
| E2E | n/a |
| Platform | n/a |
| Release | Repository governance validator passes with the new document linked from the requirements index. |

## Harness Delta

Registered as a normal-lane story with the governance validator as the verify
command; intake #4 recorded 2026-07-18.

## Evidence

- 2026-07-18: document authored in Vietnamese per Cường's language decision;
  requirements index updated; governance validator run recorded in the story
  completion proof.
