# Implementation plan

## Convergence
- **Satisfaction threshold:** 95
- **Stratified order:** Tier 1

## Now (next up)

### T1 — Analyze naming occurrences in `.md` files
- **files/areas:** `docs/**/*.md` and root `*.md` files.
- **validation:** Custom check to ensure all files containing "air conditioner", "air-conditioner", "máy lạnh" or similar are identified.
- **acceptance:** A complete list of occurrences and contexts is gathered.
- **status:** done
- **notes:** Gathered occurrences via grep_search. Found matches in root files, index files, and epic folders.

### T2 — Categorize and design the dry-run plan
- **files/areas:** `.wgm/specs/naming_reconciliation.md`
- **validation:** Check mapping definitions.
- **acceptance:** Occurrences categorized into General Naming vs Category-Specific.
- **status:** done
- **notes:** Mapped terms. Determined that code/schema references must be kept to avoid contract violation, while high-level titles and headers are safe to rename.

### T3 — Create the Naming Reconciliation Plan report
- **files/areas:** `docs/reports/naming-reconciliation-plan.md`
- **validation:** Verify markdown formatting and link resolution.
- **acceptance:** The markdown report is written and saved.
- **status:** done
- **notes:** Created `docs/reports/naming-reconciliation-plan.md` with detailed file-by-file diffs.

### T4 — Execute safe naming updates across `.md` files
- **files/areas:** `README.md`, `PROJECT_MANAGEMENT.md`, `docs/**/*.md`
- **validation:** Confirm that all safe-to-rename occurrences are updated.
- **status:** done
- **notes:** Surgically updated README.md, PROJECT_MANAGEMENT.md, docs/README.md, docs/product/README.md, docs/product/air-conditioner-advisor-m1-contract.md, docs/product/architecture/air-conditioner-advisor-m1.md, docs/product/requirements/air-conditioner-advisor-m1-prd.md, docs/stories/backlog.md, and docs/stories/epics/E01-air-conditioner-advisor-m1/US-106-catalog-adapter-pagination/overview.md.

### TZ — Demo validation
- **files/areas:** `docs/reports/naming-reconciliation-plan.md` and modified documentation files.
- **validation:** Confirm that the report contains file list, diffs, and does not touch Python/JSON schemas, and that all 152 backend tests pass.
- **acceptance:** Report and backend tests run green end-to-end.
- **status:** done
- **notes:** Verified that the plan is correctly formatted, renames are applied, and all 152 backend tests passed.
