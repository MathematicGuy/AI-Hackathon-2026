# US-122 Validation

## Proof Strategy

Use deterministic repository checks and record fresh results only after the
final reference migration is complete. The governance validator is the primary
proof for placement, authority, read-gate literals, tracker mappings, stale
paths, and local environment hygiene. The AI logging validator independently
proves that governance changes preserve canonical logging behavior. The Python
suite protects existing repository behavior.

The previously observed `53 passed` Python result is a pre-change baseline, not
acceptance evidence. Merge and push remain blocked until every required command
has run on the final rebased branch and its actual result is recorded.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Root Markdown allowlist; required registry entries; exact authority order; mandatory read-order literals; safe `.env.example` keys and placeholder values. |
| Integration | Every active tracker is indexed under `docs/team/now/`; `USER1` and `USER2` remain explicitly unassigned aliases until a human maps them; moved documents and all active consumers use the same canonical paths. |
| E2E | A change request follows logging, classification, registry, tracker, Harness, bounded context, authority, story, ready-gate, proof, trace, tracker, and log closeout in order. |
| Platform | `scripts/validate-repository-governance.ps1` and `scripts/validate-ai-logging.ps1` pass under Windows PowerShell; the Python suite passes through `uv`. |
| Performance | Not applicable; the story changes repository documentation and bounded validation only. |
| Logs/Audit | `.env` is ignored and untracked; `.env.example` is tracked and secret-free; Harness proof and trace, tracker state, and the AI session log report only observed results. |

## Fixtures

- Root Markdown allowlist: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`,
  and `PROJECT_MANAGEMENT.md`.
- Tracker directory and index: `docs/team/now/`.
- Canonical PRD:
  `docs/product/requirements/air-conditioner-advisor-m1-prd.md`.
- Canonical product architecture:
  `docs/product/architecture/air-conditioner-advisor-m1.md`.
- Canonical JTBD:
  `docs/product/discovery/air-conditioner-advisor-jtbd.md`.
- Canonical partner brief:
  `docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md`.
- Canonical product contract:
  `docs/product/air-conditioner-advisor-m1-contract.md`.
- Local environment pair: tracked `.env.example` and ignored, untracked
  `.env`.

## Commands

Run from the repository root after implementation and again after the final
rebase:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-repository-governance.ps1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-ai-logging.ps1

uv run --no-project --isolated --python 3.12 --with-editable ".[test]" --no-env-file python -m pytest -q

git diff --check

git diff --cached --check
```

The governance validator must include and report:

- A root Markdown allowlist check.
- Canonical-path existence and legacy-path absence checks.
- Stale-path scans across active repository consumers, with only the
  intentional migration record and validator fixtures excluded.
- Registry, tracker-index, authority-order, and mandatory-read-gate checks.
- Exact frozen contents and provenance markers for legacy `docs/superpowers/`.
- `git check-ignore` proof that local `.env` is ignored.
- `git ls-files` proof that `.env` is untracked and `.env.example` is tracked.
- Exact checks that credential placeholders are blank and safe non-secret
  defaults match the approved environment contract.

Closeout also requires Harness proof and a high-risk trace linked to US-122,
the documented governance-story tracker exception, and finalization of the
member's sanitized AI session log.

## Acceptance Evidence

Accepted for integration on 2026-07-17 from the reviewed staged tree based on
`69685c68c26ac1c4e0d7ad3ec808237cb8b16234`.

- `scripts/validate-repository-governance.ps1` exited `0`. Its nested AI
  logging check passed for five members and five client entrypoints, and its
  repository checks confirmed the root allowlist, authority/read order,
  structured tracker identities, unique story/file ownership, active
  reference migration, legacy-provenance boundary, Markdown links, and local
  environment safety.
- `scripts/validate-ai-logging.ps1` independently exited `0` for five members
  and five client entrypoints.
- The exact isolated Python 3.12 command above completed with `53 passed in
  0.11s`.
- `git diff --check` and `git diff --cached --check` exited `0`; the final
  candidate had no unstaged or untracked repository changes.
- The active-consumer stale-path scan found no unintended legacy paths across
  Markdown, scripts, code, configuration, data, or text files. The only
  intentional old-path literals are migration records and validator fixtures.
- The repository root contains exactly the five allowed Markdown files.
  Ordinary Windows `Resolve-Path` and `Get-Content` opened all four files in
  the shortened US-122 story directory.
- Git confirmed that local `.env` is ignored and untracked and that
  `.env.example` is tracked. The template contains the exact approved keys,
  blank credential placeholders, and approved non-secret defaults.
- Independent review reported no remaining Critical or Important findings
  after the instruction-order, tracker-provenance, validator-strength, Windows
  path-length, and governance-plan consistency fixes.
- Harness trace `#1` achieved the required detailed tier (`3/3`) for the
  high-risk lane. `US-122` completed as `implemented` with unit, integration,
  E2E, and platform proof all `yes`.
- A final fetch confirmed that `HEAD`, `origin/main`, and the merge base were
  all `69685c68c26ac1c4e0d7ad3ec808237cb8b16234` with divergence `0/0`, so no
  rebase was required before the feature commit.

These observations authorize integration. Commit hashes, the fast-forward
merge, push, and final remote divergence are recorded in the member session
log closeout only after those operations actually occur.
