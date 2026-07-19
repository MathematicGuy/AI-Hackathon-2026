"""Audit round 5: verified-flaw regressions — money parser bounds, capture
whitelist, detail flow + reference resolver, role release, general clears."""

import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, AgentUnderstanding, GenericNeed
from backend.app.agent.conversation.memory import apply_turn
from backend.app.agent.conversation.understand import (
    _parse_budget_vnd,
    fallback_understanding,
)
from backend.app.agent.graph import (
    AgentDependencies,
    _resolve_referenced_products,
    run_turn,
)


def product(pid, code, price, attrs=None, brand="B", model=None):
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="x",
        brand=brand,
        brand_id="1",
        model_code=model or pid,
        sku=pid,
        attributes=attrs or {},
        promotion=PromotionInfo(list_price=price, sale_price=None, gift=None),
    )


# --- Part A: money parser bounds and compact forms ---

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # regression: existing forms stay
        ("dưới 20 triệu", (None, 20_000_000)),
        ("tầm 15tr", (None, 15_000_000)),
        ("18-20 triệu", (18_000_000, 20_000_000)),
        ("từ 8 triệu", (8_000_000, None)),
        ("tầm 20-30 trịu", (20_000_000, 30_000_000)),
        ("500k", (None, 500_000)),
        # fixed: floor phrases were read as ceilings
        ("trên 10 triệu", (10_000_000, None)),
        ("hơn 15 triệu", (15_000_000, None)),
        ("tối thiểu 8 triệu", (8_000_000, None)),
        ("ít nhất 5 triệu", (5_000_000, None)),
        ("10 triệu trở lên", (10_000_000, None)),
        ("12 triệu đổ lại", (None, 12_000_000)),
        # new compact forms
        ("1tr5", (None, 1_500_000)),
        ("tầm 2tr2", (None, 2_200_000)),
        ("3 triệu rưỡi", (None, 3_500_000)),
        ("trên 4 củ rưỡi", (4_500_000, None)),
    ],
)
def test_budget_bounds_and_compact_forms(text, expected):
    assert _parse_budget_vnd(text) == expected


def test_fallback_uses_floor_as_budget_min():
    result = fallback_understanding("tư vấn tủ lạnh trên 10 triệu")
    assert result.need_patch.budget_min == 10_000_000
    assert result.need_patch.budget_max is None


# --- Part B: capture only for continuation intents ---

async def test_policy_interrupt_keeps_pending_and_clean_memory():
    deps = AgentDependencies(products=[product("f1", "38", 10_000_000)])
    state = AgentState()
    await run_turn(state, "tôi muốn mua tủ lạnh", deps)
    assert state.pending_question_key == "household"
    reply = await run_turn(state, "khoan đã, chính sách bảo hành thế nào?", deps)
    assert reply.intent == "policy_question"
    assert state.need.attribute_constraints == {}
    assert state.pending_question_key == "household"  # still waiting
    # the real answer afterwards is still captured
    await run_turn(state, "nhà 4 người", deps)
    assert "4" in state.need.attribute_constraints.get("household", "")


async def test_smalltalk_interrupt_not_captured():
    deps = AgentDependencies(products=[product("f1", "38", 10_000_000)])
    state = AgentState()
    await run_turn(state, "tôi muốn mua tủ lạnh", deps)
    await run_turn(state, "cảm ơn em nhé", deps)
    assert state.need.attribute_constraints == {}


# --- Part C: reference resolver + detail flow ---

def _monitor_pool():
    return [
        product("m1", "73", 3_000_000, {"Độ phân giải": "Full HD (1920 x 1080)"}, brand="Msi", model="172411"),
        product("m2", "73", 3_700_000, {"Độ phân giải": "Full HD (1920 x 1080)"}, brand="Msi", model="172263"),
        product("m3", "73", 3_900_000, {"Độ phân giải": "QHD (2560 x 1440)", "Tấm nền": "IPS"}, brand="Philips", model="172345"),
    ]


