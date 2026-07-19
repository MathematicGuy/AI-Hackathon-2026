"""Live-test round 6: full role pool, honest compare copy, policy doc-name
bonus + heading trim, product_qa explicit outcomes, unified format."""

import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, GenericNeed
from backend.app.agent.graph import AgentDependencies, run_turn
from backend.app.agent.tools.search import search_products


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


def _big_pool(count=30):
    return [
        product(f"p{i:02d}", "36", 5_000_000 + i * 1_000_000,
                attrs={"Độ ồn": f"{30 + i} dB"})
        for i in range(count)
    ]


# --- role pool covers the whole candidate set ---

async def test_most_expensive_sees_beyond_first_page():
    pool = _big_pool(30)  # prices 5tr..34tr ascending
    deps = AgentDependencies(products=pool)
    state = AgentState(need=GenericNeed(category_code="36"))
    reply = await run_turn(state, "máy lạnh đắt nhất đi em", deps)
    assert "p29" in reply.presented_ids  # 34tr — the REAL top, not the 20th


def test_search_accepts_large_limit():
    result = search_products(_big_pool(30), category_code="36", limit=500)
    assert result.total_candidates == 30
    assert len(result.items) == 30


async def test_budget_cap_on_most_expensive_is_disclosed():
    pool = _big_pool(30)
    deps = AgentDependencies(products=pool)
    state = AgentState(
        need=GenericNeed(category_code="36", budget_max=10_000_000)
    )
    reply = await run_turn(state, "máy lạnh đắt nhất đi em", deps)
    assert "Em đang lọc trong tầm giá" in reply.text


# --- honest compare copy ---

async def test_auto_fetched_compare_does_not_claim_viewing():
    deps = AgentDependencies(products=_big_pool(5))
    state = AgentState(need=GenericNeed(category_code="36"))
    reply = await run_turn(state, "so sánh 2 mẫu rẻ nhất đi", deps)
    assert "em chọn 2 mẫu" in reply.text.lower()
    assert "đang xem" not in reply.text


async def test_presented_compare_still_says_viewing():
    deps = AgentDependencies(products=_big_pool(5))
    state = AgentState(need=GenericNeed(category_code="36"))
    state.last_presented_ids = ["p00", "p01"]
    reply = await run_turn(state, "so sánh 2 mẫu này giúp anh", deps)
    assert "đang xem" in reply.text


# --- product_qa: explicit outcome on every dimension + pivot ---

async def test_qa_tie_is_stated_and_pivots():
    pool = [
        product("a", "36", 8_000_000, attrs={
            "Loại Inverter": "Máy lạnh Inverter", "Độ ồn": "Dàn lạnh: 29 dB"}),
        product("b", "36", 9_000_000, attrs={
            "Loại Inverter": "Máy lạnh Inverter", "Độ ồn": "Dàn lạnh: 33 dB"}),
    ]
    deps = AgentDependencies(products=pool)
    state = AgentState(need=GenericNeed(category_code="36"))
    state.last_presented_ids = ["a", "b"]
    reply = await run_turn(state, "cái nào tiết kiệm điện hơn", deps)
    assert "ngang nhau" in reply.text
    assert "Độ ồn" in reply.text  # pivot to a dimension that CAN separate
    assert "Kết quả:" in reply.text
    assert "→" not in reply.text


async def test_qa_missing_data_is_honest():
    pool = [
        product("a", "36", 8_000_000, attrs={"Loại Inverter": "Máy lạnh Inverter"}),
        product("b", "36", 9_000_000, attrs={}),
    ]
    deps = AgentDependencies(products=pool)
    state = AgentState(need=GenericNeed(category_code="36"))
    state.last_presented_ids = ["a", "b"]
    reply = await run_turn(state, "cái nào tiết kiệm điện hơn", deps)
    assert "chưa đủ để phân định" in reply.text


# --- "hả?" restates the last bot line ---

async def test_ha_restates_last_reply():
    deps = AgentDependencies(products=_big_pool(5))
    state = AgentState(need=GenericNeed(category_code="36"))
    state.last_presented_ids = ["p00", "p01"]
    await run_turn(state, "cái nào êm hơn?", deps)
    reply = await run_turn(state, "hả?", deps)
    assert "Dạ ý em vừa nói là:" in reply.text
    assert "xin thêm thông tin về nhu cầu" not in reply.text


# --- unified format: no arrows anywhere ---

async def test_suggestions_have_no_arrow():
    deps = AgentDependencies(products=_big_pool(10))
    state = AgentState(need=GenericNeed(category_code="36", budget_max=12_000_000))
    reply = await run_turn(state, "tư vấn máy lạnh tầm 12 triệu", deps)
    assert "→" not in reply.text
    assert "Phù hợp vì:" in reply.text


# --- LLM floor-misread of bare amounts is corrected deterministically ---

async def test_bare_amount_min_only_flipped_to_ceiling():
    from backend.app.agent.contracts import AgentUnderstanding
    from backend.app.agent.conversation.understand import _augment_understanding

    misread = AgentUnderstanding(
        intent="new_search",
        confidence=0.9,
        need_patch=GenericNeed(category_code="36", budget_min=40_000_000),
    )
    fixed = _augment_understanding(
        "tư vấn máy lạnh tầm 40 triệu", misread, active_category="36"
    )
    assert fixed.need_patch.budget_min is None
    assert fixed.need_patch.budget_max == 40_000_000


async def test_genuine_floor_phrase_stands():
    from backend.app.agent.contracts import AgentUnderstanding
    from backend.app.agent.conversation.understand import _augment_understanding

    floor = AgentUnderstanding(
        intent="new_search",
        confidence=0.9,
        need_patch=GenericNeed(category_code="36", budget_min=40_000_000),
    )
    kept = _augment_understanding(
        "máy lạnh trên 40 triệu", floor, active_category="36"
    )
    assert kept.need_patch.budget_min == 40_000_000
    assert kept.need_patch.budget_max is None


# --- a role directive is never captured as the pending answer ---

async def test_role_ask_not_captured_as_pending_answer():
    pool = _big_pool(10)
    deps = AgentDependencies(products=pool)
    state = AgentState(need=GenericNeed(category_code="36", budget_max=12_000_000))
    state.pending_question_key = "room_area"
    state.pending_question_text = "Phòng bao nhiêu m² ạ?"
    await run_turn(state, "máy lạnh đắt nhất đi em", deps)
    assert "room_area" not in state.need.attribute_constraints


# --- policy: doc-name bonus + heading trim ---

async def test_warranty_lookup_hits_warranty_doc():
    deps = AgentDependencies(products=_big_pool(3))
    state = AgentState()
    reply = await run_turn(state, "tra cứu bảo hành máy lạnh", deps)
    assert reply.intent == "policy_question"
    assert "Chính sách bảo hành & đổi trả" in reply.text
    assert "Bảng giá Dịch vụ" not in reply.text
