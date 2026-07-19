"""Tests for live-test round 4: short-message flow, tool-driven compare,
budget clear, JSON session persistence, and determinism."""

import json

import pytest

from backend.app.agent.api import _load_session, _persist_session
from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, AgentUnderstanding, GenericNeed
from backend.app.agent.conversation.memory import apply_turn
from backend.app.agent.conversation.understand import (
    _augment_understanding,
    fallback_understanding,
)
from backend.app.agent.graph import AgentDependencies, run_turn


def product(pid, code, price, sale=None, attrs=None):
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="x",
        brand="B",
        brand_id="1",
        model_code=pid,
        sku=pid,
        attributes=attrs or {},
        promotion=PromotionInfo(list_price=price, sale_price=sale, gift=None),
    )


# --- bare agreement tokens never fall to unsupported ---

@pytest.mark.parametrize("token", ["ok", "ừ", "vâng", "OK", "được"])
def test_bare_agreement_is_smalltalk(token):
    assert fallback_understanding(token).intent == "smalltalk"


async def test_ok_midflow_continues_consultation():
    deps = AgentDependencies(products=[product("f1", "38", 10_000_000)])
    state = AgentState(need=GenericNeed(category_code="38"))
    reply = await run_turn(state, "ok", deps)
    assert "không xử lý" not in reply.text
    assert reply.intent in ("smalltalk", "new_search")


# --- compare fetches its own candidates ---

def _aircon_pool():
    return [
        product("cheap", "36", 8_000_000, attrs={"Độ ồn": "45 dB"}),
        product("mid", "36", 10_000_000, sale=9_000_000, attrs={"Độ ồn": "38 dB"}),
        product("deep", "36", 12_000_000, sale=9_500_000, attrs={"Độ ồn": "40 dB"}),
        product("top", "36", 20_000_000, attrs={"Độ ồn": "35 dB"}),
    ]


async def test_compare_cheapest_pair_fetched():
    deps = AgentDependencies(products=_aircon_pool())
    state = AgentState(need=GenericNeed(category_code="36"))
    reply = await run_turn(state, "so sánh 2 mẫu rẻ nhất đi", deps)
    assert reply.intent == "compare_products"
    assert set(reply.presented_ids or state.last_presented_ids) == {"cheap", "mid"}
    assert "so sánh" in reply.text.lower()


async def test_compare_featured_prefers_deep_discounts():
    deps = AgentDependencies(products=_aircon_pool())
    state = AgentState(need=GenericNeed(category_code="36"))
    await run_turn(state, "so sánh 2 mẫu nổi bật", deps)
    # mid: 10->9 (10%), deep: 12->9.5 (~21%) — the two discounted models win.
    assert set(state.last_presented_ids) == {"mid", "deep"}


async def test_compare_without_category_asks_for_category():
    deps = AgentDependencies(products=_aircon_pool())
    state = AgentState()
    reply = await run_turn(state, "so sánh giúp anh", deps)
    # No category yet: the bot asks which ngành (menu form is acceptable).
    assert "ngành hàng" in reply.text
    assert reply.presented_ids == []


# --- budget clear ---

def test_clear_marker_without_number_sets_clear_fields():
    result = fallback_understanding("cho anh xem khoảng giá khác đi")
    assert result.clear_fields == ["budget"]


def test_oldref_clear_ignores_old_number():
    result = fallback_understanding("không tra trong mức 15 triệu nữa")
    assert result.clear_fields == ["budget"]
    assert result.need_patch.budget_max is None


def test_new_budget_overrides_without_clear():
    result = fallback_understanding("đổi sang tầm 20-25 triệu đi")
    assert result.clear_fields == []
    assert result.need_patch.budget_max == 25_000_000


def test_apply_turn_clears_budget_and_reopens_question():
    state = AgentState(
        need=GenericNeed(category_code="38", budget_min=10_000_000, budget_max=15_000_000)
    )
    state.asked_questions["38"] = ["household", "budget"]
    understanding = AgentUnderstanding(
        intent="change_constraints",
        confidence=0.3,
        need_patch=GenericNeed(),
        clear_fields=["budget"],
    )
    apply_turn(state, understanding)
    assert state.need.budget_min is None
    assert state.need.budget_max is None
    assert "budget" not in state.asked_questions["38"]


async def test_augment_adds_clear_when_llm_missed_it():
    understanding = AgentUnderstanding(
        intent="change_constraints", confidence=0.9, need_patch=GenericNeed()
    )
    result = _augment_understanding(
        "không tra trong mức 15 triệu nữa", understanding, active_category="38"
    )
    assert result.clear_fields == ["budget"]


# --- JSON session persistence ---

def test_session_json_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SESSION_DIR", str(tmp_path))
    state = AgentState(session_id="test-session-1")
    state.need = GenericNeed(category_code="38", budget_max=15_000_000)
    state.previous_needs["72"] = GenericNeed(category_code="72", usage_purpose="gaming")
    state.asked_questions["38"] = ["household", "budget"]
    state.last_presented_ids = ["a", "b"]
    state.pending_question_key = "door_style"
    state.pending_question_text = "Kiểu ngăn đá nào ạ?"
    _persist_session(state)

    saved = json.loads((tmp_path / "test-session-1.json").read_text(encoding="utf-8"))
    assert saved["need"]["budget_max"] == 15_000_000

    loaded = _load_session("test-session-1")
    assert loaded is not None
    assert loaded.need.budget_max == 15_000_000
    assert loaded.previous_needs["72"].usage_purpose == "gaming"
    assert loaded.asked_questions["38"] == ["household", "budget"]
    assert loaded.pending_question_text == "Kiểu ngăn đá nào ạ?"


def test_corrupt_session_file_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SESSION_DIR", str(tmp_path))
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    assert _load_session("broken") is None


# --- determinism: same scripted conversation twice → identical output ---

async def test_conversation_is_deterministic():
    pool = _aircon_pool() + [product("f1", "38", 10_000_000)]
    script = [
        "tư vấn máy lạnh phòng 18m2 tầm 10 triệu",
        "cái nào êm hơn?",
        "so sánh 2 mẫu rẻ nhất đi",
        "ok",
    ]

    async def run_script():
        deps = AgentDependencies(products=pool)
        state = AgentState()
        return [(await run_turn(state, msg, deps)).text for msg in script]

    first = await run_script()
    second = await run_script()
    assert first == second
