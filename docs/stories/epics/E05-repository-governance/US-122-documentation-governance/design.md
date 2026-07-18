# US-122 Design

## Domain Model

The documentation model has four concepts:

- **Authority source**: a document whose decisions control a defined domain.
- **Registry entry**: a canonical path, purpose, owner class, and authority
  description recorded in `docs/README.md`.
- **Read gate**: the ordered context and consistency checks required before
  work begins.
- **Reference migration**: an atomic document move plus updates to every
  in-scope reference that would otherwise become stale.

Conflicts are resolved by domain, not by whichever file was edited most
recently:

1. The user controls repository mutation and task scope.
2. The applicable `AGENTS.md` controls agent behavior; root client shims route
   to it and may not redefine the canonical workflows.
3. `ai-logs/README.md` controls AI session logging, identity, redaction, and
   log finalization.
4. The accepted product contract controls product behavior unless an Accepted
   ADR explicitly supersedes a named part of it.
5. The PRD is the product baseline within the accepted contract and explicit
   ADR constraints.
6. Product architecture is subordinate to the product contract and PRD.
7. A story packet bounds the registered story's scope and acceptance criteria.
8. The Harness matrix controls registered status, dependency state, and proof.
9. The mapped team tracker controls assignment, dependency coordination,
   worktree, branch, and file boundaries for product work.
10. `PROJECT_MANAGEMENT.md` is a milestone overview only.
11. Plans describe execution but cannot expand approved scope or authority.
12. Handoffs and AI session logs are non-authoritative transition and audit
    records.

## Application Flow

Before substantive work, an agent follows this order:

1. Read the client shim and the applicable root `AGENTS.md`.
2. Read `ai-logs/README.md`, resolve identity, read the member guide and
   `ai-logs/SESSION_TEMPLATE.md`, and create the member session log.
3. Classify the request as read-only or a repository change.
4. Read the canonical registry in `docs/README.md`.
5. Read the index under `docs/team/now/`. For product work, require and read
   the explicitly mapped tracker; for a registered repository-governance
   story, verify its documented product-tracker exception.
6. For a change, run Harness bootstrap, record intake, and query the active
   matrix.
7. Apply `docs/CONTEXT_RULES.md` and retrieve only bounded lane- and
   task-specific context.
8. Read `docs/product/air-conditioner-advisor-m1-contract.md` and any Accepted
   ADR that explicitly supersedes it.
9. Read the canonical PRD.
10. Read the canonical product architecture.
11. Read the story packet.
12. Read the registered story's implementation plan; for product work,
    confirm that the mapped tracker links to it.
13. Read the exact files to change and their callers or consumers.
14. Pass the ready gate before mutation.
15. After implementation, record proof, status, trace, tracker updates, and AI
    log closeout.

Read-only requests stop after the bounded context needed to answer and do not
bootstrap or mutate Harness. Explicitly authorized repository-governance work
may omit a product tracker only when it is registered as its own story; US-122
uses that exception.

The ready gate blocks mutation when any of these conditions exists:

- Identity is unresolved or conflicting, or the required log cannot be
  created or updated.
- `USER1` or `USER2` is unmapped, or product work has no mapped product
  tracker.
- Owner, story, dependency, base branch, worktree, branch, or file boundary
  disagrees across the tracker, Harness matrix, task, and local checkout.
- The tracker and Harness matrix disagree, or a dependency is blocked.
- A worktree is shared concurrently.
- Story ownership or file ownership is duplicated.
- Product authority conflicts are unresolved.
- Required validation or proof is missing or would be weakened.

## Interface Contract

`docs/README.md` is the canonical registry interface. It must expose the root
allowlist, the authority hierarchy, canonical document paths, the required
read order, and links to tracker and product-document indexes.

The placement interface is:

| Source or class | Destination |
| --- | --- |
| `USER1-NOW.md`, `USER2-NOW.md`, `THANH-NOW.md`, and future active trackers | `docs/team/now/` |
| `WORKFLOW-MVP(4).md` | `docs/product/requirements/air-conditioner-advisor-m1-prd.md` |
| `ARCHITECTURE.md` when it describes the product | `docs/product/architecture/air-conditioner-advisor-m1.md` |
| `JTBD_Completed.md` | `docs/product/discovery/air-conditioner-advisor-jtbd.md` |
| Existing partner brief | `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md` |

The local environment interface is:

- `.env.example` is tracked, contains names and safe placeholders only, and
  documents `TEAM_MEMBER` without credentials.
- `.env` remains local, ignored, and untracked.
- Instructions and validators inspect only the `TEAM_MEMBER` assignment when
  resolving identity and never print unrelated environment values.

The validation interface is
`scripts/validate-repository-governance.ps1`, with
`scripts/validate-ai-logging.ps1` as a required companion check.

## Data Model

No application database or Harness schema migration is part of this story.
Existing Harness documents and the current product contract remain in place.

Document moves preserve content and history where Git can detect it. Each move
and its in-scope reference updates form one atomic migration so the branch
never intentionally establishes a new canonical path while leaving active
consumers on the old path. The final branch is rebased against its integration
base before merge so concurrent documentation edits are reconciled against the
new paths.

## UI / Platform Impact

There is no product UI, API, runtime, deployment, or platform-shell behavior
change. Repository-aware clients gain a deterministic documentation and local
environment gate. Validation must run on the repository's Windows PowerShell
path, and the Python baseline remains platform-independent through `uv`.

## Observability

This story does not implement product observability. Its audit evidence is the
governance validator output, AI logging validator output, repository test
result, whitespace and stale-reference scans, environment-ignore checks,
Harness proof and trace records, tracker closeout, and the finalized AI session
log. Evidence is recorded only after commands actually run.

## Alternatives Considered

1. Leave the working documents at the repository root and add explanatory
   links. Rejected because placement remains ambiguous, stale references remain
   easy to create, and the root allowlist cannot be enforced.
2. Move all flat Harness documents and lifecycle records into a new hierarchy.
   Rejected because it expands US-122 into a Harness migration, increases
   authority risk, and is unrelated to the requested product-document cleanup.
3. Adopt the bounded registry, root allowlist, authority hierarchy, and atomic
   reference migration described above. Accepted because it resolves the
   ambiguity without changing product behavior or Harness storage.
