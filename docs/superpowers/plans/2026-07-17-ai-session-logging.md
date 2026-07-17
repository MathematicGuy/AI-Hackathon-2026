# AI Coding Session Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add repository-native, per-member structured AI coding session logs with mandatory discovery instructions for Codex, Claude Code, Cursor, GitHub Copilot, and Gemini CLI.

**Architecture:** `ai-logs/README.md` is the only canonical workflow policy. Five member directories contain identity-specific guides and tracked session directories, while thin client entrypoints route supported agents to the canonical policy. A PowerShell structural validator proves the required files, references, identity mappings, schema headings, and redaction rules.

**Tech Stack:** Markdown, AGENTS.md, Claude/Gemini Markdown imports, Cursor MDC, GitHub Copilot repository instructions, PowerShell, Git, Harness CLI.

---

## File Map

- Create `scripts/validate-ai-logging.ps1`: deterministic structural validation.
- Create `ai-logs/README.md`: canonical identity, lifecycle, summary, privacy, and failure policy.
- Create `ai-logs/SESSION_TEMPLATE.md`: complete Markdown session schema.
- Create five `ai-logs/<member>/BOT_INSTRUCTIONS.md` files: personalized identity and destination data.
- Create five `ai-logs/<member>/sessions/.gitkeep` files: tracked empty session directories.
- Modify `AGENTS.md`: mandatory logging preflight before the existing Harness block.
- Create `CLAUDE.md`: import `AGENTS.md`.
- Create `GEMINI.md`: import `AGENTS.md`.
- Create `.github/copilot-instructions.md`: repository-wide logging discovery shim.
- Create `.cursor/rules/ai-logging.mdc`: always-applied logging discovery rule.
- Create `docs/decisions/0008-repository-native-ai-session-logging.md`: high-risk audit/privacy decision.
- Create `docs/stories/epics/E04-ai-session-logging/US-025-repository-native-ai-session-logs/{overview,design,execplan,validation}.md`: high-risk story evidence.

### Task 1: Add the Failing Structural Validator

**Files:**
- Create: `scripts/validate-ai-logging.ps1`
- Test: `scripts/validate-ai-logging.ps1`

- [ ] **Step 1: Write the structural validator before the logging files exist**

The validator must:

```powershell
$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$failures = [System.Collections.Generic.List[string]]::new()

function Require-Path([string]$RelativePath) {
    $fullPath = Join-Path $root $RelativePath
    if (!(Test-Path -LiteralPath $fullPath)) {
        $failures.Add("Missing required path: $RelativePath")
    }
}

function Require-Text([string]$RelativePath, [string]$ExpectedText) {
    $fullPath = Join-Path $root $RelativePath
    if (!(Test-Path -LiteralPath $fullPath)) {
        $failures.Add("Cannot inspect missing file: $RelativePath")
        return
    }
    $content = Get-Content -LiteralPath $fullPath -Raw -Encoding UTF8
    if (!$content.Contains($ExpectedText)) {
        $failures.Add("Missing required text in ${RelativePath}: $ExpectedText")
    }
}

$members = @(
    @{ Name = "Lại Trí Dũng"; Slug = "lai-tri-dung" },
    @{ Name = "Lưu Tiến Duy"; Slug = "luu-tien-duy" },
    @{ Name = "Nguyễn Phương Hoài Ngọc"; Slug = "nguyen-phuong-hoai-ngoc" },
    @{ Name = "Lưu Thiện Việt Cường"; Slug = "luu-thien-viet-cuong" },
    @{ Name = "Đinh Nhật Thành"; Slug = "dinh-nhat-thanh" }
)

Require-Path "ai-logs/README.md"
Require-Path "ai-logs/SESSION_TEMPLATE.md"
Require-Path "CLAUDE.md"
Require-Path "GEMINI.md"
Require-Path ".github/copilot-instructions.md"
Require-Path ".cursor/rules/ai-logging.mdc"

foreach ($member in $members) {
    $guide = "ai-logs/$($member.Slug)/BOT_INSTRUCTIONS.md"
    $sessionDirectory = "ai-logs/$($member.Slug)/sessions/.gitkeep"
    Require-Path $guide
    Require-Path $sessionDirectory
    Require-Text $guide $member.Name
    Require-Text $guide $member.Slug
    Require-Text $guide "sessions/"
}

foreach ($text in @(
    "Which team member are you?",
    "[REDACTED: credential]",
    "started_at_utc",
    "task_summary",
    "## Failure Handling"
)) {
    Require-Text "ai-logs/README.md" $text
}

foreach ($heading in @(
    "## Session Metadata",
    "## Objective",
    "## Interaction Log",
    "## Files Touched",
    "## Validation",
    "## Errors and Blockers",
    "## Final Outcome",
    "## Redaction Summary"
)) {
    Require-Text "ai-logs/SESSION_TEMPLATE.md" $heading
}

Require-Text "AGENTS.md" "<!-- AI-LOGGING:BEGIN -->"
Require-Text "AGENTS.md" "ai-logs/README.md"
Require-Text "CLAUDE.md" "@AGENTS.md"
Require-Text "GEMINI.md" "@./AGENTS.md"
Require-Text ".github/copilot-instructions.md" "ai-logs/README.md"
Require-Text ".cursor/rules/ai-logging.mdc" "alwaysApply: true"
Require-Text ".cursor/rules/ai-logging.mdc" "ai-logs/README.md"

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "AI logging validation passed for 5 members and 5 client entrypoints."
```

