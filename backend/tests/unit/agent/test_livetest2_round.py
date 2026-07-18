"""Tests for the live-test 2 round: budget typo parsing, state-aware
fallback, most_expensive role, question-echo clarification, unavailable
products, asked-list reset fix, corpus hardening, feedback endpoint."""

import pytest
from fastapi.testclient import TestClient

from backend.app.agent.api import create_agent_app
from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, AgentUnderstanding, GenericNeed
from backend.app.agent.conversation.memory import apply_turn
from backend.app.agent.conversation.understand import (
    _parse_budget_vnd,
    fallback_understanding,
)
from backend.app.agent.graph import AgentDependencies, run_turn
from backend.app.agent.llm.client import resolve_llm_candidates
from backend.app.agent.policies.corpus import _trim_orphan_tail
from backend.app.agent.tools.suggest import suggest_products


def product(pid, code, price, *, gift=None, sale=None):
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="x",
        brand="B",
        brand_id="1",
        model_code=pid,
        sku=pid,
        attributes={},
        promotion=PromotionInfo(list_price=price, sale_price=sale, gift=gift),
    )


# --- budget parsing tolerates live-chat typos ---

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("tầm 20-30 trịu", (20_000_000, 30_000_000)),
        ("khoảng 25 trieu", (None, 25_000_000)),
        ("tầm 18-20 triệu", (18_000_000, 20_000_000)),
        ("dưới 15 củ", (None, 15_000_000)),
        ("tầm 12tr", (None, 12_000_000)),
    ],
)
def test_budget_parse_typo_units(text, expected):
    assert _parse_budget_vnd(text) == expected


# --- state-aware fallback: mid-flow follow-ups never dump the menu ---

def test_most_expensive_midflow_continues():
    result = fallback_understanding("máy đắt nhất đi em", active_category="72")
    assert result.intent == "more_recommendations"
    assert result.need_patch.requested_roles == ["most_expensive"]


def test_vague_product_reference_midflow_is_continuation():
    result = fallback_understanding("cái đó còn mẫu nào ngon hơn không", active_category="72")
    assert result.intent != "unsupported"


def test_no_category_still_unsupported():
    result = fallback_understanding("thời sự hôm nay có gì")
    assert result.intent == "unsupported"


# --- most_expensive suggestion role ---

def test_suggest_most_expensive_picks_top_price():
    pool = [product("a", "38", 5_000_000), product("b", "38", 25_000_000)]
    suggestions = suggest_products(pool, category_code="38", roles=["most_expensive"])
    assert suggestions.winners["most_expensive"].productidweb == "b"


# --- asked-list reset only after the cycle is spent ---

def test_active_cycle_not_reset_by_new_search():
    state = AgentState(need=GenericNeed(category_code="72"))
    state.asked_questions["72"] = ["purpose", "budget"]
    state.clarification_count["72"] = 1
    understanding = AgentUnderstanding(
        intent="new_search",
        confidence=0.3,
        need_patch=GenericNeed(usage_purpose="chơi game"),
    )
    apply_turn(state, understanding)
    assert state.asked_questions["72"] == ["purpose", "budget"]


def test_spent_cycle_is_reopened_by_new_search():
    state = AgentState(need=GenericNeed(category_code="72"))
    state.asked_questions["72"] = ["purpose", "budget", "priority"]
    state.clarification_count["72"] = 3
    understanding = AgentUnderstanding(
        intent="new_search",
        confidence=0.3,
        need_patch=GenericNeed(usage_purpose="đồ họa"),
    )
    apply_turn(state, understanding)
    assert state.asked_questions["72"] == []


# --- corpus: orphan enumeration tails are trimmed ---

def test_orphan_enum_tail_trimmed():
    chunk = "a. Đăng ký tài khoản, cấp tài khoản.\n\nb."
    assert _trim_orphan_tail(chunk) == "a. Đăng ký tài khoản, cấp tài khoản."


def test_content_tail_kept():
    chunk = "a. Đăng ký tài khoản.\nb. Xác thực khách hàng."
    assert _trim_orphan_tail(chunk) == chunk


# --- question echo → clarification, not policy, not captured ---

async def test_question_echo_explained_with_example():
    deps = AgentDependencies(products=[product("f1", "38", 10_000_000)])
    state = AgentState()
    await run_turn(state, "tôi muốn mua tủ lạnh", deps)
    reply = await run_turn(state, "mục đích sử dụng tủ lạnh á?", deps)
    assert reply.intent == "question_clarification"
    assert "ví dụ" in reply.text
    assert "xin lỗi" not in reply.text
    assert state.need.usage_purpose is None


# --- unavailable products answered honestly ---

async def test_laptop_honest_with_alternatives():
    deps = AgentDependencies(products=[product("f1", "38", 10_000_000)])
    reply = await run_turn(AgentState(), "có laptop không?", deps)
    assert "chưa kinh doanh" in reply.text
    assert "Máy tính để bàn" in reply.text


# --- gpt-4o-mini is the reasoning core in every key configuration ---

def test_openai_candidate_first():
    candidates = resolve_llm_candidates(
        {"OPENAI_API_KEY": "k1", "OPENROUTER_API_KEY": "k2", "MISTRAL_API_KEY": "k3"}
    )
    assert candidates[0].model == "gpt-4o-mini"
    assert "api.openai.com" in candidates[0].base_url
    assert len(candidates) == 3


def test_openrouter_runs_gpt4o_mini_not_default_model():
    # Cường's live setup: only the OpenRouter key is filled; DEFAULT_MODEL is
    # M1's deepseek route and must NOT leak into the agent.
    candidates = resolve_llm_candidates(
        {
            "OPENAI_API_KEY": "",
            "OPENROUTER_API_KEY": "k2",
            "MISTRAL_API_KEY": "",
            "DEFAULT_MODEL": "deepseek/deepseek-v4-flash",
        }
    )
    assert candidates[0].model == "openai/gpt-4o-mini"
    assert "openrouter" in candidates[0].base_url


def test_extractor_coerces_int_category_code():
    from backend.app.agent.llm.client import _extract_json

    payload = _extract_json(
        '{"intent": "new_search", "confidence": "0.9", '
        '"need_patch": {"category_code": 38, "budget_max": "15000000"}}'
    )
    assert payload["need_patch"]["category_code"] == "38"
    assert payload["need_patch"]["budget_max"] == 15_000_000
    assert payload["confidence"] == 0.9


# --- feedback endpoint records like/dislike ---

def test_feedback_endpoint_records():
    deps = AgentDependencies(products=[product("f1", "38", 10_000_000)])
    client = TestClient(create_agent_app(deps))
    response = client.post(
        "/api/v1/agent/feedback",
        json={"session_id": "s1", "message_index": 2, "rating": "like"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"
    bad = client.post(
        "/api/v1/agent/feedback",
        json={"session_id": "s1", "message_index": 0, "rating": "meh"},
    )
    assert bad.status_code == 422
