$ErrorActionPreference = "Stop"

$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$safeGitDirectory = $root.Replace("\", "/")
$failures = [System.Collections.Generic.List[string]]::new()

function Add-Failure([string]$Message) {
    $failures.Add($Message)
}

function Get-ExtendedPath([string]$Path) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if ($fullPath.StartsWith("\\?\")) {
        return $fullPath
    }
    if ($fullPath.StartsWith("\\")) {
        return "\\?\UNC\" + $fullPath.Substring(2)
    }
    return "\\?\" + $fullPath
}

function Get-RepositoryPath([string]$RelativePath) {
    return [System.IO.Path]::GetFullPath((Join-Path $root $RelativePath))
}

function Test-RepositoryPath([string]$RelativePath) {
    $extendedPath = Get-ExtendedPath (Get-RepositoryPath $RelativePath)
    return [System.IO.File]::Exists($extendedPath) -or
        [System.IO.Directory]::Exists($extendedPath)
}

function Read-RepositoryText([string]$RelativePath) {
    $extendedPath = Get-ExtendedPath (Get-RepositoryPath $RelativePath)
    return [System.IO.File]::ReadAllText(
        $extendedPath,
        [System.Text.Encoding]::UTF8
    )
}

function Require-File([string]$RelativePath) {
    $extendedPath = Get-ExtendedPath (Get-RepositoryPath $RelativePath)
    if (![System.IO.File]::Exists($extendedPath)) {
        Add-Failure "Missing required file: $RelativePath"
    }
}

function Forbid-Path([string]$RelativePath) {
    if (Test-RepositoryPath $RelativePath) {
        Add-Failure "Legacy path must be absent: $RelativePath"
    }
}

function Require-Text(
    [string]$RelativePath,
    [string]$ExpectedText,
    [string]$Description
) {
    if (!(Test-RepositoryPath $RelativePath)) {
        Add-Failure "Cannot inspect missing file: $RelativePath"
        return
    }

    $content = Read-RepositoryText $RelativePath
    if (!$content.Contains($ExpectedText)) {
        Add-Failure "Missing $Description in ${RelativePath}: $ExpectedText"
    }
}

function Require-OrderedText(
    [string]$RelativePath,
    [string[]]$OrderedTokens
) {
    if (!(Test-RepositoryPath $RelativePath)) {
        Add-Failure "Cannot inspect missing file: $RelativePath"
        return
    }

    $content = Read-RepositoryText $RelativePath
    $previousIndex = -1
    foreach ($token in $OrderedTokens) {
        $index = $content.IndexOf(
            $token,
            [System.StringComparison]::Ordinal
        )
        if ($index -lt 0) {
            Add-Failure "Missing ordered read-gate token in ${RelativePath}: $token"
            return
        }
        if ($index -le $previousIndex) {
            Add-Failure "Read-gate order is invalid in ${RelativePath}: $token"
            return
        }
        $previousIndex = $index
    }
}

function Get-NormalizedRepositoryFiles(
    [string[]]$Arguments,
    [string]$Description
) {
    $output = @(& rg @Arguments 2>$null)
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
        Add-Failure "Unable to enumerate $Description with rg."
        return @()
    }
    return @($output | ForEach-Object {
        $_.Replace("\", "/")
    } | Sort-Object)
}

function Test-IgnoredByGit([string]$RelativePath) {
    & git -c "safe.directory=$safeGitDirectory" check-ignore --quiet -- `
        $RelativePath
    return $LASTEXITCODE -eq 0
}

$expectedRootMarkdown = @(
    "AGENTS.md"
    "CLAUDE.md"
    "GEMINI.md"
    "PROJECT_MANAGEMENT.md"
    "README.md"
) | Sort-Object

$actualRootMarkdown = @(
    Get-ChildItem -LiteralPath $root -File -Filter "*.md" |
        ForEach-Object { $_.Name } |
        Sort-Object
)

if (($actualRootMarkdown -join "`n") -cne
    ($expectedRootMarkdown -join "`n")) {
    Add-Failure (
        "Root Markdown allowlist mismatch. Expected: " +
        ($expectedRootMarkdown -join ", ") +
        ". Actual: " +
        ($actualRootMarkdown -join ", ")
    )
}

$requiredFiles = @(
    "docs/team/README.md"
    "docs/team/now/README.md"
    "docs/team/now/THANH-NOW.md"
    "docs/team/now/USER1-NOW.md"
    "docs/team/now/USER2-NOW.md"
    "docs/product/requirements/README.md"
    "docs/product/requirements/air-conditioner-advisor-m1-prd.md"
    "docs/product/architecture/README.md"
    "docs/product/architecture/air-conditioner-advisor-m1.md"
    "docs/product/discovery/README.md"
    "docs/product/discovery/air-conditioner-advisor-jtbd.md"
    "docs/references/README.md"
    "docs/references/partner-briefs/README.md"
    "docs/references/partner-briefs/dien-may-xanh-vietnam-innovation-challenge-2026.md"
    ".env.example"
)

foreach ($requiredFile in $requiredFiles) {
    Require-File $requiredFile
}

$legacyPaths = @(
    "THANH-NOW.md"
    "USER1-NOW.md"
    "USER2-NOW.md"
    "WORKFLOW-MVP(4).md"
    "ARCHITECTURE.md"
    "JTBD_Completed.md"
    "resources/Điện-Máy-Xanh.md"
)

foreach ($legacyPath in $legacyPaths) {
    Forbid-Path $legacyPath
}

$registryRequirements = @(
    @{ Text = "## Authority Registry"; Description = "authority registry heading" }
    @{ Text = "Purpose"; Description = "purpose field" }
    @{ Text = "Authority"; Description = "authority field" }
    @{ Text = "Lifecycle"; Description = "lifecycle field" }
    @{ Text = "Owner"; Description = "owner field" }
    @{ Text = "Read trigger"; Description = "read-trigger field" }
    @{ Text = "## Conflict Precedence"; Description = "conflict precedence" }
    @{ Text = "docs/team/now/"; Description = "tracker registry entry" }
    @{ Text = "docs/product/requirements/"; Description = "requirements registry entry" }
    @{ Text = "docs/product/architecture/"; Description = "product architecture registry entry" }
    @{ Text = "docs/product/discovery/"; Description = "product discovery registry entry" }
    @{ Text = "docs/references/partner-briefs/"; Description = "partner brief registry entry" }
    @{ Text = "docs/superpowers/"; Description = "legacy provenance registry entry" }
    @{ Text = "No new files"; Description = "legacy-folder creation prohibition" }
)

foreach ($requirement in $registryRequirements) {
    Require-Text "docs/README.md" $requirement.Text $requirement.Description
}

Require-OrderedText "docs/README.md" @(
    "## Mandatory Read Order"
    "1. Read the AI logging policy"
    "2. Classify the request as read-only or change work."
    "3. Read this authority registry."
    "4. Always read"
    "5. For changes, bootstrap Harness"
    "6. Apply the bounded retrieval rules"
    "7. Read the applicable product contract"
    "8. Read requirements, product architecture"
    "## Conflict Precedence"
    "1. The current human request controls"
    '2. `AGENTS.md` controls'
    '3. `ai-logs/README.md` controls'
    "4. The accepted product contract controls"
    "5. Requirements control"
    "6. Product architecture must conform"
    "7. A registered story controls"
    "8. The Harness matrix controls"
    "9. The mapped tracker controls"
    '10. `PROJECT_MANAGEMENT.md`'
)

Require-OrderedText "AGENTS.md" @(
    "<!-- AI-LOGGING:BEGIN -->"
    "ai-logs/README.md"
    "Classify the request as read-only or change work."
    "docs/README.md"
    "docs/team/now/README.md"
    "<!-- HARNESS:BEGIN -->"
    "<!-- HARNESS:END -->"
    "<!-- BOUNDED-CONTEXT:BEGIN -->"
    "Applicable bounded-context rules."
    "The accepted product contract"
    "The applicable PRD."
    "Product architecture."
    "The registered story packet and implementation plan."
    "Only then, the relevant code."
    "<!-- BOUNDED-CONTEXT:END -->"
)

foreach ($blockingField in @(
    "identity"
    "tracker ownership"
    "story ID"
    "dependencies"
    "branch/worktree"
    "Harness matrix"
    "file ownership"
)) {
    Require-Text "AGENTS.md" $blockingField "implementation blocking field"
}

$trackerFiles = Get-NormalizedRepositoryFiles @(
    "--files"
    "-g"
    "*-NOW.md"
) "team trackers"

$expectedTrackerFiles = @(
    "docs/team/now/THANH-NOW.md"
    "docs/team/now/USER1-NOW.md"
    "docs/team/now/USER2-NOW.md"
) | Sort-Object

if (($trackerFiles -join "`n") -cne ($expectedTrackerFiles -join "`n")) {
    Add-Failure (
        "Tracker placement mismatch. Expected: " +
        ($expectedTrackerFiles -join ", ") +
        ". Actual: " +
        ($trackerFiles -join ", ")
    )
}

if (Test-RepositoryPath "docs/team/now/README.md") {
    $trackerIndex = Read-RepositoryText "docs/team/now/README.md"
    $identitySection = [regex]::Match(
        $trackerIndex,
        "(?ms)^## Identity Map\s*(.*?)(?=^## |\z)"
    )
    if (!$identitySection.Success) {
        Add-Failure "Tracker index must contain a parseable Identity Map."
    }
    else {
        $tableLines = @(
            $identitySection.Groups[1].Value -split "`r?`n" |
                Where-Object { $_.Trim().StartsWith("|") }
        )
        $identityRows = @($tableLines | Select-Object -Skip 2)
        $expectedTrackerRows = [ordered]@{
            THANH = @{
                Identity = "dinh-nhat-thanh"
                Tracker = "THANH-NOW.md"
            }
            USER1 = @{
                Identity = "Unassigned"
                Tracker = "USER1-NOW.md"
            }
            USER2 = @{
                Identity = "Unassigned"
                Tracker = "USER2-NOW.md"
            }
        }

        if ($identityRows.Count -ne $expectedTrackerRows.Count) {
            Add-Failure (
                "Tracker identity map must contain exactly " +
                "$($expectedTrackerRows.Count) data rows."
            )
        }

        $seenAliases = @{}
        $seenTrackerTargets = @{}
        $seenAssignedIdentities = @{}
        foreach ($identityRow in $identityRows) {
            $cells = @(
                $identityRow.Trim().Trim([char[]]'|').Split("|") |
                    ForEach-Object { $_.Trim() }
            )
            if ($cells.Count -ne 4) {
                Add-Failure "Malformed tracker identity row: $identityRow"
                continue
            }

            $alias = $cells[0]
            $identity = $cells[1]
            $trackerCell = $cells[2]
            if (!$expectedTrackerRows.Contains($alias)) {
                Add-Failure "Unexpected tracker alias: $alias"
                continue
            }
            if ($seenAliases.ContainsKey($alias)) {
                Add-Failure "Duplicate tracker alias row: $alias"
                continue
            }
            $seenAliases[$alias] = $true

            $expectedRow = $expectedTrackerRows[$alias]
            if ($identity -cne $expectedRow.Identity) {
                Add-Failure (
                    "Tracker alias $alias must map to " +
                    "$($expectedRow.Identity), not $identity."
                )
            }

            $targetPattern = "\]\(" +
                [regex]::Escape($expectedRow.Tracker) + "\)"
            if (![regex]::IsMatch($trackerCell, $targetPattern)) {
                Add-Failure (
                    "Tracker alias $alias must link to " +
                    "$($expectedRow.Tracker)."
                )
            }
            if ($seenTrackerTargets.ContainsKey($expectedRow.Tracker)) {
                Add-Failure (
                    "Duplicate tracker target: $($expectedRow.Tracker)"
                )
            }
            $seenTrackerTargets[$expectedRow.Tracker] = $true

            if ($identity -cne "Unassigned") {
                if ($seenAssignedIdentities.ContainsKey($identity)) {
                    Add-Failure "Duplicate assigned tracker identity: $identity"
                }
                $seenAssignedIdentities[$identity] = $true
            }
        }

        foreach ($expectedAlias in $expectedTrackerRows.Keys) {
            if (!$seenAliases.ContainsKey($expectedAlias)) {
                Add-Failure "Missing tracker identity row: $expectedAlias"
            }
        }
    }
}

$storyOwners = @{}
$fileOwners = @{}
foreach ($trackerFile in $expectedTrackerFiles) {
    if (!(Test-RepositoryPath $trackerFile)) {
        continue
    }

    $trackerContent = Read-RepositoryText $trackerFile
    $storySection = [regex]::Match(
        $trackerContent,
        "(?ms)^## Ownership boundary\s*(.*?)(?=^## |\z)"
    )
    if (!$storySection.Success) {
        Add-Failure "Missing Ownership boundary section: $trackerFile"
        continue
    }

    $stories = @(
        [regex]::Matches(
            $storySection.Groups[1].Value,
            "(?m)^\d+\.\s+(US-\d{3})\b"
        ) |
            ForEach-Object { $_.Groups[1].Value } |
            Sort-Object -Unique
    )
    if ($stories.Count -eq 0) {
        Add-Failure "No parseable owned stories in $trackerFile"
    }
    foreach ($story in $stories) {
        if (!$storyOwners.ContainsKey($story)) {
            $storyOwners[$story] = @()
        }
        $storyOwners[$story] += $trackerFile
    }

    $fileSection = [regex]::Match(
        $trackerContent,
        "(?ms)^## File boundary\s*(.*?)(?=^## |\z)"
    )
    if (!$fileSection.Success) {
        Add-Failure "Missing File boundary section: $trackerFile"
        continue
    }

    $ownedFiles = @(
        [regex]::Matches(
            $fileSection.Groups[1].Value,
            '(?m)^\s*-\s+`(?<path>[^`]+)`'
        ) |
            ForEach-Object {
                $_.Groups["path"].Value.Replace("\", "/").TrimEnd("/")
            } |
            Sort-Object -Unique
    )
    if ($ownedFiles.Count -eq 0) {
        Add-Failure "No parseable owned files in $trackerFile"
    }
    foreach ($ownedFile in $ownedFiles) {
        if (!$fileOwners.ContainsKey($ownedFile)) {
            $fileOwners[$ownedFile] = @()
        }
        $fileOwners[$ownedFile] += $trackerFile
    }

    foreach ($trackerLine in ($trackerContent -split "`r?`n")) {
        if ($trackerLine.Contains("docs/superpowers/") -and
            $trackerLine -notmatch "(?i)legacy provenance") {
            Add-Failure (
                "Active tracker treats legacy docs/superpowers as authority " +
                "in ${trackerFile}: $trackerLine"
            )
        }
    }
}

foreach ($story in $storyOwners.Keys) {
    if ($storyOwners[$story].Count -gt 1) {
        Add-Failure (
            "Duplicate tracker ownership for ${story}: " +
            ($storyOwners[$story] -join ", ")
        )
    }
}

foreach ($ownedFile in $fileOwners.Keys) {
    if ($fileOwners[$ownedFile].Count -gt 1) {
        Add-Failure (
            "Duplicate tracker file ownership for ${ownedFile}: " +
            ($fileOwners[$ownedFile] -join ", ")
        )
    }
}

$expectedEnvironment = [ordered]@{
    TEAM_MEMBER = ""
    OPENAI_API_KEY = ""
    OPENROUTER_API_KEY = ""
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    LANGFUSE_PUBLIC_KEY = ""
    LANGFUSE_SECRET_KEY = ""
    LANGFUSE_BASE_URL = "https://cloud.langfuse.com"
    NEXT_PUBLIC_ADVISOR_MODE = "mock"
    NEXT_PUBLIC_ADVISOR_API_URL = "http://127.0.0.1:8000"
}

if (Test-RepositoryPath ".env.example") {
    $environmentValues = @{}
    $environmentLines = (Read-RepositoryText ".env.example") -split "`r?`n"
    foreach ($line in $environmentLines) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith("#")) {
            continue
        }
        if ($trimmed -notmatch "^([A-Z][A-Z0-9_]*)=(.*)$") {
            Add-Failure "Invalid .env.example assignment: $trimmed"
            continue
        }
        $key = $matches[1]
        if ($environmentValues.ContainsKey($key)) {
            Add-Failure "Duplicate .env.example key: $key"
        }
        $environmentValues[$key] = $matches[2]
    }

    foreach ($key in $expectedEnvironment.Keys) {
        if (!$environmentValues.ContainsKey($key)) {
            Add-Failure "Missing .env.example key: $key"
            continue
        }
        if ($environmentValues[$key] -cne $expectedEnvironment[$key]) {
            Add-Failure (
                "Unexpected .env.example value for ${key}. " +
                "Expected '$($expectedEnvironment[$key])'."
            )
        }
    }

    foreach ($key in $environmentValues.Keys) {
        if (!$expectedEnvironment.Contains($key)) {
            Add-Failure "Unexpected .env.example key: $key"
        }
    }
}

