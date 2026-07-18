# AI Coding Session Logging Policy

This file is the canonical policy for AI-assisted coding session logs in this
repository. It applies to Codex, Claude Code, Cursor, GitHub Copilot, Gemini CLI,
and any other repository-aware AI client that follows the repository
instruction entrypoints. Client-specific instruction files may require this
policy, but they must not redefine its workflow.

Logs are repository artifacts. They contain concise, structured summaries of
work performed with an AI client. They are not raw transcripts, command-output
archives, telemetry streams, or secret stores.

## Team Members
IMPORTANT: Allow a valid repository `.env` `TEAM_MEMBER` slug to resolve team identity safely.

Repository convention: Đinh Nhật Thành uses `TEAM_MEMBER="dinh-nhat-thanh"`.
Future agents must inspect only this assignment, match it exactly against the
allowlist below, and must not read or expose other `.env` values.

Only the following identities and directory slugs are valid:

| Team member | Directory slug |
| --- | --- |
| Lại Trí Dũng | `lai-tri-dung` |
| Lưu Tiến Duy | `luu-tien-duy` |
| Nguyễn Phương Hoài Ngọc | `nguyen-phuong-hoai-ngoc` |
| Lưu Thiện Việt Cường | `luu-thien-viet-cuong` |
| Đinh Nhật Thành | `dinh-nhat-thanh` |

Each member has a personalized guide at
`ai-logs/<member-slug>/BOT_INSTRUCTIONS.md` and an independent log directory at
`ai-logs/<member-slug>/sessions/`.

## Mandatory Preflight

Before substantive work, the AI must:

1. Read this canonical policy.
2. Resolve the current team member's identity.
3. Read that member's `BOT_INSTRUCTIONS.md`.
4. Collect session metadata only from information already exposed by the
   client or current context, using the documented safe fallbacks for anything
   else.
5. Do not create a session log yet. Create or update one only when a durable
   deliverable is produced (for example, a spec, plan, code, or test), the task
   is completed, or a major bug or blocker is reached; finalize it before the
   session ends when one exists.

Reading repository instructions, reading only the `TEAM_MEMBER` assignment from
the repository `.env`, asking the identity question, and asking questions needed
to clarify the task are allowed before a session log exists. Preflight must not
run a terminal command to discover metadata other than reading only that
`TEAM_MEMBER` assignment. When a milestone log is created, use a branch name
already exposed by the client; otherwise record `unknown`, then optionally run a
sanitized Git command and update the metadata.

If this policy conflicts with a duplicated workflow in a client shim or member
guide, this policy is the workflow source of truth. Higher-priority system,
developer, and user instructions still take precedence.

## Identity Resolution

Resolve identity from either an explicit, unambiguous identity statement in the
current session or the repository `.env` `TEAM_MEMBER` assignment when its value
exactly matches one valid directory slug in the table above. Inspect only that
assignment: never display, log, or retain other `.env` content. The AI must not
infer identity from an operating-system account, Git author, email address,
machine name, repository history, directory ownership, or an earlier session.

When neither source resolves identity, or when they conflict, ask exactly:

> Which team member are you?

Present or accept only the five members listed in this policy. If the answer
does not map unambiguously to one member, ask again and do not begin substantive
work. Never select a directory by guessing.

If a different member takes over an active conversation, finalize the current
member's log before starting a new log in the new member's directory.

## Session Metadata

Collect these variables without requesting information that may expose
credentials or other sensitive values:

| Variable | Source | Safe fallback |
| --- | --- | --- |
| `member` | Explicit identity in the current session or a valid repository `.env` `TEAM_MEMBER` slug | Ask the user. |
| `member_slug` | The mapping in this policy | None; ambiguity blocks substantive work. |
| `ai_client` | Current client or runtime | Ask only when the runtime does not expose it. |
| `interface` | Known CLI, IDE, chat, agent, or other surface | `unknown` |
| `session_id` | A new local, non-sensitive random logging identifier generated for this log | Generate it before creating the log. |
| `started_at_utc` | Current UTC time at log creation | Generate it at log creation. |
| `task_summary` | Concise summary of the current request | Clarify only when the goal is unclear. |
| `repository` | Current repository root | Use the repository directory name. |
| `branch` | Branch already exposed without a command | Record `unknown`, then optionally detect and update it after log creation. |

Ask only for variables that cannot be derived safely. Never ask a user to
provide a secret for inclusion in a log. Generate a fresh local `session_id`
for every log, even when the client exposes an identifier. Never persist a
client or external conversation, thread, session, request, run, trace, or
message identifier in log metadata, filenames, or log content.

## Log Creation and Naming

When a milestone requires a log, copy the structure of
`ai-logs/SESSION_TEMPLATE.md` into:

```text
ai-logs/<member-slug>/sessions/<UTC_TIMESTAMP>_<CLIENT>_<LOGGING_SESSION_ID>.md
```

Use the timestamp format `YYYY-MM-DDTHH-mm-ssZ`; its `T` and `Z` are
deliberately uppercase. Only the `CLIENT` and `LOGGING_SESSION_ID` components
are restricted to lowercase ASCII letters, digits, and hyphens. Normalize the
client name to that character set and generate the local random logging
identifier in that character set. Never use an external or client conversation
identifier as either component. Create the file when the milestone is reached
and populate every metadata field. Use `unknown` only where this policy permits
it.

## Required Log Schema

Every session log must retain these top-level sections in this order:

1. `Session Metadata`
2. `Objective`
3. `Interaction Log`
4. `Files Touched`
5. `Validation`
6. `Errors and Blockers`
7. `Final Outcome`
8. `Redaction Summary`

Use the explicit value `None` in an empty section or field. Do not leave
unresolved placeholder markers in a completed log.

## Interaction Logging

When a session log exists, append a concise structured entry for each completed
milestone or major bug/blocker. Each applicable entry records:

- A UTC timestamp.
- A concise summary of the human request.
- A concise summary of the AI response, decision, or rationale.
- Sanitized terminal commands, CLI activity, and tool actions.
- The exit status and a safe summary of important output or outcome.
- Files created, changed, deleted, or inspected when relevant.
- Validation performed and its result when relevant.
- Redactions, omitted sensitive material, or logging limitations.

Summarize behavior and evidence. Do not reproduce full prompts, full model
responses, long command output, generated files, binary content, or raw request
and response payloads. Group related work into one milestone entry; do not log
every tool call or intermediate step.

Update `Files Touched`, `Validation`, and `Errors and Blockers` as work
progresses. Include inspected files only when the inspection materially
influenced the work. Never claim validation that was not actually run.

## Privacy and Redaction

Sanitize every summary before writing it. A log must never contain:

- Passwords, access tokens, session tokens, cookies, API keys, signing keys, or
  other credential material.
- Values read from `.env` files, secret stores, credential managers, or
  authentication headers.
- Private keys or complete certificates.
- Unnecessary personal data.
- Client or external conversation, thread, session, request, run, trace, or
  message identifiers.
- Full output that may include sensitive values.
- Raw prompts, responses, or payloads when a structured summary is sufficient.

Replace a sensitive substring with a typed marker such as:

```text
[REDACTED: credential]
[REDACTED: environment value]
[REDACTED: personal data]
```

Rewrite commands containing sensitive arguments as sanitized descriptions.
Record only command intent, safe arguments when useful, exit status, and a safe
outcome. Do not write a secret first and rely on later cleanup; exclusion or
redaction must happen before repository content is written.

## Finalization and Continuation

Before sending the final response for the task, update the log when one exists
with:

- The final outcome and current status.
- Fresh validation evidence.
- Files created, changed, deleted, or materially inspected.
- Errors, blockers, and their disposition.
- Unresolved work and suggested next actions.
- A statement that sensitive values were not intentionally recorded.

When work continues after a final response in the same client session, reuse
the same log only if both the member and task context remain unchanged. A
materially different task starts a new session log. A member change always
requires finalizing the current log and starting another.

## Failure Handling

- If this canonical policy cannot be read, report the missing or unreadable
  path and do not begin substantive work.
- If identity remains ambiguous, repeat the exact identity question and do not
  create a log in a guessed directory.
- If the member guide cannot be read, report its path and do not begin
  substantive work.
- If a required milestone log creation or append fails, report the failure
  immediately. Retain only a sanitized pending summary in the current session
  context, retry after the filesystem problem is resolved, and do not silently
  continue.
- If the repository or Git branch cannot be detected, record `unknown`; this
  condition does not block work.
- If command output is too large or potentially sensitive, record only the
  command intent, exit status, and a safe outcome summary.
- If a client disables or ignores repository instructions, repository files
  cannot force compliance. The supported entrypoints reduce this limitation
  but cannot override a client's higher-priority configuration.

## Acceptance Criteria

This policy is being followed only when:

- A supported fresh session is instructed to read this file before substantive
  work.
- A valid repository `.env` `TEAM_MEMBER` slug resolves identity without a
  question; missing, invalid, uncertain, or conflicting identity triggers the
  exact identity question before substantive work.
- Confirmed identity maps to the correct member guide and independent session
  directory.
- A complete structured Markdown log is created from the template at a durable
  milestone, major bug/blocker, or task completion, without a helper runtime.
- Human requests, AI decisions, tool activity, file changes, validation,
  errors, and outcomes are summarized as applicable.
- Sensitive values are excluded or redacted before writing.
- Log write failures are reported immediately and never ignored silently.
- Finalization records evidence, remaining work, and the redaction statement.
