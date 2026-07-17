# US-025 Design

## Domain Model

A configured member has a full name, portable slug, personalized guide, and
session directory. A session log has locally generated metadata, structured
interaction summaries, file and validation evidence, final outcome, and a
redaction summary.

Identity is valid only when explicitly and unambiguously established in the
current session. External conversation identifiers and sensitive values are
invalid log data.

## Application Flow

1. A supported client loads its repository instruction entrypoint.
2. The entrypoint requires `ai-logs/README.md`.
3. The bot resolves identity or asks the canonical identity question.
4. The bot reads the selected member guide and session template.
5. The bot creates a session file with a fresh local logging identifier.
6. The bot appends sanitized structured summaries during work.
7. The bot records fresh evidence and finalizes the log before its final
   response.

## Interface Contract

The canonical identity prompt is:

```text
Which team member are you?
```

The log interface is the eight-section Markdown schema in
`ai-logs/SESSION_TEMPLATE.md`. Client shims may route to the policy but may not
define a competing workflow.

## Data Model

Logs are tracked Markdown files at:

```text
ai-logs/<member-slug>/sessions/<UTC_TIMESTAMP>_<CLIENT>_<LOCAL_LOG_ID>.md
```

The fixed timestamp contains uppercase `T` and `Z`. Client and local log ID
components use lowercase ASCII letters, digits, and hyphens.

No database schema or application storage changes are included.

## UI / Platform Impact

There is no application UI impact. Repository instruction entrypoints cover
Codex/AGENTS-aware agents, Claude Code, Gemini CLI, GitHub Copilot, and Cursor.

## Observability

The session logs are the requested review surface. They contain summaries of
human requests, AI decisions, terminal/CLI/tool actions, results, affected
files, validation, errors, final outcome, and redactions.

`scripts/validate-ai-logging.ps1` verifies structure and discovery semantics. It
does not inspect or collect credentials.

## Alternatives Considered

1. Helper CLI: deferred because it adds a runtime dependency.
2. Client hooks: rejected because capture semantics vary and raw content raises
   privacy risk.
3. Shared log directory without member separation: rejected because ownership
   would be ambiguous.
