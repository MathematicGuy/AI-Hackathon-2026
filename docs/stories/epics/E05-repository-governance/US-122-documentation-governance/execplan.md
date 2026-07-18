# US-122 Exec Plan

## Goal

Establish and verify the repository's documentation authority, canonical
placement, mandatory agent read gate, safe local environment contract, and
atomic reference migration without changing product behavior.

## Scope

In scope:

- Enforce the root Markdown allowlist: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
  `README.md`, and `PROJECT_MANAGEMENT.md`.
- Register canonical documents and authority in `docs/README.md`.
- Move active trackers to `docs/team/now/`, index named owners separately from
  unresolved workstream aliases, and prohibit inferred identity mappings.
- Move the M1 PRD, product architecture, completed JTBD, and partner brief to
  their canonical destinations without translating their content.
- Add the mandatory agent read gate and its blocking conditions.
- Add a safe `.env.example` and preserve the ignored, untracked local `.env`.
- Update in-scope references atomically with every move.
- Implement `scripts/validate-repository-governance.ps1` and run
  `scripts/validate-ai-logging.ps1`.
- Validate, record Harness proof and trace, close the tracker and AI log, rebase
  the branch, and merge and push only after all gates pass.

Out of scope:

- Product code or behavior.
- Data tooling, business metrics, pilot behavior, or product observability
  implementation.
- CI/CD implementation.
- Translation of moved Vietnamese content.
- Moving flat Harness documents, the current product contract, existing
  canonical documents, or `docs/superpowers/` history.

## Risk Classification

Risk flags:

- Audit/security: instruction ordering, identity, redaction, and `.env`
  handling can expose or misattribute sensitive work.
- Existing behavior: changing canonical paths can break active references and
  concurrent branches.
- Weak proof: a plausible directory layout does not prove authority, ignore
  behavior, or stale-reference cleanup.
- Multi-domain: repository instructions, product documents, trackers, Harness
  state, local environment, and Git integration are involved.

Lane: high-risk.

Hard gates:

- Identity must be explicit and conflict-free, and the member log must be
  writable.
- Product work may not begin under `USER1` or `USER2` until a human explicitly
  maps the alias; unresolved aliases remain visibly unassigned and blocked.
- Owner, story, dependency, base, branch, worktree, and file boundary must
  agree across the request, tracker, Harness matrix, and checkout.
- Tracker and Harness state must agree; no dependency may be blocked.
- The worktree must not be shared concurrently.
- Story and file ownership must not be duplicated.
- Product authority conflicts must be resolved before mutation.
- Validation and proof requirements may not be missing, fabricated, or
  weakened.

The product-tracker gate has one narrow exception: explicitly authorized
repository-governance work may proceed without a product tracker when it is
registered as its own story. US-122 is that registered governance story.

## Work Phases

1. **Discovery**
   - Confirm member identity, branch, isolated worktree, story ownership, file
     boundary, base branch, and dependencies.
   - Read the canonical logging policy and create the session log.
   - Query the active Harness matrix without changing the controller's
     registered US-122 ownership or status.
   - Inventory root documents, canonical docs, tracker mappings, old-path
     references, `.gitignore`, `.env.example`, and validation scripts.
2. **Design**
   - Accept ADR 0011 with the authority hierarchy, root allowlist, canonical
     destinations, read order, governance exception, and rejected alternatives.
   - Keep ADR number 0010 reserved.
   - Confirm that the story changes repository governance only and does not
     supersede the accepted product contract.
3. **Validation planning**
   - Define deterministic checks for the root allowlist, canonical registry,
     tracker mappings, required read order, moved files, stale paths,
     environment hygiene, and logging-policy compatibility.
   - Preserve the Python command and the existing 53-passing-test result as a
     baseline only; require a fresh result for acceptance evidence.
4. **Implementation**
   - Create canonical destination directories and move the four product or
     reference artifacts and all active trackers.
   - Update every in-scope consumer in the same change as its document move.
   - Update repository instruction entrypoints, `docs/README.md`, tracker
     index, `.gitignore`, and the secret-free `.env.example`.
   - Add `scripts/validate-repository-governance.ps1`.
5. **Verification**
   - Run the governance validator and the AI logging validator.
   - Run the Python baseline exactly as specified.
   - Run `git diff --check`, stale-path scans, and `.env` ignore and tracking
     checks.
   - Review the diff for unintended translation, Harness-document moves,
     product-contract changes, or files outside the registered boundary.
6. **Harness and integration closeout**
   - Record only observed proof in the Harness trace and status.
   - Update the mapped tracker when applicable and finalize the AI session log.
   - Rebase the branch against the integration base, rerun all proof, and merge
     and push only when evidence is complete.

## Stop Conditions

Pause for human confirmation if:

- Identity is unresolved or conflicts with repository configuration.
- AI logging cannot be created or maintained.
- Product work is requested under an unmapped `USER1` or `USER2` alias, or a
  named owner lacks an applicable tracker.
- Owner, story, dependency, base, branch, worktree, or file-boundary metadata
  conflicts.
- Tracker and Harness state disagree, or a dependency is blocked.
- The worktree is shared concurrently.
- Story ownership or file ownership is duplicated.
- A product authority source conflicts with another authority source and no
  explicit Accepted ADR resolves it.
- Required validation or proof is absent, fails, would be weakened, or cannot
  be recorded truthfully.
- The requested work expands into product code, product behavior, Harness
  migration, CI/CD, translation, or another non-goal.
