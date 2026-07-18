---
name: setup-template
description: Bootstrap a project from the AI Hackathon template without copying repository history, caches, or secrets. Use when the user asks to initialize, sync, or adopt the shared hackathon template.
argument-hint: "Target directory and the template areas to apply"
---

# Set Up AI Hackathon Template

Apply the reusable project baseline from:

`E:\VIN-INTERNSHIP\AI-HACKATHON-TEMPLATE`

Use this skill when a project needs the template's operating conventions, docs, scripts, and starter structure. Select one mode before copying:

- **New-repository mode:** the target is empty or contains only Git metadata. Create the complete reusable project scaffold described below.
- **Existing-repository mode:** the target already contains project files. Apply only selected material and never overwrite it wholesale.

## 1. Inspect before changing anything

1. Confirm the target directory. If the user did not name one, use the current workspace.
2. Inspect the target's Git state and top-level layout, then select New-repository or Existing-repository mode.
3. In Existing-repository mode, read the target's `AGENTS.md`, `README.md`, and `.gitignore` before making changes.
4. Inspect the corresponding template files and produce a short copy plan: files to add, files that would conflict, and files intentionally excluded.
5. Preserve all pre-existing target work. Never replace a non-identical file without the user's explicit approval.

## 2. Copy only reusable source material

In New-repository mode, create the full reusable scaffold:

- `.agents/skills/` and `.agents/handoffs/` conventions
- `docs/` templates, planning guides, harness documentation, and contracts
- `scripts/`, including the Harness bootstrap and codebase-memory verification scripts
- `.gitattributes`, `.gitignore`, `Makefile`, `ruff.toml`, and other stack-neutral project configuration
- the root Markdown boilerplates listed below

Create these root Markdown files from their matching template boilerplates:

- `AGENTS.md`
- `docs/product/architecture/air-conditioner-advisor-m1.md`
- `HACKATHON_RUNBOOK.md`
- `JTBD.md`
- `JUDGING.md`
- `NOW.md`
- `OWNERS.md`
- `PROJECT_MANAGEMENT.md`
- `README.md`
- `WORKFLOW-MVP.md`

Keep the document structure and general instructions, but replace template-project-specific facts with explicit `TODO` placeholders before declaring the new repository ready. Do not copy `update-report.md`; it is a generated status artifact, not boilerplate.

In Existing-repository mode, the default candidates are:

- selected project instructions from `AGENTS.md`
- `.agents/skills/` and `.agents/handoffs/` conventions
- `docs/` templates and planning guides
- `scripts/` and other source-controlled helper files
- starter configuration such as `.gitignore`, `Makefile`, `ruff.toml`, or `requirements.txt`, only when compatible with the target stack

Do not copy any of the following:

- `.git/`, `.venv/`, caches, build outputs, local databases, or generated reports
- `.env` or any file containing credentials, tokens, personal data, or machine-specific settings
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.deepeval/`, `.tokensave/`, `.wgm/`, or `.archives/`
- template application code, tests, or dependencies unless the user explicitly asks to adopt them

## 3. Set up codebase-memory MCP

Before doing code discovery, check whether `codebase-memory-mcp` is available. If it is absent, install it from the official installer:

```powershell
& ([scriptblock]::Create((irm "https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.ps1"))) --skip-config
```

Then index the target repository and persist the graph artifact:

```powershell
codebase-memory-mcp cli index_repository --repo-path $PWD.Path --persistence true
```

Use the template's `scripts/verify-codebase-mcp.ps1` when it has been copied to the target to verify the index and the `.gitattributes`/`.gitignore` configuration. Keep `.codebase-memory/graph.db.zst` when the project deliberately shares its graph artifact; do not treat the entire `.codebase-memory/` directory as template source material.

## 4. Set up Repository Harness for an existing project

If the target already contains `AGENTS.md`, install or merge the Repository Harness in merge mode so the project's instructions are preserved. Use the template-pinned installer command:

```powershell
& ([scriptblock]::Create((irm "https://raw.githubusercontent.com/hoangnb24/repository-harness/harness-cli-v0.1.14/scripts/install-harness.ps1"))) `
  -Merge -UpgradeCli -Ref harness-cli-v0.1.14 -Yes
```

After the installer completes, read the resulting `AGENTS.md` and verify it retained the target's instructions. Then run:

```powershell
.\scripts\bootstrap-harness.ps1
.\scripts\bin\harness-cli.exe --version
```

Do not run the installer without the `-Merge` flag in a project that already has `AGENTS.md`.

## 5. Handle conflicts deliberately

- Add missing files directly when they are reusable and do not contain secrets.
- For an existing target file that differs from the template, show the relevant difference and ask whether to merge, replace, or skip it.
- Never copy the template's Git history or initialize a repository unless the user explicitly requests it.
- Keep project-specific commands, stack details, and conventions in the target's `AGENTS.md`; do not leave template `TODO` placeholders where target facts are known.

## 6. Verify and report

1. List the files actually added or changed.
2. Confirm excluded sensitive and generated paths were not copied.
3. Confirm `codebase-memory-mcp` indexed the target successfully and report whether its graph artifact is shared or local-only.
4. When Repository Harness was installed, confirm its CLI version and that the pre-existing `AGENTS.md` instructions remain intact.
5. Run the lightest relevant verification for copied scripts or configuration.
6. Report conflicts that were skipped and any target-specific follow-up needed to complete the setup.
