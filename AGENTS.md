# AGENTS.md

<!-- AI-LOGGING:BEGIN -->
## Mandatory AI Session Logging

Before substantive work:

1. Read `ai-logs/README.md`.
2. Resolve the current team member exactly as required by that policy. A valid
   `TEAM_MEMBER` value may identify the member; otherwise ask the canonical
   identity question.
3. Read that member's `BOT_INSTRUCTIONS.md`.
4. Create or update the session log only when a durable deliverable is produced,
   the task is complete, or a major bug/blocker is reached; finalize it before
   ending the session when one exists.

Never infer identity from a tracker alias, Git configuration, operating-system
username, earlier session, branch name, or task content.
<!-- AI-LOGGING:END -->

<!-- REPOSITORY-GOVERNANCE:BEGIN -->
## Mandatory Repository Read Gate

After logging preflight and before selecting implementation context:

1. Classify the request as read-only or change work.
2. Read `docs/README.md`, the canonical documentation authority registry.
3. Read `docs/team/now/README.md`.
4. For product work, confirm that the current identity is explicitly mapped to
   exactly one tracker, then read that tracker.
5. Stop before implementation if identity, tracker ownership, story ID,
   dependencies, branch/worktree, Harness matrix state, or file ownership is
   missing, duplicated, blocked, or inconsistent.

`USER1` and `USER2` are aliases, not identities. They remain unassigned until
a human updates the tracker index explicitly. Do not infer or claim either
alias.

Repository-governance work may update the read gate and tracker index through
its own registered story without claiming a product tracker. It may not
implement an unassigned product workstream.
<!-- REPOSITORY-GOVERNANCE:END -->

<!-- HARNESS:BEGIN -->
## Harness

Apply this gate only after the logging and repository read gates above.

- For a read-only answer, explanation, review, diagnosis, plan, or status
  request, inspect only the material needed to respond. Do not bootstrap,
  initialize or migrate a database, record intake, or record a trace. A session
  log may be created or finalized only at a durable milestone or major
  bug/blocker.
- For an explicit change, build, fix, or repository-artifact request, first run
  `scripts/bootstrap-harness.sh` on macOS/Linux or
  `.\scripts\bootstrap-harness.ps1` on Windows. Then use
  `docs/FEATURE_INTAKE.md` to classify and record the request, query
  `scripts/bin/harness-cli query matrix --active --summary` on macOS/Linux or
  `.\scripts\bin\harness-cli.exe query matrix --active --summary` on Windows,
  and retrieve only the lane- and task-specific context described in
  `docs/CONTEXT_RULES.md`.
<!-- HARNESS:END -->

<!-- BOUNDED-CONTEXT:BEGIN -->
## Mandatory Bounded Implementation Context

After the Harness gate for a change, read context in this order:

1. Applicable bounded-context rules.
2. The accepted product contract and any Accepted ADR that explicitly
   supersedes part of it.
3. The applicable PRD.
4. Product architecture.
5. The registered story packet and implementation plan.
6. Only then, the relevant code.
<!-- BOUNDED-CONTEXT:END -->

Drop-in operating instructions for coding agents. Read this file before every task.

**Working code only. Finish the job. Plausibility is not correctness.**