- [ ] **Step 2: Run the validator and confirm the red phase**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-ai-logging.ps1
```

Expected: exit code `1` with missing-path failures beginning with
`ai-logs/README.md`.

### Task 2: Add the Canonical Policy and Session Template

**Files:**
- Create: `ai-logs/README.md`
- Create: `ai-logs/SESSION_TEMPLATE.md`
- Test: `scripts/validate-ai-logging.ps1`

- [ ] **Step 1: Create the canonical policy**

`ai-logs/README.md` must define these exact contracts:

```markdown
# AI Coding Session Logging Policy

This file is the canonical policy for repository-tracked AI coding session
logs. Every supported coding agent must read it before substantive work.

## Team Members

| Member | Slug | Log directory |
| --- | --- | --- |
| Lại Trí Dũng | `lai-tri-dung` | `ai-logs/lai-tri-dung/sessions/` |
| Lưu Tiến Duy | `luu-tien-duy` | `ai-logs/luu-tien-duy/sessions/` |
| Nguyễn Phương Hoài Ngọc | `nguyen-phuong-hoai-ngoc` | `ai-logs/nguyen-phuong-hoai-ngoc/sessions/` |
| Lưu Thiện Việt Cường | `luu-thien-viet-cuong` | `ai-logs/luu-thien-viet-cuong/sessions/` |
| Đinh Nhật Thành | `dinh-nhat-thanh` | `ai-logs/dinh-nhat-thanh/sessions/` |
```

The same file must fully specify preflight, identity resolution, required
variables, filename format, structured interaction entries, finalization,
redaction-before-write, identity handoff, new-task behavior, and visible retry
behavior under a `## Failure Handling` heading. It must include the exact
identity question `Which team member are you?` and typed redaction markers.

- [ ] **Step 2: Create the session template**

`ai-logs/SESSION_TEMPLATE.md` must contain:

```markdown
# AI Coding Session Log

## Session Metadata

- Member:
- Member slug:
- AI client:
- Interface:
- Session ID:
- Started at (UTC):
- Repository:
- Branch:
- Log file:

## Objective

- Task summary:
- Requested outcome:

## Interaction Log

### Entry

- Timestamp (UTC):
- Human request summary:
- AI response or decision summary:
- Terminal, CLI, or tool actions:
- Outcome:
- Files involved:
- Validation:
- Redactions or limitations:

## Files Touched

None.

## Validation

None.

## Errors and Blockers

None.

## Final Outcome

- Status:
- Summary:
- Unresolved work:
- Suggested next action:

## Redaction Summary

No sensitive values were intentionally recorded.
```

