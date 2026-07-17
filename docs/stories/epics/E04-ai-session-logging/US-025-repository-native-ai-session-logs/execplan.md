# US-025 Exec Plan

## Goal

Deliver member-specific, repository-native structured AI coding session logs
with mandatory discovery instructions and privacy-safe validation.

## Scope

In scope:

- Canonical policy and session template under `ai-logs/`.
- Five personalized member guides and session directories.
- Instruction entrypoints for five supported client families.
- A structural policy validator.
- Logging-specific design, decision, story, and validation evidence.

Out of scope:

- Application code and product behavior.
- Product architecture changes.
- Raw transcript capture.
- Client hooks and background services.
- External storage or analytics.

## Risk Classification

Risk flags:

- Audit/security.
- Privacy and sensitive data.
- Agent instruction behavior.

Hard gates:

- Sensitive values must be excluded or redacted before writing.
- Identity must not be inferred.
- Client/external conversation identifiers must not be persisted.
- A logging failure must not be silently ignored.

## Work Phases

1. Validate the absent feature with a failing structural check.
2. Add the canonical policy and template.
3. Add five member-specific logging trees.
4. Add client instruction entrypoints.
5. Record the audit/privacy decision and story evidence.
6. Run structural, marker, synthetic-log, whitespace, and Harness checks.
7. Commit and integrate only logging-related changes.

## Stop Conditions

Pause for human confirmation if:

- The requested member list changes.
- Raw transcript capture is requested.
- A design would store credentials or external session identifiers.
- Application code or product behavior would need to change.
- Validation requirements would need to be weakened.
