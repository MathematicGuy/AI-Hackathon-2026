# 0008 Repository-Native AI Session Logging

Date: 2026-07-17

## Status

Accepted

## Context

Five team members use multiple AI coding clients in the same repository. The
repository needs reviewable evidence of human-AI coding activity without
depending on one vendor's transcript format or collecting raw terminal output.

AI prompts, command arguments, tool payloads, and client identifiers can contain
credentials or correlatable data. The logging workflow therefore changes agent
instructions and introduces an audit/privacy hard gate.

## Decision

Use repository-native Markdown instructions and structured session summaries.

- `ai-logs/README.md` is the canonical workflow policy.
- Each configured member has a personalized `BOT_INSTRUCTIONS.md` and an
  independent `sessions/` directory.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, GitHub Copilot instructions, and a
  Cursor always-applied rule route supported clients to the canonical policy.
- A bot asks `Which team member are you?` whenever current-session identity is
  not explicit and certain.
- A fresh local, non-sensitive logging identifier is generated for each log.
  Client and external conversation identifiers are never persisted.
- Logs contain structured summaries rather than raw prompts, responses, tool
  payloads, or large command output.
- Sensitive values are excluded or redacted before repository content is
  written.
- Logging failures are visible and block silent continuation.
- `scripts/validate-ai-logging.ps1` mechanically verifies the member trees,
  required policy content, template schema, guide parity, and client discovery
  semantics.

## Alternatives Considered

1. Add a helper CLI that creates and appends logs. Rejected for the initial
   version because coding agents can write the Markdown files directly and a
   helper would add a runtime dependency.
2. Install client hooks that capture full transcripts. Rejected because hook
   behavior differs by client and raw capture materially increases privacy and
   credential-exposure risk.
3. Keep one shared team log. Rejected because it weakens ownership and makes
   concurrent sessions difficult to review.

## Consequences

Positive:

- Every configured member has an isolated, reviewable logging location.
- The workflow works across supported repository-aware clients.
- Structured summaries provide useful evidence without storing raw transcripts.
- Identity uncertainty and write failures have explicit stop behavior.
- A deterministic validator catches missing or drifting instruction surfaces.

Tradeoffs:

- Repository instructions cannot force compliance when a client disables or
  ignores repository context.
- Agents remain responsible for summarizing meaningful interactions and
  redacting content before writing.
- Markdown logs will grow repository history and require normal review hygiene.

## Verification

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-ai-logging.ps1
```

The command must exit `0` and report five members and five client entrypoints.
