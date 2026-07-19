# US-126 Validation

## Proof Strategy

Keep parsing and assignment deterministic under local fixtures, then use a
single bounded live pilot to prove that five configured first-party pages
currently yield reviewable mappings. No test or pilot may write the database.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Existing parser/selector cases plus catalog group derivation, production mapping validation, placeholder fallback, checkpoint resume, force overwrite, and CLI mode gates. |
| Integration | Agent JSON and stream responses project the same representative fields without changing reply text/comparison; CLI writes production mapping and operational evidence atomically. |
| E2E | Re-run the five-group live pilot, then live-test one mapped and one placeholder product turn against the running API/UI. |
| Platform | Frontend lint, typecheck, production build, and visual inspection of the disclosed image figure. |
| Performance | Pilot remains five fetches; all-groups defaults to at least 1.5 seconds between requests with bounded timeout/retry and resume. |
| Logs/Audit | Group status/count only; no response bodies, cookies, or environment values. |

## Fixtures

- Minimal local DMX-like listing HTML with duplicate `src`, `data-src`, and
  protocol-relative image URLs.
- Five explicit pilot category-brand source records.

## Commands

```text
.venv/bin/python -m pytest backend/tests/unit/catalog_images -q
.venv/bin/python -m pytest backend/tests/contract/test_agent_api_contract.py -q
.venv/bin/python scripts/collect_representative_images.py --pilot --limit-groups 5 --resume
cd frontend && npm run check
```

## Acceptance Evidence

- Focused collector, mapping, Agent API, and observability checks: `.venv/bin/python -m pytest backend/tests/unit/catalog_images backend/tests/contract/test_agent_api_contract.py backend/tests/unit/agent/test_observation_api.py backend/tests/unit/agent/test_production_hardening.py -q` → **63 passed**.
- Full backend suite: `.venv/bin/python -m pytest backend/tests -q` → **500 passed, 17 skipped**.
- Pilot resume regression: `.venv/bin/python scripts/collect_representative_images.py --pilot --limit-groups 5 --resume` → **5 cache hits, 5 ready groups, 15 images, 0 not_found, 0 error**.
- Pilot output: `data/processed/representative-images/pilot-5/mapping.json`, `review.csv`, and `summary.json`.
- Catalog derivation returns **238 unique groups**: 234 deterministic first-party source URLs and 4 placeholder-only groups.
- Agent contract checks cover mapped, placeholder, JSON, stream, and non-product projections. A running API transcript for a Samsung refrigerator turn returned the first presented product's official CDN URL with `image_type="representative"` and `mapping_version=1`.
- Frontend `npm run check` passed lint, TypeScript, and the production build for 66 routes.
- Stable assignment was exercised against one real workbook SKU per group twice; each result was identical and returned `image_type="representative"`.

The all-group crawl was intentionally not invoked because the safety contract
requires an explicit `--all-groups` command. No database or per-SKU image field
was written. Browser screenshot proof remains pending after the local dev/CDP
session was interrupted; the production build and API live proof do not replace
that visual check.
