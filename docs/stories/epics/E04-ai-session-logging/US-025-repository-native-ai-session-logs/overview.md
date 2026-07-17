# US-025 Repository-Native AI Session Logs

## Current Behavior

The repository has no member-specific location or cross-client policy for
recording structured AI coding activity.

## Target Behavior

Supported AI coding clients load one canonical policy before substantive work,
resolve the current member without inference, create a structured Markdown log
in that member's directory, summarize terminal/CLI/tool activity, redact
sensitive content before writing, and finalize the log before the final
response.

## Affected Users

- Lại Trí Dũng
- Lưu Tiến Duy
- Nguyễn Phương Hoài Ngọc
- Lưu Thiện Việt Cường
- Đinh Nhật Thành

## Affected Product Docs

- `ai-logs/README.md`
- `ai-logs/SESSION_TEMPLATE.md`
- `docs/superpowers/specs/2026-07-17-ai-session-logging-design.md`
- `docs/decisions/0008-repository-native-ai-session-logging.md`

## Non-Goals

- Changing application code or product architecture.
- Capturing raw transcripts or terminal-output archives.
- Installing client hooks or background collectors.
- Persisting credentials or external/client conversation identifiers.
- Reconstructing sessions that started before the policy existed.
