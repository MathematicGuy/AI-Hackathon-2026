# Parallel Critical-Path Ledgers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create two teammate-specific work ledgers and reduce `THANH-NOW.md` to controller-level delegated ownership so three developers can implement M1 foundations concurrently.

**Architecture:** Each teammate receives an isolated sequential story chain on a dedicated branch/worktree. The root NOW files are coordination boundaries: teammates update only their own ledger, while Thành serializes reviewed merges and updates the controller ledger.

**Tech Stack:** Markdown coordination documents, Git branches/worktrees, Harness story/trace workflow, pytest verification commands.

## Global Constraints

- Thành retains US-107 → US-108 → US-109 → US-110 and M1.5 integration ownership.
- USER1 owns US-102 → US-103 on `agent/user1-m1-3-guardrails-intent`.
- USER2 owns US-104 → US-105 on `agent/user2-m1-4-state-routing`; US-105 remains blocked until US-103 and US-104 are merged.
- Concurrent implementation in one working tree is prohibited.
- Each teammate updates only their own NOW file; Thành updates `THANH-NOW.md` after reviewed merges.
- Activate one Harness story at a time per isolated worktree and preserve RED → GREEN, separate review, proof, and trace gates.
- Context investigation requests `gpt-5.6-luna-high`; code implementation requests `gpt-5.6-terra-high`. Do not claim enforcement when the API lacks model selection.
- Use `deepseek/deepseek-v4-flash` through OpenRouter for grounded explanations; never GPT-5.4 Mini.
- Ignore `resources/` and preserve unrelated dirty work.
- Do not create `PROGRESS.md` or `.superpowers/sdd/progress.md`.

---

### Task 1: Create teammate work ledgers

**Files:**
- Create: `USER1-NOW.md`
- Create: `USER2-NOW.md`

**Interfaces:**
- Consumes: approved ownership and merge protocol from `docs/superpowers/specs/2026-07-17-parallel-critical-path-workstreams-design.md`.
- Produces: self-contained execution briefs that link to the detailed M1 plan rather than duplicating its implementation code.

- [ ] **Step 1: Create `USER1-NOW.md`** with these exact sections:
  - `Current mission`: deliver M1.3 guardrails and Vietnamese intent/need extraction.
  - `Ownership`: US-102 followed by US-103; no later story is implied.
  - `Start point`: branch from local `main` containing merge `9dc9363`; create/use `agent/user1-m1-3-guardrails-intent` in an isolated worktree or clone.
  - `Execution board`: US-102 ready from US-121, US-103 blocked on US-102.
  - `File boundary`: Task 6 and Task 7 files only; no decision-engine, state, contract, or other NOW-file edits.
  - `Verification`: exact focused pytest commands from Tasks 6 and 7, plus contract tests for US-103.
  - `Merge handoff`: reviewed US-102 first, refresh from main, then reviewed US-103; notify controller when each commit is ready.
  - `Frozen constraints`: guardrail order, 150-word block threshold, Nano intent ownership, null-preserving extraction, synthetic fixture policy, model-label limitation, and ignored `resources/`.

- [ ] **Step 2: Create `USER2-NOW.md`** with these exact sections:
  - `Current mission`: deliver M1.4 state merge followed by clarification/routing/persistence.
  - `Ownership`: US-104 followed by US-105; no later story is implied.
  - `Start point`: branch from local `main` containing merge `9dc9363`; create/use `agent/user2-m1-4-state-routing` in an isolated worktree or clone.
  - `Execution board`: US-104 ready from US-121, US-105 blocked until both US-103 and US-104 are on main.
  - `File boundary`: Task 8 and Task 9 files only; no guardrail, intent, decision-engine, contract, or other NOW-file edits.
  - `Verification`: exact focused pytest commands from Tasks 8 and 9 plus contract tests for US-104.
  - `Merge handoff`: reviewed US-104 first; after US-103 merges, refresh from main before US-105; notify controller for serialized integration.
  - `Frozen constraints`: explicit correction precedence, omitted-value preservation, no implicit deletion, one clarification question, maximum three-question cycle, same-session isolation, model-label limitation, and ignored `resources/`.

- [ ] **Step 3: Validate both ledgers**

Run:

```powershell
rtk grep "US-102|US-103|agent/user1-m1-3-guardrails-intent|USER1-NOW.md" USER1-NOW.md
rtk grep "US-104|US-105|agent/user2-m1-4-state-routing|USER2-NOW.md" USER2-NOW.md
```

Expected: both commands find the assigned stories, branch, and own-ledger rule; neither file contains another teammate's implementation ownership.

---

### Task 2: Update the controller ledger and verify coordination consistency

**Files:**
- Modify: `THANH-NOW.md`
- Test: `USER1-NOW.md`
- Test: `USER2-NOW.md`

**Interfaces:**
- Consumes: teammate ownership from Task 1.
- Produces: one controller board that delegates details by link and retains integration truth.

- [ ] **Step 1: Replace delegated implementation roles in `THANH-NOW.md`**
  - Keep completed US-121 and US-106 rows unchanged.
  - Keep Thành as owner for US-107 → US-110 and M1.5 onward.
  - Mark US-102 and US-103 as delegated to USER1 with `USER1-NOW.md` as the detail source.
  - Mark US-104 and US-105 as delegated to USER2 with `USER2-NOW.md` as the detail source; retain the US-105 dependency on US-103 and US-104.
  - Add a parallel-workstream section naming both branches and stating that merges are serialized by Thành.
  - Do not copy the teammates' detailed file lists or commands into `THANH-NOW.md`.

- [ ] **Step 2: Run documentation checks**

Run:

```powershell
rtk grep "USER1-NOW.md|USER2-NOW.md|agent/user1-m1-3-guardrails-intent|agent/user2-m1-4-state-routing" THANH-NOW.md USER1-NOW.md USER2-NOW.md
rtk git diff --check -- THANH-NOW.md USER1-NOW.md USER2-NOW.md
```

Expected: all ownership/branch references exist and the scoped whitespace check exits 0.

- [ ] **Step 3: Confirm scope**

Run:

```powershell
rtk git status --short -- THANH-NOW.md USER1-NOW.md USER2-NOW.md
```

Expected: only the controller ledger is modified and the two teammate ledgers are new within this task's implementation scope.

- [ ] **Step 4: Commit the coordination ledgers**

```powershell
rtk git add THANH-NOW.md USER1-NOW.md USER2-NOW.md
rtk git commit -m "docs: delegate M1 foundation workstreams"
```