- [ ] **Step 3: Run the validator**

Run the validator again.

Expected: exit code `1`; canonical policy and template checks pass, while
member and client-entrypoint checks still fail.

### Task 3: Add the Five Personalized Member Trees

**Files:**
- Create: `ai-logs/lai-tri-dung/BOT_INSTRUCTIONS.md`
- Create: `ai-logs/luu-tien-duy/BOT_INSTRUCTIONS.md`
- Create: `ai-logs/nguyen-phuong-hoai-ngoc/BOT_INSTRUCTIONS.md`
- Create: `ai-logs/luu-thien-viet-cuong/BOT_INSTRUCTIONS.md`
- Create: `ai-logs/dinh-nhat-thanh/BOT_INSTRUCTIONS.md`
- Create: each matching `sessions/.gitkeep`
- Test: `scripts/validate-ai-logging.ps1`

- [ ] **Step 1: Create each personalized guide**

`ai-logs/lai-tri-dung/BOT_INSTRUCTIONS.md`:

```markdown
# Bot Instructions for Lại Trí Dũng

This guide applies only after the current user has been explicitly identified
as Lại Trí Dũng.

## Member Record

- Full name: Lại Trí Dũng
- Member slug: `lai-tri-dung`
- Session log directory: `ai-logs/lai-tri-dung/sessions/`

## Mandatory Workflow

1. Read `../README.md` as the canonical policy.
2. Read `../SESSION_TEMPLATE.md` before creating a session file.
3. Confirm that the current-session identity maps unambiguously to this member.
4. Create and update the session log in the directory above.
5. Summarize terminal, CLI, and tool activity without storing sensitive values.
6. Finalize the log before the final response.

Opening this file does not prove the user's identity. If identity is uncertain,
return to the identity protocol in `../README.md` and ask the canonical
identity question. Never infer identity from the machine, Git configuration,
or previous sessions.
```

`ai-logs/luu-tien-duy/BOT_INSTRUCTIONS.md`:

```markdown
# Bot Instructions for Lưu Tiến Duy

This guide applies only after the current user has been explicitly identified
as Lưu Tiến Duy.

## Member Record

- Full name: Lưu Tiến Duy
- Member slug: `luu-tien-duy`
- Session log directory: `ai-logs/luu-tien-duy/sessions/`

## Mandatory Workflow

1. Read `../README.md` as the canonical policy.
2. Read `../SESSION_TEMPLATE.md` before creating a session file.
3. Confirm that the current-session identity maps unambiguously to this member.
4. Create and update the session log in the directory above.
5. Summarize terminal, CLI, and tool activity without storing sensitive values.
6. Finalize the log before the final response.

Opening this file does not prove the user's identity. If identity is uncertain,
return to the identity protocol in `../README.md` and ask the canonical
identity question. Never infer identity from the machine, Git configuration,
or previous sessions.
```

`ai-logs/nguyen-phuong-hoai-ngoc/BOT_INSTRUCTIONS.md`:

```markdown
# Bot Instructions for Nguyễn Phương Hoài Ngọc

This guide applies only after the current user has been explicitly identified
as Nguyễn Phương Hoài Ngọc.

## Member Record

- Full name: Nguyễn Phương Hoài Ngọc
- Member slug: `nguyen-phuong-hoai-ngoc`
- Session log directory: `ai-logs/nguyen-phuong-hoai-ngoc/sessions/`

## Mandatory Workflow

1. Read `../README.md` as the canonical policy.
2. Read `../SESSION_TEMPLATE.md` before creating a session file.
3. Confirm that the current-session identity maps unambiguously to this member.
4. Create and update the session log in the directory above.
5. Summarize terminal, CLI, and tool activity without storing sensitive values.
6. Finalize the log before the final response.

Opening this file does not prove the user's identity. If identity is uncertain,
return to the identity protocol in `../README.md` and ask the canonical
identity question. Never infer identity from the machine, Git configuration,
or previous sessions.
```

