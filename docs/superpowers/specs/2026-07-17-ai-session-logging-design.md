# AI Coding Session Logging Design

**Date:** 2026-07-17

**Status:** Approved

## Purpose

Create a repository-native logging system that records structured summaries of
AI-assisted coding sessions for these team members:

| Member | Directory slug |
| --- | --- |
| Lại Trí Dũng | `lai-tri-dung` |
| Lưu Tiến Duy | `luu-tien-duy` |
| Nguyễn Phương Hoài Ngọc | `nguyen-phuong-hoai-ngoc` |
| Lưu Thiện Việt Cường | `luu-thien-viet-cuong` |
| Đinh Nhật Thành | `dinh-nhat-thanh` |

The system must work through repository instructions rather than client hooks
or raw transcript capture. All policy, instruction, template, and log content
must be written in English. Vietnamese personal names retain their correct
spelling because they are proper names.

## Goals

- Give each member an isolated directory for their AI coding logs.
- Give each member a personalized bot instruction file.
- Require supported AI clients to load one canonical logging policy before
  substantive work.
- Require the bot to ask for the member's identity whenever identity is not
  explicit and certain in the current session.
- Make the bot create and maintain a Markdown log without relying on a helper
  runtime.
- Record structured summaries of prompts, responses, terminal commands, CLI
  activity, tool calls, file changes, validation, errors, and outcomes.
- Keep credentials and sensitive values out of repository history.

## Non-Goals

- Capturing complete raw transcripts.
- Installing client-specific hooks or background collectors.
- Recording secrets, environment values, private keys, access tokens, or
  sensitive personal data.
- Inferring a member from an operating-system account, Git author, email
  address, machine name, or a previous session.
- Supporting AI clients that ignore all repository instruction mechanisms.
- Retroactively reconstructing sessions that were not logged.

## Chosen Approach

Use repository-native Markdown instructions and logs. A canonical policy under
`ai-logs/` defines the workflow. Client-specific instruction entrypoints direct
Codex, Claude Code, Cursor, GitHub Copilot, and Gemini CLI to that policy. Each
member file contains only identity-specific details and links back to the
canonical policy, so workflow rules have a single source of truth.

This approach is preferred over a helper CLI because it introduces no runtime
dependency and lets any repository-aware coding agent create files directly.
It is preferred over hooks because hooks vary by client and would increase the
risk of collecting unsanitized content.

## Repository Structure

```text
ai-logs/
  README.md
  SESSION_TEMPLATE.md
  lai-tri-dung/
    BOT_INSTRUCTIONS.md
    sessions/
      .gitkeep
  luu-tien-duy/
    BOT_INSTRUCTIONS.md
    sessions/
      .gitkeep
  nguyen-phuong-hoai-ngoc/
    BOT_INSTRUCTIONS.md
    sessions/
      .gitkeep
  luu-thien-viet-cuong/
    BOT_INSTRUCTIONS.md
    sessions/
      .gitkeep
  dinh-nhat-thanh/
    BOT_INSTRUCTIONS.md
    sessions/
      .gitkeep
```

The repository instruction entrypoints are:

| Client | Entrypoint | Required behavior |
| --- | --- | --- |
| Codex and AGENTS-aware clients | `AGENTS.md` | Require `ai-logs/README.md` as a preflight instruction. |
| Claude Code | `CLAUDE.md` | Import `AGENTS.md` with `@AGENTS.md`. |
| Gemini CLI | `GEMINI.md` | Import `AGENTS.md` with `@./AGENTS.md`. |
| GitHub Copilot | `.github/copilot-instructions.md` | Require `AGENTS.md` and `ai-logs/README.md`. |
| Cursor | `.cursor/rules/ai-logging.mdc` | Use an always-applied rule that requires `AGENTS.md` and `ai-logs/README.md`. |

The client shims must not duplicate the canonical session workflow. Their
responsibility is limited to ensuring discovery and stating that the canonical
policy is mandatory.

## Session Lifecycle

### 1. Preflight

Before planning, editing, running terminal commands, or invoking non-reading
tools, the bot reads:

1. `ai-logs/README.md`.
2. The selected member's `BOT_INSTRUCTIONS.md`, once identity is resolved.

Reading repository instructions and asking identity or task-clarification
questions are permitted before a session log exists. Every other action is
substantive work for this policy.

### 2. Resolve Identity

Identity is resolved only when the user explicitly identifies one of the five
members in the current session or the current session already contains an
unambiguous identity statement.

When identity is absent or uncertain, the bot asks:

> Which team member are you?

The bot presents or accepts only the five configured members. It must not guess.
If the response does not map unambiguously to one configured member, the bot
asks again before substantive work.

If a different member takes over an active conversation, the bot finalizes the
current log and starts a new session log under the new member.

### 3. Collect Session Variables

The bot obtains the following variables:

| Variable | Source | Fallback |
| --- | --- | --- |
| `member` | Explicit current-session identity | Ask the user. |
| `member_slug` | Member mapping in the canonical policy | No fallback; ambiguous identities block work. |
| `ai_client` | Current client/runtime | Ask only if the runtime does not expose it. |
| `interface` | CLI, IDE, chat, agent, or other known surface | Use `unknown` when the surface cannot be determined. |
| `session_id` | Client session identifier | Generate a short unique identifier. |
| `started_at_utc` | Current UTC time | Generate at log creation. |
| `task_summary` | Current user request | Ask for clarification only when the goal is unclear. |
| `repository` | Current repository root | Use the repository directory name. |
| `branch` | Current Git branch | Use `unknown` when Git is unavailable. |

