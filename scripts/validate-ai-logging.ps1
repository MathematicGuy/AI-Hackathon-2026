$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$failures = [System.Collections.Generic.List[string]]::new()

function Require-Path([string]$RelativePath) {
    $fullPath = Join-Path $root $RelativePath
    if (!(Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $failures.Add("Missing required path: $RelativePath")
    }
}

function Require-Text([string]$RelativePath, [string]$ExpectedText) {
    $fullPath = Join-Path $root $RelativePath
    if (!(Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $failures.Add("Cannot inspect missing file: $RelativePath")
        return
    }
    $content = Get-Content -LiteralPath $fullPath -Raw -Encoding UTF8
    if (!$content.Contains($ExpectedText)) {
        $failures.Add("Missing required text in ${RelativePath}: $ExpectedText")
    }
}

function ConvertTo-NormalizedLineEndings([string]$Text) {
    return $Text.Replace("`r`n", "`n").Replace("`r", "`n")
}

function Require-Pattern(
    [string]$RelativePath,
    [string]$Pattern,
    [string]$Description
) {
    $fullPath = Join-Path $root $RelativePath
    if (!(Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $failures.Add("Cannot inspect missing file: $RelativePath")
        return
    }

    $content = Get-Content -LiteralPath $fullPath -Raw -Encoding UTF8
    $normalizedContent = ConvertTo-NormalizedLineEndings $content
    if (![regex]::IsMatch($normalizedContent, $Pattern)) {
        $failures.Add("Missing $Description in client entrypoint: $RelativePath")
    }
}

function Require-Prefix([string]$RelativePath, [string]$ExpectedPrefix) {
    $fullPath = Join-Path $root $RelativePath
    if (!(Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $failures.Add("Cannot inspect prefix of missing file: $RelativePath")
        return
    }

    $content = Get-Content -LiteralPath $fullPath -Raw -Encoding UTF8
    $normalizedContent = ConvertTo-NormalizedLineEndings $content
    $normalizedPrefix = ConvertTo-NormalizedLineEndings $ExpectedPrefix

    if (!$normalizedContent.StartsWith(
        $normalizedPrefix,
        [System.StringComparison]::Ordinal
    )) {
        $failures.Add(
            "AI logging block must immediately follow the AGENTS.md heading " +
            "and precede the Harness block."
        )
    }
}

function ConvertFrom-UnicodeCodePoints([int[]]$CodePoints) {
    return -join ($CodePoints | ForEach-Object { [char]$_ })
}

$members = @(
    @{
        Name = (ConvertFrom-UnicodeCodePoints @(
            0x004C, 0x1EA1, 0x0069, 0x0020, 0x0054, 0x0072,
            0x00ED, 0x0020, 0x0044, 0x0169, 0x006E, 0x0067
        ))
        Slug = "lai-tri-dung"
    },
    @{
        Name = (ConvertFrom-UnicodeCodePoints @(
            0x004C, 0x01B0, 0x0075, 0x0020, 0x0054, 0x0069,
            0x1EBF, 0x006E, 0x0020, 0x0044, 0x0075, 0x0079
        ))
        Slug = "luu-tien-duy"
    },
    @{
        Name = (ConvertFrom-UnicodeCodePoints @(
            0x004E, 0x0067, 0x0075, 0x0079, 0x1EC5, 0x006E,
            0x0020, 0x0050, 0x0068, 0x01B0, 0x01A1, 0x006E,
            0x0067, 0x0020, 0x0048, 0x006F, 0x00E0, 0x0069,
            0x0020, 0x004E, 0x0067, 0x1ECD, 0x0063
        ))
        Slug = "nguyen-phuong-hoai-ngoc"
    },
    @{
        Name = (ConvertFrom-UnicodeCodePoints @(
            0x004C, 0x01B0, 0x0075, 0x0020, 0x0054, 0x0068,
            0x0069, 0x1EC7, 0x006E, 0x0020, 0x0056, 0x0069,
            0x1EC7, 0x0074, 0x0020, 0x0043, 0x01B0, 0x1EDD,
            0x006E, 0x0067
        ))
        Slug = "luu-thien-viet-cuong"
    },
    @{
        Name = (ConvertFrom-UnicodeCodePoints @(
            0x0110, 0x0069, 0x006E, 0x0068, 0x0020, 0x004E,
            0x0068, 0x1EAD, 0x0074, 0x0020, 0x0054, 0x0068,
            0x00E0, 0x006E, 0x0068
        ))
        Slug = "dinh-nhat-thanh"
    }
)

$clientEntrypoints = @(
    "AGENTS.md"
    "CLAUDE.md"
    "GEMINI.md"
    ".github/copilot-instructions.md"
    ".cursor/rules/ai-logging.mdc"
)

Require-Path "ai-logs/README.md"
Require-Path "ai-logs/SESSION_TEMPLATE.md"
Require-Path "CLAUDE.md"
Require-Path "GEMINI.md"
Require-Path ".github/copilot-instructions.md"
Require-Path ".cursor/rules/ai-logging.mdc"

$memberGuideBaseline = $null
$memberGuideBaselinePath = $null

foreach ($member in $members) {
    $guide = "ai-logs/$($member.Slug)/BOT_INSTRUCTIONS.md"
    $sessionDirectory = "ai-logs/$($member.Slug)/sessions/.gitkeep"
    Require-Path $guide
    Require-Path $sessionDirectory
    Require-Text $guide $member.Name
    Require-Text $guide $member.Slug
    Require-Text $guide "sessions/"

    $fullGuidePath = Join-Path $root $guide
    if (Test-Path -LiteralPath $fullGuidePath -PathType Leaf) {
        $normalizedGuide = Get-Content -LiteralPath $fullGuidePath -Raw -Encoding UTF8
        $normalizedGuide = $normalizedGuide.Replace(
            $member.Name,
            "__MEMBER_NAME__"
        )
        $normalizedGuide = $normalizedGuide.Replace(
            $member.Slug,
            "__MEMBER_SLUG__"
        )
        $normalizedGuide = $normalizedGuide.Replace("`r`n", "`n")
        $normalizedGuide = $normalizedGuide.Replace("`r", "`n")

        if ($null -eq $memberGuideBaseline) {
            $memberGuideBaseline = $normalizedGuide
            $memberGuideBaselinePath = $guide
        }
        elseif (![string]::Equals(
            $memberGuideBaseline,
            $normalizedGuide,
            [System.StringComparison]::Ordinal
        )) {
            $failures.Add(
                "Member guide common body differs: $guide " +
                "(baseline: $memberGuideBaselinePath)"
            )
        }
    }
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

$expectedAgentsPrefix = @'
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
'@

Require-Prefix "AGENTS.md" $expectedAgentsPrefix
Require-Pattern "CLAUDE.md" "(?m)^[ \t]*@AGENTS\.md[ \t]*$" `
    "standalone AGENTS.md import"
Require-Pattern "GEMINI.md" "(?m)^[ \t]*@\./AGENTS\.md[ \t]*$" `
    "standalone AGENTS.md import"
Require-Text ".github/copilot-instructions.md" "AGENTS.md"
Require-Text ".github/copilot-instructions.md" "ai-logs/README.md"
Require-Text ".github/copilot-instructions.md" "mandatory"
Require-Pattern ".github/copilot-instructions.md" `
    "before\s+substantive work" "pre-substantive-work requirement"
Require-Pattern ".cursor/rules/ai-logging.mdc" `
    "\A---\n(?s:.*?)\n---(?:\n|$)" "MDC frontmatter"
Require-Pattern ".cursor/rules/ai-logging.mdc" `
    "(?m)^alwaysApply:[ \t]*true[ \t]*$" "always-applied rule"
Require-Text ".cursor/rules/ai-logging.mdc" "@AGENTS.md"
Require-Text ".cursor/rules/ai-logging.mdc" "@ai-logs/README.md"

if ($failures.Count -gt 0) {
    foreach ($failure in $failures) {
        [Console]::Error.WriteLine($failure)
    }
    exit 1
}

Write-Host "AI logging validation passed for $($members.Count) members and $($clientEntrypoints.Count) client entrypoints."