`ai-logs/luu-thien-viet-cuong/BOT_INSTRUCTIONS.md`:

```markdown
# Bot Instructions for Lưu Thiện Việt Cường

This guide applies only after the current user has been explicitly identified
as Lưu Thiện Việt Cường.

## Member Record

- Full name: Lưu Thiện Việt Cường
- Member slug: `luu-thien-viet-cuong`
- Session log directory: `ai-logs/luu-thien-viet-cuong/sessions/`

## Mandatory Workflow

1. Read `../README.md` as the canonical policy.
2. Read `../SESSION_TEMPLATE.md` before creating a session file.
3. Confirm that the current-session identity maps unambiguously to this member.
4. Create and update the session log in the directory above.
5. Summarize terminal, CLI, and tool activity without storing sensitive values.
6. Finalize the log before the final response.

Opening this file does not prove the user's identity. If identity is uncertain,
return to the identity protocol in `../README.md` and ask the canonical
identity question. Never infer identity from the machine, Git configuration,
or previous sessions.
```

`ai-logs/dinh-nhat-thanh/BOT_INSTRUCTIONS.md`:

```markdown
# Bot Instructions for Đinh Nhật Thành

This guide applies only after the current user has been explicitly identified
as Đinh Nhật Thành.

## Member Record

- Full name: Đinh Nhật Thành
- Member slug: `dinh-nhat-thanh`
- Session log directory: `ai-logs/dinh-nhat-thanh/sessions/`

## Mandatory Workflow

1. Read `../README.md` as the canonical policy.
2. Read `../SESSION_TEMPLATE.md` before creating a session file.
3. Confirm that the current-session identity maps unambiguously to this member.
4. Create and update the session log in the directory above.
5. Summarize terminal, CLI, and tool activity without storing sensitive values.
6. Finalize the log before the final response.

Opening this file does not prove the user's identity. If identity is uncertain,
return to the identity protocol in `../README.md` and ask the canonical
identity question. Never infer identity from the machine, Git configuration,
or previous sessions.
```

- [ ] **Step 2: Track the empty session directories**

Create a newline-only `.gitkeep` file in every member's `sessions/` directory.

- [ ] **Step 3: Run the validator**

Expected: exit code `1`; all member checks pass, while client-entrypoint checks
still fail.

### Task 4: Add Mandatory Client Entrypoints

**Files:**
- Modify: `AGENTS.md`
- Create: `CLAUDE.md`
- Create: `GEMINI.md`
- Create: `.github/copilot-instructions.md`
- Create: `.cursor/rules/ai-logging.mdc`
- Test: `scripts/validate-ai-logging.ps1`

- [ ] **Step 1: Add the root mandatory preflight**

Insert this block immediately after `# Agent Instructions` and before the
existing Harness block:

```markdown
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
```

- [ ] **Step 2: Add Claude Code and Gemini CLI imports**

`CLAUDE.md`:

```markdown
# Claude Code Instructions

@AGENTS.md
```

`GEMINI.md`:

```markdown
# Gemini CLI Instructions

@./AGENTS.md
```

- [ ] **Step 3: Add GitHub Copilot and Cursor shims**

`.github/copilot-instructions.md`:

```markdown
# GitHub Copilot Instructions

Read `AGENTS.md` and `ai-logs/README.md` before planning, editing, running
commands, or invoking coding tools. The AI session logging policy is mandatory.
Resolve the current member and create that member's session log before
substantive work. Do not duplicate or override the canonical policy here.
```

`.cursor/rules/ai-logging.mdc`:

```markdown
---
description: Mandatory repository-wide AI coding session logging
globs:
alwaysApply: true
---

Read @AGENTS.md and @ai-logs/README.md before planning, editing, running
commands, or invoking coding tools. Follow the canonical identity and logging
workflow before substantive work.
```

- [ ] **Step 4: Run the validator and confirm the green phase**

Expected:

```text
AI logging validation passed for 5 members and 5 client entrypoints.
```

