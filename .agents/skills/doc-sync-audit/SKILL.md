---
name: doc-sync-audit
description: Audits project documentation against actual source code implementation using the Doc Sweep Loop. Finds stale or missing content, plans incremental slices, updates docs in place with minimal targeted edits, and opens or prepares reviewable PRs/commits. Use when docs may be out of date, or when asked to "verify", "update", "sweep", or "sync" docs.
---

# Doc Sync Audit (Doc Sweep Loop)

This skill implements the **Doc Sweep Loop** workflow to systematically compare documentation against source code, identify drift, and apply targeted, incremental updates. It aims to keep documentation perfectly aligned with the codebase while producing small, reviewable changes.

---

## 🎯 Goal & Stopping Condition

- **Goal**: Keep the project's documentation accurate, complete, and in sync with codebase changes, surfacing updates incrementally as small, focused, reviewable git commits or pull requests.
- **Stopping Condition**: Every public API, CLI flag, config option, and system behavior is correctly documented, all examples compile/verify, all internal links resolve, and the documentation builds with zero errors/warnings.

---

## 📋 Project Config

Before beginning the loop, identify or ask the user for the relevant files:

```
DOC FILES TO AUDIT:
- <path/to/api_contract.md>
- <path/to/architecture.md>
- <path/to/agent_graph.md>
- <path/to/frontend_spec.md>

GROUND TRUTH SOURCE FILES:
- <path/to/api_routes>          # endpoints, request/response shapes
- <path/to/graph_definition>    # agent nodes, edges, routing
- ...
```

---

## 🔁 The Doc Sweep Loop Workflow

Run the audit in an iterative cycle (observe, plan, act, verify) using these five steps:

### Step 1 — Perceive (Gather Ground Truth & Diff)
Read all relevant source files **before** reading the documentation files. Extract the ground truth facts:
- **API Routes**: Endpoint paths, HTTP methods, request headers/bodies, response shapes.
- **Agent/Graph**: Nodes, edges, state transitions, routing logic.
- **State/Models**: Fields, types, DB schemas, table columns.
- **Frontend App**: View states, route paths, handler actions, API client methods.
- **Component Props**: Expected parameters, types, default values.

Write your extracted facts down as a list before proceeding. Do NOT rely on memory. Compare these facts against the current docs to see where they differ.

### Step 2 — Reason (Detect Drift)
Compare the extracted ground truth facts against each doc to identify discrepancies. Look for:
- **Missing Pages/Sections**: Newly added code that lacks documentation.
- **Stale Snippets**: Code examples, signatures, env vars, or configs that changed.
- **Count Drift**: Discrepancies in total endpoints, tables, or workflow steps.
- **Routing Typos**: Renamed graph nodes, incorrect next-step flows, or broken links.
- **Diagram Out-of-Sync**: Mermaid or text flow diagrams that do not reflect the current system architecture or workflow.

### Step 3 — Plan (Slice the Work)
Instead of batching all edits into one large, hard-to-review change:
1. List all detected drift.
2. Select the **smallest meaningful slice** (e.g., a single doc file, one API group, or a specific diagram) to update first.
3. If any change requires rewriting more than ~30% of a section, or if you cannot find a source line to justify it, halt and mark it **AMBIGUOUS** for user review.

### Step 4 — Act (Strict, Targeted Edits)
Apply edits to the selected slice following these rules:
- **Targeted Edits**: Change the absolute minimum text needed. Never rewrite correct sentences to "improve style."
- **Diagram Updates**: 
  - Change only the nodes, edges, or labels that are wrong.
  - When styling Mermaid diagrams, **always explicitly set a dark high-contrast color** (e.g., `color:#000000`) inside classDef definitions to prevent unreadable light text.
  - Synchronize dependent diagrams (e.g., if a workflow changes in `business_workflow.md` or `API_CONTRACT.md`, ensure the use case diagram reflects it).
- **Justification**: For every edit, verify you can answer: *"`<doc file>:<section>` changed because `<source file>:<line>` says `<fact>`"*. If you cannot, revert the change.

### Step 5 — Observe (Verify & Propose)
Verify the changes and package them for review:
1. Run syntax compiles or build checks (e.g., `python -m py_compile` or `npm run build`) to ensure no syntax errors were introduced if code was modified.
2. Verify that markdown renders correctly and links/diagrams are valid.
3. Propose the changes as a focused commit or git PR (e.g., `/create-pr` or `git commit`), highlighting what was updated.
4. Report status:
   - **CHANGED**: Incremental edits made (list doc, section, old -> new, and source reference).
   - **UNCHANGED**: Docs that were already accurate.
   - **AMBIGUOUS**: Sections you could not verify or that require design decisions from the user.
5. If drift remains, repeat the loop starting at Step 1 for the next slice.

---

## 🛑 Hard Stops (Do NOT Cross)

- **No Speculative Documentation**: Do NOT document speculative or "probable" behavior. If it is not in the ground truth code, do not write it unless explicitly told it is future scope.
- **No Deletions without Confirmation**: Do not delete existing documentation sections; mark them as AMBIGUOUS instead.
- **No Style Overhauls**: Do not rewrite paragraphs that are accurate but stylistically different from your preference.
- **Blocked Status**: If a critical ground truth file is missing or unreadable, stop the loop and report BLOCKED.

---

## 💡 Stale Patterns to Watch For

- **File Path Drift**: Code files renamed/moved, but docs still refer to the old path.
- **Bypass Patterns**: Workflow docs showing `A -> B -> C` but code added a direct bypass route.
- **Step Number Drift**: Adding a step in the middle of a sequence without updating subsequent step numbers.
