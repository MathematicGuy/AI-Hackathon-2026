# Handoff — Milestone 1.2: Hard Constraints → Ranking → Deduplication

**Owner tracker:** `docs/team/now/THANH-NOW.md` (Đinh Nhật Thành)
**Branch:** `agent/m1-implementation` (already checked out; stay on it)
**Builds on:** US-107 product normalization + evidence (done this session, `implemented` in the Harness matrix)
**Epic:** `docs/stories/epics/E01-air-conditioner-advisor-m1/`

---

## Governance preflight (do this FIRST in the new session — no shortcuts)

The handoff does not bypass the AGENTS.md gates. Before any product edit:

1. **Session logging** — read `ai-logs/README.md`, resolve `TEAM_MEMBER` from
   `.env` (read only that key; never read/expose other `.env` values, never
   infer identity from Git config / OS user / machine / branch / task), read
   that member's `BOT_INSTRUCTIONS.md`, create the session log.
2. **Read gate** — read `docs/README.md`, then `docs/team/now/README.md`, then
   confirm the identity maps to exactly one tracker and read `THANH-NOW.md`.
3. **Harness (change lane)** — run `.\scripts\bootstrap-harness.ps1`, classify
   the request via `docs/FEATURE_INTAKE.md`, query
   `.\scripts\bin\harness-cli.exe query matrix --active --summary`, and pull
   only the lane/task context named in `docs/CONTEXT_RULES.md`.
4. **Bounded context order:** context rules → accepted contract (+ any
   superseding Accepted ADR) → PRD → product architecture → story packet +
   execplan → code.

Each story below needs its **own registered story packet reviewed before
implementation** (same gate US-107 had). US-108 has no packet yet — create it
first, mirroring the US-107 packet layout (`overview.md`, `design.md`,
`execplan.md`, `validation.md`).

---

## Scope — three stories, in dependency order

### US-108 — Hard constraint filter (do first; unblocks the rest)
Deterministic filter over the normalized catalog. Splits products into
eligible vs excluded, producing the **frozen** `FilterResult` /
`ExcludedProduct` shapes already defined in
`backend/app/contracts/schemas.py` (do NOT redefine them — implement against
them, exactly as US-107 implemented against `NormalizedAirConditioner`).

- **Input:** `list[NormalizedProduct]` from
  `backend.app.domain.air_conditioner.normalization.normalize_catalog`
  (each carries `product`, `evidence`, `missing_fields`).
- **Output:** `FilterResult` (eligible products + `ExcludedProduct` entries).
- **Truthfulness:** every exclusion must cite a reason grounded in the
  normalized field + its `EvidenceRef`; never exclude on a guessed value.
  A `null` field (in `missing_fields`) is unknown, not a violation — decide
  in the packet whether unknown-on-a-hard-constraint excludes or passes, and
  record that decision in `design.md` with the PRD citation.
- **Authority:** PRD hard-constraint section (the pipeline step
  `product_normalization → hard_constraint_filter → availability_decision`
  in the accepted contract). Read it before coding — do not assume the
  constraint list.

### US-109 — Injected deterministic ranking (depends on US-108)
Rank the eligible set into the three golden roles. **Production ranking policy
stays injected** (dependency-injected, not hardcoded) per the tracker — the
node consumes a policy, it does not embed weights inline.

- **Fixture / oracle:** `data/aircon-m1-test-data/aircon-m1-ranking-fixture.json`
  — keys: `version`, `purpose`, `eligibility`, `best_overall_weights`,
  `best_value_formula`, `cheapest_qualified`, `normalization_ranges`,
  `tie_breakers`. Drive the injected policy from this fixture; assert against it.
- **Golden regression AIRCON-M1-001** must resolve to:
  Best Overall → `AC-M1-002`, Best Value → `AC-M1-003`,
  Cheapest Qualified → `AC-M1-006`. This is the pass/fail gate for US-109.
- Respect `tie_breakers` and `normalization_ranges` deterministically — no
  floating-point nondeterminism, stable sort with explicit tie-break keys.

