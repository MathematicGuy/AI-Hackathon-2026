# US-106 Catalog Adapter and Pagination

## Current Behavior

The synthetic 14-product catalog is committed and contract-validated, but no runtime adapter or stable cursor search exists.

## Target Behavior

Provide a read-only catalog adapter and deterministic air-conditioner search with region filtering, limit 1–10, stable cursor scanning, exclusions, candidate count, snapshot, and terminal-page behavior.

## Non-Goals

- Product normalization, eligibility, ranking, provider calls, or graph wiring.
- Treating synthetic fixtures as live product data.