The bot asks only for variables it cannot derive safely. It must never ask the
user to provide secrets for the log.

### 4. Create the Log

The bot copies the structure of `ai-logs/SESSION_TEMPLATE.md` into:

```text
ai-logs/<member-slug>/sessions/<UTC_TIMESTAMP>_<CLIENT>_<SESSION_ID>.md
```

Filename components use lowercase ASCII characters, digits, and hyphens.
The timestamp format is `YYYY-MM-DDTHH-mm-ssZ`. The log is created before
substantive coding work starts.

### 5. Append Structured Entries

The bot appends one entry after each meaningful interaction or action group.
Each entry contains:

- UTC timestamp.
- Human request summary.
- AI response or decision summary.
- Sanitized terminal, CLI, and tool actions.
- Outcome or important output summary.
- Files created, changed, deleted, or inspected when relevant.
- Validation performed and its result when relevant.
- Redactions or logging limitations.

Entries summarize behavior; they do not reproduce full prompts, full model
responses, large command outputs, generated files, or binary content.

### 6. Finalize

Before sending the final response, the bot records:

- Final outcome.
- Validation evidence.
- Files changed.
- Errors or blockers.
- Unresolved work and suggested next actions.
- A statement that sensitive values were not intentionally recorded.

If work continues in the same client session after a final response, the bot
may reopen the same log only when the member and task context remain unchanged.
A materially different task starts a new log.

## Log Schema

Every session log contains these top-level sections:

1. `Session Metadata`
2. `Objective`
3. `Interaction Log`
4. `Files Touched`
5. `Validation`
6. `Errors and Blockers`
7. `Final Outcome`
8. `Redaction Summary`

The metadata block contains all session variables. Empty evidence sections use
the explicit value `None`, not unresolved placeholder markers.

## Privacy and Redaction

Logs are committed repository artifacts and must be safe for repository
history.

The bot must never record:

- Passwords, tokens, cookies, API keys, signing keys, or credential material.
- Values read from `.env` files, secret stores, credential managers, or
  authentication headers.
- Private keys or complete certificates.
- Unnecessary personal data.
- Full command output that may contain sensitive values.
- Raw request or response payloads when a structured summary is sufficient.

Sensitive substrings are replaced with a typed marker such as:

```text
[REDACTED: credential]
[REDACTED: environment value]
[REDACTED: personal data]
```

Commands that contain sensitive arguments are rewritten as sanitized command
summaries. The bot must not place a secret in the log and then rely on a later
cleanup.

## Error Handling

- If the canonical policy cannot be read, the bot reports the missing path and
  does not begin substantive work.
- If identity remains ambiguous, the bot repeats the identity request and does
  not create a log in a guessed directory.
- If log creation or append fails, the bot reports the failure immediately,
  retains a sanitized pending summary in session context, retries after the
  filesystem problem is resolved, and does not silently continue.
- If the repository or Git branch cannot be detected, the bot records
  `unknown`; this does not block work.
- If a command output is too large or potentially sensitive, the bot records
  only the command intent, exit status, and a safe outcome summary.
- If a client disables or ignores repository instructions, repository files
  alone cannot enforce compliance. The five supported entrypoints reduce this
  limitation but do not override a client's higher-priority configuration.

## Validation Strategy

Implementation validation must prove:

1. The canonical policy, template, five member guides, and five session
   directories exist.
2. Every member guide contains the correct full name, slug, and destination.
3. `AGENTS.md` contains a mandatory preflight reference to
   `ai-logs/README.md`.
4. Claude Code and Gemini CLI import `AGENTS.md`.
5. GitHub Copilot and Cursor contain repository-wide mandatory references to
   the canonical policy.
6. The session template contains every required schema section.
7. Searches find no placeholder text in the delivered logging files.
8. A dry-run review covers known identity, unknown identity, redaction, write
   failure, and finalization behavior without creating synthetic member logs.
9. All authored prose is English except proper names and literal paths.

## Acceptance Criteria

- A fresh supported AI session receives a repository instruction that requires
  reading the canonical logging policy.
- A bot that does not know the member asks for identity before substantive
  work.
- A bot with a confirmed member can determine the correct personalized guide
  and log directory.
- The bot can create a complete structured Markdown session log from the
  template without a helper CLI.
- Terminal, CLI, and tool activity is summarized with outcomes and affected
  files.
- Sensitive values are excluded or redacted before writing.
- Log write failures are visible and cannot be silently ignored.
- All five members have independent, repository-tracked logging locations.

## Alternatives Considered

### Instructions plus a helper CLI

A helper CLI could create and append logs more mechanically. It was rejected
for the initial version because it adds a runtime dependency and duplicates
capabilities already available to coding agents.

### Client hooks and automatic transcript capture

Hooks could capture more events automatically. They were rejected because their
configuration differs by client, coverage would be inconsistent, and raw
capture increases privacy and credential exposure risk.

## Client Documentation Checked

The entrypoint choices were checked on 2026-07-17 against:

- Claude Code project memory:
  <https://code.claude.com/docs/en/memory>
- Cursor project rules:
  <https://docs.cursor.com/context/rules>
- GitHub Copilot repository instructions:
  <https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions>
- Gemini CLI context files:
  <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md>
