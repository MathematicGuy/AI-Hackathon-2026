$ErrorActionPreference = "Stop"

& uv run --no-project --isolated --python 3.12 --with-editable ".[test]" --no-env-file python -m pytest backend/tests/contract/test_agent_api_contract.py backend/tests/unit/agent/test_presentation.py -q
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& npm --prefix frontend run test
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& npm --prefix frontend run lint
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& npm --prefix frontend run typecheck
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& npm --prefix frontend run build
exit $LASTEXITCODE
