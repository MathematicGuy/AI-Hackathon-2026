# 0011 Documentation Authority and Placement

Date: 2026-07-17

## Status

Accepted

ADR number 0010 remains reserved and is not reassigned by this decision.

## Context

The repository root mixes agent entrypoints with team trackers, product
requirements, product architecture, discovery output, and reference material.
Those files overlap in subject matter but do not have equal authority. Without
an explicit hierarchy and canonical registry, a contributor can mistake an
architecture note or plan for accepted product behavior, miss a tracker
dependency, or continue using a stale path after a move.

Repository-aware agents also need one deterministic read order that composes
the existing AGENTS and AI logging policies with product, Harness, tracker, and
story authority. Local environment documentation must support identity
resolution without encouraging secrets in tracked files.

This is high-risk governance work because it affects audit/security behavior,
existing repository consumers, proof quality, and several documentation
domains at once.

## Decision

Adopt a canonical documentation registry, a root Markdown allowlist, an
authority hierarchy, and an enforced read gate.

The only Markdown files allowed at the repository root are:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `README.md`
- `PROJECT_MANAGEMENT.md`

Canonical placement is:

| Material | Canonical destination |
| --- | --- |
| Team trackers | `docs/team/now/` |
| `WORKFLOW-MVP(4).md` | `docs/product/requirements/air-conditioner-advisor-m1-prd.md` |
| Product `ARCHITECTURE.md` | `docs/product/architecture/air-conditioner-advisor-m1.md` |
| `JTBD_Completed.md` | `docs/product/discovery/air-conditioner-advisor-jtbd.md` |
| Partner brief | `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md` |

Authority is resolved as follows:

1. The user controls mutation and scope.
2. The applicable `AGENTS.md` controls agent behavior.
3. `ai-logs/README.md` controls AI logging.
4. The accepted product contract and an Accepted ADR that explicitly
   supersedes it control product behavior.
5. The PRD is the product baseline.
6. Product architecture is subordinate to the product contract and PRD.
7. A story packet bounds story scope and acceptance.
8. The Harness matrix controls registered status and proof.
9. The mapped tracker controls assignment, dependencies, worktree, branch, and
   file boundaries.
10. `PROJECT_MANAGEMENT.md` is a milestone overview only.
11. Plans cannot expand approved scope.
12. Handoffs and AI session logs are non-authoritative records.

Agents must read, in order: the client shim and root AGENTS; the AI logging
policy, identity/member guide, template, and log; request classification;
`docs/README.md`; the `docs/team/now/` index and, for product work, the
explicitly mapped tracker; for a registered repository-governance story, its
documented product-tracker exception; for changes, Harness bootstrap, intake,
and the active matrix; bounded context
under `docs/CONTEXT_RULES.md`; the accepted product contract and any explicitly
superseding Accepted ADR; the PRD; product architecture; story packet;
the registered story's implementation plan; for product work, confirmation
that the mapped tracker links to that plan; exact files and callers; then the
ready gate. Proof, status, trace, tracker, and log closeout follow
implementation.

Unresolved identity, logging failure, tracker or ownership ambiguity,
tracker/matrix disagreement, a blocked dependency, a shared worktree,
duplicate story or file ownership, product-authority conflict, or missing
validation/proof blocks mutation. Explicitly authorized repository-governance
work may proceed without a product tracker when registered as its own story.

Track a secret-free `.env.example`; keep local `.env` ignored and untracked.
Move documents and update their active references atomically. Verify the
result with `scripts/validate-repository-governance.ps1`,
`scripts/validate-ai-logging.ps1`, repository tests, whitespace and stale-path
scans, environment-ignore checks, and Harness proof and trace before merge and
push.

## Alternatives Considered

1. Leave the root clutter in place and rely on explanatory links. Rejected
   because the same material would retain ambiguous placement and stale paths
   would remain difficult to detect.
2. Perform a full migration of flat Harness documents and lifecycle records.
   Rejected because it expands the change into Harness storage and process
   migration without improving the requested product-document authority.

## Consequences

Positive:

- Contributors have one registry, placement map, authority hierarchy, and read
  order.
- The root remains limited to durable repository entrypoints and milestone
  orientation.
- Product behavior cannot be changed accidentally by subordinate architecture,
  planning, tracker, handoff, or log artifacts.
- Local identity configuration is documented without tracking developer
  secrets.
- Deterministic validation can detect drift before merge.

Tradeoffs:

- Reference migration must be atomic; partial moves are blocking failures.
- Concurrent branches that still use legacy paths must rebase and reconcile
  against the canonical paths before merge.
- Maintainers must keep the registry, tracker index, and validators synchronized
  when canonical documentation changes.
- Explicit high-risk proof adds work before merge and push.

## Follow-Up

- Implement and run `scripts/validate-repository-governance.ps1`.
- Run `scripts/validate-ai-logging.ps1` and the exact repository test command.
- Record only fresh results as US-122 acceptance evidence and Harness proof.
- Rebase the governance branch, rerun validation, then merge and push when all
  gates pass.