def _state_with_presented():
    state = AgentState(need=GenericNeed(category_code="73"))
    state.last_presented_ids = ["m1", "m2", "m3"]
    return state


def test_resolver_ordinals():
    deps = AgentDependencies(products=_monitor_pool())
    state = _state_with_presented()
    resolved = _resolve_referenced_products(state, "so sánh mẫu 1 với mẫu thứ ba", deps)
    assert [p.productidweb for p in resolved] == ["m1", "m3"]


def test_resolver_model_code_not_ordinal():
    deps = AgentDependencies(products=_monitor_pool())
    state = _state_with_presented()
    resolved = _resolve_referenced_products(state, "xem mẫu 172345 giúp anh", deps)
    assert [p.productidweb for p in resolved] == ["m3"]


def test_resolver_brand_fragment():
    deps = AgentDependencies(products=_monitor_pool())
    state = _state_with_presented()
    resolved = _resolve_referenced_products(state, "con philips ấy", deps)
    assert [p.productidweb for p in resolved] == ["m3"]


def test_resolver_empty_without_presented():
    deps = AgentDependencies(products=_monitor_pool())
    state = AgentState(need=GenericNeed(category_code="73"))
    assert _resolve_referenced_products(state, "mẫu thứ hai", deps) == []


async def test_detail_flow_renders_spec_sheet():
    deps = AgentDependencies(products=_monitor_pool())
    state = _state_with_presented()
    reply = await run_turn(state, "cho anh xem chi tiết mẫu thứ ba", deps)
    assert reply.intent == "product_detail"
    assert "Philips" in reply.text
    assert "Độ phân giải: QHD (2560 x 1440)" in reply.text
    assert reply.presented_ids == ["m3"]


async def test_detail_ambiguous_asks_which():
    deps = AgentDependencies(products=_monitor_pool())
    state = _state_with_presented()
    reply = await run_turn(state, "cho anh xem thông số chi tiết", deps)
    assert reply.intent == "product_detail"
    assert "mẫu nào" in reply.text


async def test_compare_ordinal_pair():
    deps = AgentDependencies(products=_monitor_pool())
    state = _state_with_presented()
    reply = await run_turn(state, "so sánh mẫu 1 với mẫu 3", deps)
    assert reply.intent == "compare_products"
    assert set(reply.presented_ids) == {"m1", "m3"}


# --- Part D: role release + general clears ---

def _understanding(**kwargs):
    defaults = dict(intent="change_constraints", confidence=0.3)
    defaults.update(kwargs)
    return AgentUnderstanding(**defaults)


def test_new_preference_releases_role_lock():
    state = AgentState(
        need=GenericNeed(category_code="38", requested_roles=["best_price"])
    )
    apply_turn(
        state,
        _understanding(need_patch=GenericNeed(usage_purpose="gia đình đông người")),
    )
    assert state.need.requested_roles == []


def test_explicit_roles_still_replace():
    state = AgentState(
        need=GenericNeed(category_code="38", requested_roles=["best_price"])
    )
    apply_turn(
        state,
        _understanding(need_patch=GenericNeed(requested_roles=["most_expensive"])),
    )
    assert state.need.requested_roles == ["most_expensive"]


@pytest.mark.parametrize(
    ("message", "field", "attribute"),
    [
        ("hãng nào cũng được em", "brands", "brand_prefs"),
        ("bỏ ưu tiên đi, gì cũng được", "priorities", "priorities"),
        ("gợi ý bình thường đi em", "roles", "requested_roles"),
    ],
)
def test_general_clear_markers(message, field, attribute):
    result = fallback_understanding(message)
    assert field in result.clear_fields
    state = AgentState(
        need=GenericNeed(
            category_code="38",
            brand_prefs=["Samsung"],
            priorities=["tiết kiệm điện"],
            requested_roles=["best_price"],
        )
    )
    apply_turn(state, _understanding(clear_fields=[field]))
    assert getattr(state.need, attribute) == []
