# AI Product Comparison Advisor

This repository contains the Milestone 1 air-conditioner decision-support
advisor, its deterministic test fixtures, and the repository Harness used to
coordinate AI-assisted development.

The current backend foundation defines the accepted request, response, product,
state, catalog, and graph contracts. Product work is story-gated and uses
synthetic Milestone 1 data; the repository does not claim that those fixtures
are live Điện Máy XANH catalog facts.

## Start Here

Human navigation:

- [Documentation authority registry](docs/README.md)
- [Milestone overview](PROJECT_MANAGEMENT.md)
- [Accepted product contract](docs/product/air-conditioner-advisor-m1-contract.md)
- [Product requirements](docs/product/requirements/air-conditioner-advisor-m1-prd.md)
- [Product architecture](docs/product/architecture/air-conditioner-advisor-m1.md)
- [Story index](docs/stories/README.md)
- [Active workstream trackers](docs/team/now/README.md)

Coding agents must start with [AGENTS.md](AGENTS.md). It requires identity and
AI-log preflight, documentation and tracker checks, and then the appropriate
Harness workflow before implementation.

## Repository Layout

```text
ai-logs/                     AI session policy, member guides, and logs
backend/                     Python application contracts and tests
data/aircon-m1-test-data/    Synthetic Milestone 1 fixtures
docs/
  product/                   Product contract, requirements, architecture, discovery
  stories/                   Bounded story packets and evidence
  team/now/                  Parallel workstream ownership and coordination
  decisions/                 Accepted durable decisions
  references/                Partner-provided source material
scripts/                     Harness and repository validation tools
```

Only `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, and
`PROJECT_MANAGEMENT.md` are allowed as root Markdown files. The placement and
conflict rules for every other document are defined in
[docs/README.md](docs/README.md).

## Local Environment

Copy `.env.example` to `.env` and fill only the values needed by your local
task. `.env` files are ignored; example templates remain trackable. Never
commit, print, or copy credentials into AI logs.

The environment template documents planned provider and frontend interfaces.
It does not imply that every variable is already consumed by application code,
and this repository does not automatically load `.env` during validation.
Provider variable conventions follow the official
[OpenAI quickstart](https://platform.openai.com/docs/quickstart/make-your-first-api-request),
[OpenRouter authentication reference](https://openrouter.ai/docs/api/reference/authentication),
and
[Langfuse SDK guidance](https://langfuse.com/docs/observability/sdk/troubleshooting-and-faq).

## Validation

The project requires Python 3.12 or newer. Run the isolated regression suite
without loading local environment files:

```powershell
uv run --no-project --isolated --python 3.12 --with-editable ".[test]" --no-env-file python -m pytest -q
```

Validate repository documentation, tracker ownership, AI logging, local links,
and environment safety:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-repository-governance.ps1
```

For Harness commands and bootstrap details, see
[scripts/README.md](scripts/README.md) and [docs/HARNESS.md](docs/HARNESS.md).
