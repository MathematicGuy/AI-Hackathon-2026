"""Golden eval runner: executes data/agent-eval/agent-golden-cases.jsonl
against the deterministic agent (Excel backend, no LLM, no network).

Each case is a scripted conversation with declarative expectations, so the
same file can later be imported into Langfuse as a dataset (judge-route
scoring is deferred until Langfuse keys are configured).
"""

import importlib
import json
from pathlib import Path

import pytest

from backend.app.agent.contracts import AgentState

CASES_PATH = Path("data") / "agent-eval" / "agent-golden-cases.jsonl"


def load_cases():
    lines = CASES_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


@pytest.fixture(scope="module")
def deps(tmp_path_factory):
    graph = importlib.import_module("backend.app.agent.graph")
    adapter = importlib.import_module(
        "backend.app.agent.catalog.dataset_adapter"
    ).ExcelDatasetAdapter()
    return graph.AgentDependencies(products=adapter.load())


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
async def test_golden_case(case, deps):
    graph = importlib.import_module("backend.app.agent.graph")
    state = AgentState()
    previous_presented: set[str] = set()
    for turn in case["turns"]:
        reply = await graph.run_turn(state, turn["user"], deps)
        expect = turn.get("expect")
        if not expect:
            previous_presented.update(reply.presented_ids)
            continue

        if "intent" in expect:
            assert reply.intent == expect["intent"], reply.text
        if "not_intent" in expect:
            assert reply.intent != expect["not_intent"], reply.text
        for fragment in expect.get("contains", []):
            assert fragment in reply.text, reply.text
        for fragment in expect.get("not_contains", []):
            assert fragment not in reply.text, reply.text
        if expect.get("no_products"):
            assert reply.presented_ids == []
        if expect.get("has_products"):
            assert reply.presented_ids, reply.text
        if "max_questions" in expect:
            assert reply.text.count("?") <= expect["max_questions"]
        if "flag" in expect:
            assert expect["flag"] in reply.flags
        if "state_flag" in expect:
            assert expect["state_flag"] in state.guardrail_flags
        if expect.get("verbatim_quote"):
            parts = reply.text.split('"')
            assert len(parts) >= 3, reply.text
            raw = "".join(d.raw_text for d in deps.corpus.documents)
            assert parts[1] in raw
        if expect.get("verbatim_body"):
            raw = "".join(d.raw_text for d in deps.corpus.documents)
            body = (
                reply.text.split("của bên em ạ:", 1)[-1]
                .rsplit("Anh/chị cần em", 1)[0]
                .strip()
            )
            assert len(body) > 60, reply.text
            assert body in raw
        if "need_category" in expect:
            assert state.need.category_code == expect["need_category"]
        if "need_budget_max" in expect:
            assert state.need.budget_max == expect["need_budget_max"]
        if "need_roles" in expect:
            assert state.need.requested_roles == expect["need_roles"]
        if "need_constraint_key" in expect:
            assert expect["need_constraint_key"] in state.need.attribute_constraints
        if expect.get("disjoint_from_previous"):
            assert previous_presented.isdisjoint(reply.presented_ids)
        previous_presented.update(reply.presented_ids)