### Task 5: Record High-Risk Logging Decision and Story Evidence

**Files:**
- Create: `docs/decisions/0008-repository-native-ai-session-logging.md`
- Create: `docs/stories/epics/E04-ai-session-logging/US-025-repository-native-ai-session-logs/overview.md`
- Create: `docs/stories/epics/E04-ai-session-logging/US-025-repository-native-ai-session-logs/design.md`
- Create: `docs/stories/epics/E04-ai-session-logging/US-025-repository-native-ai-session-logs/execplan.md`
- Create: `docs/stories/epics/E04-ai-session-logging/US-025-repository-native-ai-session-logs/validation.md`

- [ ] **Step 1: Write the decision**

Record the accepted choice: structured summaries, repository-native
instructions, five supported client entrypoints, redaction before write, no
identity inference, no raw transcript hooks, and visible failure behavior.

- [ ] **Step 2: Write the high-risk story packet**

The packet must link the approved design, list audit/privacy as the hard gate,
keep application code explicitly out of scope, and use
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File
.\scripts\validate-ai-logging.ps1` as mechanical proof.

- [ ] **Step 3: Register the decision and story**

Run:

```powershell
.\scripts\bin\harness-cli.exe decision add --id 0008-repository-native-ai-session-logging --title "Repository-Native AI Session Logging" --doc docs/decisions/0008-repository-native-ai-session-logging.md --notes "Approved structured-summary policy with redaction-before-write."
.\scripts\bin\harness-cli.exe story add --id US-025 --title "Repository-Native AI Session Logs" --lane high-risk --verify "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-ai-logging.ps1"
.\scripts\bin\harness-cli.exe story update --id US-025 --status in_progress
```

Expected: the decision and story are recorded, and `US-025` is active with a
verification command.

### Task 6: Verify, Finalize Evidence, and Commit

**Files:**
- Modify: `docs/stories/epics/E04-ai-session-logging/US-025-repository-native-ai-session-logs/validation.md`
- Modify: Harness durable records
- Test: all logging artifacts

- [ ] **Step 1: Run all structural and repository checks**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-ai-logging.ps1
git diff --check
rg -n -i "\b(T[B]D|T[O]DO|FIX[M]E|X[X]X)\b" ai-logs AGENTS.md CLAUDE.md GEMINI.md .github/copilot-instructions.md .cursor/rules/ai-logging.mdc
```

Expected: validator passes, `git diff --check` prints nothing, and the marker
scan returns no matches.

- [ ] **Step 2: Record validation evidence**

Update the story validation file with the exact commands, exit codes, and
results. Set proof flags with:

```powershell
.\scripts\bin\harness-cli.exe story update --id US-025 --unit 1 --integration 1 --e2e 0 --platform 1 --evidence "Static policy validator passed for five members and five client entrypoints; whitespace and unresolved-marker scans passed."
```

- [ ] **Step 3: Run story proof and complete the story**

Run:

```powershell
.\scripts\bin\harness-cli.exe story verify US-025
.\scripts\bin\harness-cli.exe story complete US-025
```

Expected: both commands pass and the story becomes `implemented`.

- [ ] **Step 4: Commit only logging-related tracked files**

Stage explicit paths and commit:

```powershell
git add -- ai-logs AGENTS.md CLAUDE.md GEMINI.md .github/copilot-instructions.md .cursor/rules/ai-logging.mdc scripts/validate-ai-logging.ps1 docs/decisions/0008-repository-native-ai-session-logging.md docs/stories/epics/E04-ai-session-logging/US-025-repository-native-ai-session-logs docs/superpowers/plans/2026-07-17-ai-session-logging.md
git commit -m "feat: add per-member AI session logging"
```

- [ ] **Step 5: Record the final Harness trace**

Read `docs/TRACE_SPEC.md`, then record a detailed high-risk trace containing
the files read, actions, validation, changed files, redaction decision, outcome,
and any Harness friction. Confirm the printed trace score meets the high-risk
tier.