foreach ($ignoredEnvironmentPath in @(
    ".env"
    ".env.local"
    "backend/.env"
    "backend/.env.production"
)) {
    if (!(Test-IgnoredByGit $ignoredEnvironmentPath)) {
        Add-Failure "$ignoredEnvironmentPath must be ignored by Git."
    }
}
foreach ($trackableEnvironmentPath in @(
    ".env.example"
    ".env.local.example"
    "backend/.env.example"
    "backend/.env.test.example"
)) {
    if (Test-IgnoredByGit $trackableEnvironmentPath) {
        Add-Failure "$trackableEnvironmentPath must remain trackable."
    }
}
$trackedEnvironmentExample = @(
    & git -c "safe.directory=$safeGitDirectory" ls-files -- .env.example `
        2>$null
)
if ($trackedEnvironmentExample.Count -ne 1 -or
    $trackedEnvironmentExample[0] -cne ".env.example") {
    Add-Failure ".env.example must be tracked exactly once."
}
$trackedEnvironmentFiles = @(
    & git -c "safe.directory=$safeGitDirectory" ls-files -- .env 2>$null
)
if ($trackedEnvironmentFiles.Count -gt 0) {
    Add-Failure ".env must never be tracked."
}

$expectedLegacyArtifacts = @(
    "docs/superpowers/plans/2026-07-17-ai-session-logging.md"
    "docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md"
    "docs/superpowers/plans/2026-07-17-parallel-critical-path-ledgers.md"
    "docs/superpowers/specs/2026-07-17-ai-session-logging-design.md"
    "docs/superpowers/specs/2026-07-17-frontend-mvp-design.md"
    "docs/superpowers/specs/2026-07-17-parallel-critical-path-workstreams-design.md"
) | Sort-Object

$actualLegacyArtifacts = Get-NormalizedRepositoryFiles @(
    "--files"
    "docs/superpowers"
) "legacy docs/superpowers artifacts"

if (($actualLegacyArtifacts -join "`n") -cne
    ($expectedLegacyArtifacts -join "`n")) {
    Add-Failure (
        "docs/superpowers is frozen. Expected only: " +
        ($expectedLegacyArtifacts -join ", ") +
        ". Actual: " +
        ($actualLegacyArtifacts -join ", ")
    )
}

