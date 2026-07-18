# Agent Instructions

<!-- AI-LOGGING:BEGIN -->
## Mandatory AI Session Logging

Before planning, editing, running commands, or invoking tools other than
reading repository instructions:

1. Read `ai-logs/README.md`.
2. Resolve the current team member exactly as required by that policy.
3. Read that member's `BOT_INSTRUCTIONS.md`.
4. Create the session log before substantive work.

If identity is not explicit and certain, ask the canonical identity question
from `ai-logs/README.md`. Do not infer identity or silently continue without a
log.
<!-- AI-LOGGING:END -->

<!-- HARNESS:BEGIN -->
## Harness

Choose the request class before any Harness operation.

- When the requested outcome is only an answer, explanation, review, diagnosis,
  plan, or status report: inspect only the material needed to respond. Keep the
  task read-only. Do not bootstrap, initialize or migrate a database, record
  intake, or record a trace.
- When the user explicitly asks to change, build, fix, or write repository
  artifacts: first run `scripts/bootstrap-harness.sh`
  on macOS/Linux or `.\scripts\bootstrap-harness.ps1` on Windows. Then use
  `docs/FEATURE_INTAKE.md` to classify and record the request, query
  `scripts/bin/harness-cli query matrix --active --summary` on macOS/Linux or
  `.\scripts\bin\harness-cli.exe query matrix --active --summary` on Windows,
  and retrieve only the lane- and task-specific context described in
  `docs/CONTEXT_RULES.md`.
<!-- HARNESS:END -->
