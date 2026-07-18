# Spec: Naming Reconciliation Plan

## JTBD (job to be done)
Provide a clear, risk-mitigated dry-run plan of what needs to be changed across the project's `.md` files to unify the high-level project name to **AI Product Advisor** while preserving category-specific technical reference names (like "air conditioner", "máy lạnh", etc.) for Milestone 1.

## User-visible success criteria
- A detailed dry-run report `docs/reports/naming-reconciliation-plan.md` created in the workspace.
- Clear distinction between general naming (safe to rename) and category-specific naming (must keep).
- Exact line-by-line diff examples showing the proposed replacements.

## Magic moment
- **The whoa:** Other agents and humans will instantly understand the distinction between the general "AI Product Advisor" framework and the "Air-Conditioner" M1 slice, preventing naming collisions.
- **Demo path:** Inspect the report [naming-reconciliation-plan.md](file:///E:/VIN-INTERNSHIP/AI-Hackathon-2026/docs/reports/naming-reconciliation-plan.md).
- **Smallest end-to-end slice:** The dry-run plan compiled for all `.md` files in `docs/` and root folders.

## Acceptance criteria → backpressure

| Criterion (EARS) | How it's verified (command/check) |
|---|---|
| When the report is written, it shall contain a list of all files analyzed. | Manual check of the file list in the report. |
| When the report is written, it shall detail the specific proposed changes with diffs. | Manual check of diff sections. |
| When the report is written, it shall not propose changing python code files, variable names, or frozen contracts. | Check that no code files are listed for mutation. |

## Assumptions
- We only propose modifications to `.md` files (READMEs, indexes, specs, retrospectives). We do not touch code (`.py`) or JSON schemas (`.json`).