foreach ($legacyArtifact in $expectedLegacyArtifacts) {
    Require-Text $legacyArtifact "Legacy provenance artifact" `
        "legacy provenance marker"
}

$markdownFiles = Get-NormalizedRepositoryFiles @(
    "--files"
    "--hidden"
    "-g"
    "*.md"
    "-g"
    "!.git/**"
    "-g"
    "!.worktrees/**"
    "-g"
    "!node_modules/**"
    "-g"
    "!.venv/**"
) "Markdown files"

$migrationRecordPrefixes = @(
    "docs/decisions/0011-documentation-authority-and-placement.md"
    "docs/stories/epics/E05-repository-governance/" +
        "US-122-documentation-governance/"
)

$activeTextFiles = Get-NormalizedRepositoryFiles @(
    "--files"
    "--hidden"
    "-g"
    "*.md"
    "-g"
    "*.mdc"
    "-g"
    "*.ps1"
    "-g"
    "*.sh"
    "-g"
    "*.py"
    "-g"
    "*.toml"
    "-g"
    "*.yml"
    "-g"
    "*.yaml"
    "-g"
    "*.json"
    "-g"
    "*.jsonl"
    "-g"
    "*.sql"
    "-g"
    "*.txt"
    "-g"
    "*.rs"
    "-g"
    "*.ts"
    "-g"
    "*.tsx"
    "-g"
    "*.js"
    "-g"
    "*.jsx"
    "-g"
    "*.css"
    "-g"
    "*.html"
    "-g"
    ".gitignore"
    "-g"
    "*.example"
    "-g"
    "!.git/**"
    "-g"
    "!.worktrees/**"
    "-g"
    "!node_modules/**"
    "-g"
    "!.venv/**"
) "active text and configuration files"

$activeConsumerFiles = @($activeTextFiles | Where-Object {
    $path = $_
    $isExcluded = $path -match "^ai-logs/[^/]+/sessions/" -or
        $path -eq "scripts/validate-repository-governance.ps1" -or
        $path -eq $migrationRecordPrefixes[0] -or
        $path.StartsWith($migrationRecordPrefixes[1])
    !$isExcluded
})

$linkMarkdownFiles = @($markdownFiles | Where-Object {
    $_ -notmatch "^ai-logs/[^/]+/sessions/"
})

$legacyReferenceTokens = @(
    "WORKFLOW-MVP(4).md"
    "JTBD_Completed.md"
    "resources/Điện-Máy-Xanh.md"
)

foreach ($consumerFile in $activeConsumerFiles) {
    $content = Read-RepositoryText $consumerFile

    if (!$consumerFile.StartsWith("docs/team/now/")) {
        foreach ($trackerName in @(
            "THANH-NOW.md"
            "USER1-NOW.md"
            "USER2-NOW.md"
        )) {
            $staleTrackerPattern =
                "(?<!docs/team/now/)" + [regex]::Escape($trackerName)
            if ([regex]::IsMatch($content, $staleTrackerPattern)) {
                Add-Failure (
                    "Stale tracker reference in ${consumerFile}: " +
                    $trackerName
                )
            }
        }
    }

    foreach ($legacyToken in $legacyReferenceTokens) {
        if ($content.Contains($legacyToken)) {
            Add-Failure (
                "Stale legacy reference in ${consumerFile}: $legacyToken"
            )
        }
    }

    if ([regex]::IsMatch(
        $content,
        '(?<![A-Za-z0-9_./\\-])ARCHITECTURE\.md'
    )) {
        Add-Failure "Stale root architecture reference in $consumerFile."
    }
}

foreach ($markdownFile in $linkMarkdownFiles) {
    $content = Read-RepositoryText $markdownFile

    $linkMatches = [regex]::Matches(
        $content,
        "(?:!)?\[[^\]]*\]\((?<target><[^>]+>|[^)\s]+)"
    )
    foreach ($linkMatch in $linkMatches) {
        $target = $linkMatch.Groups["target"].Value.Trim("<", ">")
        if ($target.Length -eq 0 -or $target.StartsWith("#") -or
            $target -match "^[A-Za-z][A-Za-z0-9+.-]*:") {
            continue
        }

        $target = ($target -split "[?#]", 2)[0]
        $target = [System.Uri]::UnescapeDataString($target)
        if ($target.Length -eq 0) {
            continue
        }

        if ($target.StartsWith("/")) {
            $resolvedPath = Get-RepositoryPath $target.TrimStart("/")
        }
        else {
            $sourcePath = Get-RepositoryPath $markdownFile
            $sourceDirectory = [System.IO.Path]::GetDirectoryName($sourcePath)
            $resolvedPath = [System.IO.Path]::GetFullPath(
                (Join-Path $sourceDirectory $target)
            )
        }

        $extendedResolvedPath = Get-ExtendedPath $resolvedPath
        if (![System.IO.File]::Exists($extendedResolvedPath) -and
            ![System.IO.Directory]::Exists($extendedResolvedPath)) {
            Add-Failure (
                "Broken local Markdown link in ${markdownFile}: $target"
            )
        }
    }
}

$aiLoggingValidator = Join-Path $PSScriptRoot "validate-ai-logging.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $aiLoggingValidator
if ($LASTEXITCODE -ne 0) {
    Add-Failure "AI logging validation failed."
}

if ($failures.Count -gt 0) {
    foreach ($failure in $failures) {
        [Console]::Error.WriteLine($failure)
    }
    exit 1
}

Write-Host (
    "Repository governance validation passed: root allowlist, document " +
    "authority, tracker ownership, Markdown links, AI logging, and " +
    "environment safety are consistent."
)
