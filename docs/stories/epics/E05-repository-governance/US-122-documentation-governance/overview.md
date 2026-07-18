# US-122 Documentation Authority and Local Environment

## Current Behavior

Repository-level instructions, team trackers, product requirements,
architecture, discovery material, and external references do not yet have one
enforced placement and authority model. The repository root therefore mixes
agent entrypoints with working documents, and a contributor can follow a stale
path or treat a plan, tracker, architecture note, handoff, or session log as a
source of product authority.

The local environment contract is also incomplete unless a safe
`.env.example`, an ignored local `.env`, and deterministic validation are
maintained together. These gaps affect auditability because an agent can begin
work with the wrong context, ownership, dependency, or file boundary.

## Target Behavior

The repository has one documented authority hierarchy, one canonical
documentation registry, and a mandatory read gate for human and agent
contributors. The root Markdown allowlist is limited to:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `README.md`
- `PROJECT_MANAGEMENT.md`

Working documents have these canonical destinations:

| Material | Canonical destination |
| --- | --- |
| Team trackers | `docs/team/now/` |
| `WORKFLOW-MVP(4).md` | `docs/product/requirements/air-conditioner-advisor-m1-prd.md` |
| Product `ARCHITECTURE.md` | `docs/product/architecture/air-conditioner-advisor-m1.md` |
| `JTBD_Completed.md` | `docs/product/discovery/air-conditioner-advisor-jtbd.md` |
| Partner brief | `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md` |

`docs/README.md` registers canonical documents and their authority. The agent
gate requires bounded reads in a fixed order, detects ownership or authority
conflicts before mutation, and allows explicitly authorized
repository-governance work to proceed without a product tracker when that work
is registered as its own story, as US-122 is.

The repository provides a secret-free `.env.example`, keeps the developer's
local `.env` ignored and untracked, migrates references atomically with the
documents, and validates placement, stale paths, logging policy, environment
hygiene, and repository tests before merge and push.

## Affected Users

- Team members who own or review repository work.
- AI coding agents that read repository instructions and story context.
- Maintainers who merge, rebase, or validate concurrent branches.

## Affected Product Docs

- `docs/README.md`
- `docs/team/now/`
- `docs/product/requirements/air-conditioner-advisor-m1-prd.md`
- `docs/product/architecture/air-conditioner-advisor-m1.md`
- `docs/product/discovery/air-conditioner-advisor-jtbd.md`
- `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md`
- `docs/product/air-conditioner-advisor-m1-contract.md`
- `docs/decisions/0011-documentation-authority-and-placement.md`

## Non-Goals

- Changing product code or product behavior.
- Adding data tooling, business metrics, pilot behavior, or observability
  implementation.
- Adding or changing CI/CD.
- Translating Vietnamese content while moving it.
- Moving flat Harness documents, the current product contract, existing
  canonical documents, or the `docs/superpowers/` history.
- Treating plans, handoffs, trackers, or AI session logs as product authority.