### US-110 — Truthful deduplication (depends on US-109)
Collapse the ranked roles for the UI without lying about coverage. Per the
accepted contract: **a product that wins multiple roles keeps all its roles
and renders once with merged badges** — it is not dropped, and a role is never
silently reassigned to a different product to avoid a repeat.

- Verify against the contract's dedup/badge wording before implementing.
- The three golden role winners above are distinct products, so the golden
  case does not exercise the merge path — add a targeted unit case (synthetic
  ranked input where one product wins two roles) to prove merge-not-drop.

---

## Definition of Done (per story)

- Story packet created and **separately reviewed** before implementation
  (fresh implementation subagent, then a separate reviewer — the project's
  delegation model).
- TDD RED → GREEN: failing unit test committed first, then implementation.
- Implements against the **frozen** `schemas.py` contract models; no schema
  edits (schemas.py is frozen for M1).
- Golden regression **AIRCON-M1-001** still produces
  `AC-M1-002 / AC-M1-003 / AC-M1-006` (US-109 onward).
- Full backend suite green (currently **166 tests**; each story adds to it).
- Harness closed: `story verify` → record Trace (standard tier: include
  `--read` and `--friction` so it clears the normal-lane requirement, as
  US-107 did) → `harness-cli audit` (expect entropy 0/100 once traced+closed)
  → `harness-cli propose` (report its output even when it is "No proposals
  generated" — an intentional no-op, not a failure).
- Session log finalized (Final Outcome, Validation, Files Touched, Redaction).

---

## Tech constraints & gotchas (carried from this session)

- **pytest under RTK needs explicit PYTHONPATH** — the RTK wrapper does not add
  the repo root to `sys.path` the way `python -m` does. Run:
  ```
  PYTHONPATH="E:/VIN-INTERNSHIP/AI-Hackathon-2026" python -m pytest backend/tests/... -p no:cacheprovider
  ```
  (`harness-cli story verify` runs a raw subprocess and does NOT need this.)
- **Windows cp1252 console** cannot print the Vietnamese catalog. Don't `print`
  Unicode to the console — dump `json.dumps(..., ensure_ascii=True)` to the
  scratchpad and Read the file instead.
- **Frozen evaluation contract:** only use `data/aircon-m1-test-data/`. Do not
  regenerate, edit, or add catalog/fixture data.
- **Ignore `resources/`** unless explicitly asked.
- **Contracts:** `backend/app/contracts/schemas.py` — `ContractModel` uses
  pydantic v2 `extra="forbid"`. `NormalizedAirConditioner`, `EvidenceRef`,
  `ExcludedProduct`, `FilterResult`, `StockStatus` all live here and are frozen.
- **Trace tiers:** outcome must be `completed|blocked|partial|failed` (not
  "success"); a bare trace lands below-requirement — add `--read`/`--friction`
  to reach standard tier for a normal lane.
- **M1 grounded explanations** use `deepseek/deepseek-v4-flash` via OpenRouter,
  never GPT-5.4 Mini (not needed for 1.2 deterministic nodes, but noted).
- **Progress tracking** goes only in `docs/team/now/THANH-NOW.md`. Do not create
  root `*-NOW.md`, `PROGRESS.md`, or a separate SDD progress ledger.
- **No commit/push** unless the user explicitly asks.

---

## Key files to open first (US-108)

- `backend/app/contracts/schemas.py` — `FilterResult`, `ExcludedProduct`, `StockStatus`.
- `backend/app/domain/air_conditioner/normalization.py` — US-108 input source.
- `backend/app/domain/air_conditioner/evidence.py` — `NormalizedProduct` shape.
- `backend/tests/unit/domain/air_conditioner/test_normalization.py` — test style to mirror.
- `data/aircon-m1-test-data/aircon-m1-catalog-enriched.json` — 14 records + golden fixtures.
- The accepted product contract + PRD (via the bounded-context read order above).