This file follows the [AGENTS.md](https://agents.md) open standard (Linux Foundation / Agentic AI Foundation). Claude Code, Codex, Cursor, Windsurf, Copilot, Aider, Devin, Amp read it natively. For tools that look elsewhere, symlink:

```bash
ln -s AGENTS.md CLAUDE.md
```

---

## 0. Non-negotiables

These rules override everything else in this file when in conflict:

1. **No flattery, no filler.** Skip openers like "Great question", "You're absolutely right", "Excellent idea", "I'd be happy to". Start with the answer or the action.
2. **Disagree when you disagree.** If the user's premise is wrong, say so before doing the work. Agreeing with false premises to be polite is the single worst failure mode in coding agents.
3. **Never fabricate.** Not file paths, not commit hashes, not API names, not test results, not library functions. If you don't know, read the file, run the command, or say "I don't know, let me check."
4. **Stop when confused.** If the task has two plausible interpretations, ask. Do not pick silently and proceed.
5. **Touch only what you must.** Every changed line must trace directly to the user's request. No drive-by refactors, reformatting, or "while I was in there" cleanups.

---

## 1. Before writing code

**Goal: understand the problem and the codebase before producing a diff.**

- State your plan in one or two sentences before editing. For anything non-trivial, produce a numbered list of steps with a verification check for each.
- Read the files you will touch. Read the files that call the files you will touch. Claude Code: use subagents for exploration so the main context stays clean.
- Match existing patterns in the codebase. If the project uses pattern X, use pattern X, even if you'd do it differently in a greenfield repo.
- Surface assumptions out loud: "I'm assuming you want X, Y, Z. If that's wrong, say so." Do not bury assumptions inside the implementation.
- If two approaches exist, present both with tradeoffs. Do not pick one silently. Exception: trivial tasks (typo, rename, log line) where the diff fits in one sentence.

---

## 2. Writing code: simplicity first

**Goal: the minimum code that solves the stated problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code. No configurability, flexibility, or hooks that were not requested.
- No error handling for impossible scenarios. Handle the failures that can actually happen.
- If the solution runs 200 lines and could be 50, rewrite it before showing it.
- If you find yourself adding "for future extensibility", stop. Future extensibility is a future decision.
- Bias toward deleting code over adding code. Shipping less is almost always better.

The test: would a senior engineer reading the diff call this overcomplicated? If yes, simplify.

---

## 3. Surgical changes

**Goal: clean, reviewable diffs. Change only what the request requires.**

- Do not "improve" adjacent code, comments, formatting, or imports that are not part of the task.
- Do not refactor code that works just because you are in the file.
- Do not delete pre-existing dead code unless asked. If you notice it, mention it in the summary.
- Do clean up orphans created by your own changes (unused imports, variables, functions your edit made obsolete).
- Match the project's existing style exactly: indentation, quotes, naming, file layout.

The test: every changed line traces directly to the user's request. If a line fails that test, revert it.

---

## 4. Goal-driven execution

**Goal: define success as something you can verify, then loop until verified.**

Rewrite vague asks into verifiable goals before starting:

- "Add validation" becomes "Write tests for invalid inputs (empty, malformed, oversized), then make them pass."
- "Fix the bug" becomes "Write a failing test that reproduces the reported symptom, then make it pass."
- "Refactor X" becomes "Ensure the existing test suite passes before and after, and no public API changes."
- "Make it faster" becomes "Benchmark the current hot path, identify the bottleneck with profiling, change it, show the benchmark is faster."

For every task:

1. State the success criteria before writing code.
2. Write the verification (test, script, benchmark, screenshot diff) where practical.
3. Run the verification. Read the output. Do not claim success without checking.
4. If the verification fails, fix the cause, not the test.

---

## 5. Tool use and verification

- Prefer running the code to guessing about the code. If a test suite exists, run it. If a linter exists, run it. If a type checker exists, run it.
- Never report "done" based on a plausible-looking diff alone. Plausibility is not correctness.
- When debugging, address root causes, not symptoms. Suppressing the error is not fixing the error.
- For UI changes, verify visually: screenshot before, screenshot after, describe the diff.
- Use CLI tools (gh, aws, gcloud, kubectl) when they exist. They are more context-efficient than reading docs or hitting APIs unauthenticated.
- When reading logs, errors, or stack traces, read the whole thing. Half-read traces produce wrong fixes.

---

## 6. Session hygiene

- Context is the constraint. Long sessions with accumulated failed attempts perform worse than fresh sessions with a better prompt.
- After two failed corrections on the same issue, stop. Summarize what you learned and ask the user to reset the session with a sharper prompt.
- Use subagents (Claude Code: "use subagents to investigate X") for exploration tasks that would otherwise pollute the main context with dozens of file reads.
- When committing, write descriptive commit messages (subject under 72 chars, body explains the why). No "update file" or "fix bug" commits. No "Co-Authored-By: Claude" attribution unless the project explicitly wants it.

---

## 7. Communication style

- Direct, not diplomatic. "This won't scale because X" beats "That's an interesting approach, but have you considered...".
- Concise by default. Two or three short paragraphs unless the user asks for depth. No padding, no restating the question, no ceremonial closings.
- When a question has a clear answer, give it. When it does not, say so and give your best read on the tradeoffs.
- Celebrate only what matters: shipping, solving genuinely hard problems, metrics that moved. Not feature ideas, not scope creep, not "wouldn't it be cool if".
- No excessive bullet points, no unprompted headers, no emoji. Prose is usually clearer than structure for short answers.

---

## 8. When to ask, when to proceed

**Ask before proceeding when:**
- The request has two plausible interpretations and the choice materially affects the output.
- The change touches something you've been told is load-bearing, versioned, or has a migration path.
- You need a credential, a secret, or a production resource you don't have access to.
- The user's stated goal and the literal request appear to conflict.

**Proceed without asking when:**
- The task is trivial and reversible (typo, rename a local variable, add a log line).
- The ambiguity can be resolved by reading the code or running a command.
- The user has already answered the question once in this session.

---

## 9. Self-improvement loop

**This file is living. Keep it short by keeping it honest.**

After every session where the agent did something wrong:

1. Ask: was the mistake because this file lacks a rule, or because the agent ignored a rule?
2. If lacking: add the rule under "Project Learnings" below, written as concretely as possible ("Always use X for Y" not "be careful with Y").
3. If ignored: the rule may be too long, too vague, or buried. Tighten it or move it up.
4. Every few weeks, prune. For each line, ask: "Would removing this cause the agent to make a mistake?" If no, delete. Bloated AGENTS.md files get ignored wholesale.

Boris Cherny (creator of Claude Code) keeps his team's file around 100 lines. Under 300 is a good ceiling. Over 500 and you are fighting your own config.

---

## 10. Project context

**Fill this in per project. Keep it specific. Delete sections that don't apply.**


### Stack
- Language and version:
- Framework(s):
- Package manager:
- Runtime / deployment target:

### Commands
- Install: `TODO`
- Build: `TODO`
- Test (all): `TODO`
- Test (single file): `TODO`
- Lint: `TODO`
- Typecheck: `TODO`
- Run locally: `TODO`

Prefer single-file or single-test runs during iteration. Full suites are for the final verification pass.

### Layout
- Source lives in: `TODO`
- Tests live in: `TODO`
- Do not modify: `TODO` (generated code, vendored deps, legacy areas)

### Conventions specific to this repo
- Naming: `TODO`
- Import style: `TODO`
- Error handling pattern: `TODO`
- Testing pattern and framework: `TODO`

### Forbidden
- `TODO`: things that look reasonable but will break this project.

---

## 11. Project Learnings

**Accumulated corrections. This section is for the agent to maintain, not just the human.**

When the user corrects your approach, append a one-line rule here before ending the session. Write it concretely ("Always use X for Y"), never abstractly ("be careful with Y"). If an existing line already covers the correction, tighten it instead of adding a new one. Remove lines when the underlying issue goes away (model upgrades, refactors, process changes).

- Ignore `resources/` unless the user explicitly asks to inspect or modify it.
- After any doc-sync or spec-decomposition task that registers new stories, always explain the harness entropy score in the walkthrough: `harness audit` entropy = 10 pts × number of orphaned stories; this is expected for pre-implementation work, not a failure, and resolves when each story is traced and closed.
- Always run `harness-cli propose` after `harness-cli audit` and include its output in the walkthrough, so the reader knows what improvement actions are available and which are intentional no-ops.
- Only when /handoff skills is activated by users, save handoff files to `.agents/handoffs/<handoff_name>.md` for scope, DoD, and tech constraints (optionally: findings and patterns from the session). `.agents/handoffs/` holds only the current project's live transitions — do not leave stale or example handoffs there.
- Always use `deepseek/deepseek-v4-flash` through OpenRouter for M1 grounded explanations; never use GPT-5.4 Mini for that role.
- When using subagent-driven development, request `gpt-5.6-luna-high` for context investigation and `gpt-5.6-terra-high` for code implementation; if the runtime cannot select a model, state that limitation and never claim enforcement.
- Track product-work progress only in the explicitly mapped file under `docs/team/now/`; do not create root `*-NOW.md`, `PROGRESS.md`, or a separate SDD progress ledger.
- The E02 agent always self-addresses as "em" (khách = "anh/chị") in every user-visible string, backend and frontend alike; never "mình/tôi/bạn" as self-reference.
- The E02 agent's main reasoning core is gpt-4o-mini via OPENAI_API_KEY (override AGENT_MAIN_LLM_MODEL); deepseek/Mistral are fallbacks only. The deepseek rule above applies to M1 grounded explanations, not the E02 agent.
- Always live-test an E02 fix round against the running API (8010) with the exact transcript that failed before declaring it done; suite-green alone is not enough.
- E02 suggestion/comparison must be dimension-driven per category (catalog/dimensions.py) according to the user's preference — never a fixed generic trio; every spec claim must filter placeholder values ("Hãng không công bố", "Đang cập nhật") first.
- Updates must never break parts of the system that already work: additive changes behind the existing behavior, full suite green BEFORE and AFTER as proof.
- Never gate chat messages on length at any layer (no "tin nhắn quá ngắn" checks); bare agreements like "ok"/"ừ" must flow as small talk.
- Cold-start answer capture fires only for continuation intents; interrupts (policy/smalltalk/QA...) must never be stored as the pending answer and must keep the question pending.
- Every sticky preference (budget, brands, priorities, role locks) must have a clear path (clear_fields) and role locks release automatically on new preference signals.

---

## 12. How this file was built

This boilerplate synthesizes:
- Sean Donahoe's IJFW ("It Just F\*cking Works") principles: one install, working code, no ceremony.
- Andrej Karpathy's observations on LLM coding pitfalls (the four principles: think-first, simplicity, surgical changes, goal-driven execution).
- Boris Cherny's public Claude Code workflow (reactive pruning, keep it ~100 lines, only rules that fix real mistakes).
- Anthropic's official Claude Code best practices (explore-plan-code-commit, verification loops, context as the scarce resource).
- Community anti-sycophancy patterns (explicit banned phrases, direct-not-diplomatic).
- The AGENTS.md open standard (cross-tool portability via symlinks).

Read once. Edit sections 10 and 11 for your project. Prune the rest over time. This file gets better the more you use it.
