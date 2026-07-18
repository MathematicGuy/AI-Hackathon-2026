# Documentation Authority Registry

This file is the canonical map for repository documentation. It defines where
documents belong, what each document controls, when agents must read it, and
how conflicts are resolved. Read it before selecting product or implementation
context.

## Root Markdown Allowlist

Only these Markdown entrypoints may live at the repository root:

| File | Purpose |
| --- | --- |
| [`AGENTS.md`](../AGENTS.md) | Canonical coding-agent behavior and read gate |
| [`CLAUDE.md`](../CLAUDE.md) | Claude discovery shim for `AGENTS.md` |
| [`GEMINI.md`](../GEMINI.md) | Gemini discovery shim for `AGENTS.md` |
| [`README.md`](../README.md) | Human-facing repository overview and navigation |
| [`PROJECT_MANAGEMENT.md`](../PROJECT_MANAGEMENT.md) | Milestone overview; not implementation authority |

All other Markdown belongs in a purpose folder under `docs/`, `ai-logs/`, or
the owning component directory.

## Authority Registry

| Canonical path | Purpose | Authority | Lifecycle | Owner | Read trigger |
| --- | --- | --- | --- | --- | --- |
| `AGENTS.md` and client shims | Agent behavior and mandatory context order | Controls agent behavior; shims may only route to it | Stable, updated through a governance story | Repository maintainers | Every agent session |
| `ai-logs/README.md` and `ai-logs/<member>/BOT_INSTRUCTIONS.md` | Identity, logging, redaction, and finalization | Controls AI session logging only | Stable policy plus append-only session records | Team and named member | Before planning, commands, tools, or edits |
| `docs/HARNESS.md`, `docs/FEATURE_INTAKE.md`, `docs/CONTEXT_RULES.md`, and other flat Harness policy files | Work classification, retrieval, proof, and process | Controls Harness workflow, not product behavior | Stable compatibility paths | Harness maintainers | Every repository change after logging and tracker checks |
| `docs/decisions/` | Accepted architectural and governance decisions | An Accepted ADR supersedes only the rules it names | Append decisions; supersede explicitly | Decision owner | When a relevant decision exists or a durable tradeoff changes |
| `docs/product/air-conditioner-advisor-m1-contract.md` | Product Advisor Contract — Milestone 1 (Air-Conditioner) | Primary product authority unless an Accepted ADR explicitly supersedes a named part | Stable compatibility path in this phase | Product contract owner | Before any advisor behavior change |
| `docs/product/requirements/` | Approved requirements and milestone baselines | Controls product scope within the contract and Accepted ADRs | Living, versioned with approved scope | Product owner | When planning or changing the affected product behavior |
| `docs/product/architecture/` | Product-specific system architecture | Subordinate to the product contract, Accepted ADRs, and requirements | Living architecture | Technical owner | Before design or implementation in the affected subsystem |
| `docs/product/discovery/` | JTBD and discovery context | Informative; does not override accepted product authority | Preserve and revise through discovery work | Product discovery owner | When validating customer need or requirement intent |
| `docs/references/partner-briefs/` | Partner-provided source material | Reference only unless adopted by an accepted artifact | Preserve source content and provenance | Product discovery owner | When an accepted artifact cites the source |
| `docs/stories/` | Bounded story scope, design, plan, and validation evidence | Controls the registered story boundary; cannot expand product authority | Planned through completed evidence | Story owner | Before work on the story |
| `docs/team/now/` | Parallel assignment, dependency, branch/worktree, and file coordination | Controls active workstream assignment; not product behavior or proof status | Active coordination records | Explicitly mapped team members | Before selecting or implementing product work |
| `PROJECT_MANAGEMENT.md` | Milestone dashboard and sequencing overview | Informative overview only | Living milestone summary | Integration controller | When coordinating milestones |
| `docs/templates/` | Reusable artifact structure | Guidance only | Stable templates | Harness maintainers | When creating the corresponding artifact |
| `docs/superpowers/` | Legacy design and plan provenance | Historical only; never current authority | Frozen legacy set | Repository maintainers | Only when tracing historical rationale |
| Component-local `README.md` and skill files, including `scripts/README.md` | Narrow usage instructions for the containing component | Subordinate to repository, product, story, and Harness authority | Living with the owning component | Component owner | Before changing or operating that component |
| `.env.example` | Safe local configuration variable contract | Defines names and non-secret defaults; does not load configuration | Living template with blank secrets | Repository maintainers | Before configuring local tools or providers |

No new files may be created under `docs/superpowers/`. Existing files there are
legacy provenance artifacts; create new plans in the applicable story packet
and new durable decisions in `docs/decisions/`.

## Mandatory Read Order

For every session:

1. Read the AI logging policy, resolve identity, read the member guide, and
   create the session log.
2. Classify the request as read-only or change work.
3. Read this authority registry.
4. Always read [`team/now/README.md`](team/now/README.md). For product work,
   require exactly one tracker mapped to the current identity and read it. A
   registered repository-governance story may use its documented exception
   without claiming a product tracker.
5. For changes, bootstrap Harness, record intake, and query the active matrix.
6. Apply the bounded retrieval rules in
   [`CONTEXT_RULES.md`](CONTEXT_RULES.md).
7. Read the applicable product contract and Accepted ADRs.
8. Read requirements, product architecture, the story packet, its
   implementation plan, and then only the relevant code.

Read-only tasks do not bootstrap or mutate Harness. Their only permitted
repository write is creation and finalization of the mandatory AI session log.

## Conflict Precedence

Resolve conflicts by domain:

1. The current human request controls task scope and repository mutation.
2. `AGENTS.md` controls agent behavior.
3. `ai-logs/README.md` controls logging identity, redaction, and finalization.
4. The accepted product contract controls product behavior unless an Accepted
   ADR explicitly names and supersedes a rule.
5. Requirements control product scope within the contract and Accepted ADRs.
6. Product architecture must conform to those product authorities.
7. A registered story controls its own bounded scope and acceptance evidence.
8. The Harness matrix controls registered status, dependency state, and proof.
9. The mapped tracker controls assignment, coordination, branch/worktree, and
   file boundaries.
10. `PROJECT_MANAGEMENT.md`, plans, handoffs, and session logs cannot override
    the authorities above.

Stop before implementation when identity, tracker ownership, story ID,
dependencies, branch/worktree, Harness matrix state, or file ownership is
missing, duplicated, blocked, or inconsistent. A governance story may change
the governance artifacts it explicitly owns but may not claim an unassigned
product tracker.

## Placement Rules

Place future documents by purpose:

- PRDs and requirement baselines: `docs/product/requirements/`.
- Product system designs: `docs/product/architecture/`.
- JTBD and discovery analysis: `docs/product/discovery/`.
- Partner source material: `docs/references/partner-briefs/`.
- Active parallel-work trackers: `docs/team/now/`.
- Story-specific design, execution, and validation: the registered story
  packet under `docs/stories/`.
- Cross-story durable decisions: `docs/decisions/`.
- AI interaction records: the resolved member directory under `ai-logs/`.
- Narrow component usage instructions: the owning component directory, using
  `README.md` or the component's established metadata convention.

Do not add another general-purpose Markdown file to the root. Keep existing
flat Harness policy files, Accepted ADR paths, story evidence, templates, and
the current product-contract path stable unless a separately approved
migration explicitly changes them.
