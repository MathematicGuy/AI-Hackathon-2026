# US-025 Validation

## Proof Strategy

Use deterministic repository checks. The primary validator proves the member
tree, policy literals, template headings, guide parity, AGENTS placement, and
client discovery semantics. Independent scans prove that no synthetic member
logs or unresolved marker text were introduced.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Policy literals, template headings, member mappings, guide parity, semantic client imports/frontmatter. |
| Integration | AGENTS preflight ordering and five client entrypoints route to the canonical policy. |
| E2E | Not applicable; this feature has no application surface. |
| Platform | Windows PowerShell 5.1 parses the ASCII-only validator and reads authored UTF-8 files correctly. |
| Performance | Not applicable; validation covers a fixed, small file set. |
| Logs/Audit | No synthetic session logs; structured-summary and redaction-before-write rules are present. |

## Fixtures

- Lại Trí Dũng / `lai-tri-dung`
- Lưu Tiến Duy / `luu-tien-duy`
- Nguyễn Phương Hoài Ngọc / `nguyen-phuong-hoai-ngoc`
- Lưu Thiện Việt Cường / `luu-thien-viet-cuong`
- Đinh Nhật Thành / `dinh-nhat-thanh`
- One harmless Claude client comment used temporarily to prove that semantic
  validation does not reject non-conflicting client-specific text.

## Commands

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-ai-logging.ps1

$sessionFiles = Get-ChildItem -LiteralPath .\ai-logs -Recurse -File |
    Where-Object {
        $_.FullName -match '[\\/]sessions[\\/]' -and $_.Name -ne '.gitkeep'
    }
if ($sessionFiles) { exit 1 }

rg -n -i "\b(T[B]D|T[O]DO|FIX[M]E|X[X]X)\b" `
    ai-logs AGENTS.md CLAUDE.md GEMINI.md `
    .github/copilot-instructions.md .cursor/rules/ai-logging.mdc

git diff --check
```

## Acceptance Evidence

Recorded on 2026-07-17:

- Structural validator: exit `0`;
  `AI logging validation passed for 5 members and 5 client entrypoints.`
- Synthetic session log scan: exit `0`; zero session files other than the five
  `.gitkeep` files.
- Unresolved-marker scan: exit `0`; no matches.
- Git whitespace check: exit `0`; no whitespace errors.
- The semantic-validation RED case reproduced the former brittle behavior with
  a harmless Claude comment, and the revised validator passed before the
  temporary comment was removed.
