"""Tests for the dimension round: registry parsing, preference-driven roles,
dimension compare, product_qa flow, and the upgraded domain rules."""

import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.dimensions import (
    dimension_value,
    find_dimension,
    headline_dimension,
    metric_explanation,
    preferred_dimensions,
)
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, GenericNeed
from backend.app.agent.conversation.domain_rules import apply_domain_filters
from backend.app.agent.conversation.understand import fallback_understanding
from backend.app.agent.graph import (
    AgentDependencies,
    _is_product_qa,
    run_turn,
)
from backend.app.agent.respond import render_suggestions
from backend.app.agent.tools.suggest import suggest_products


def product(pid, code, price, attrs=None):
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="x",
        brand="B",
        brand_id="1",
        model_code=pid,
        sku=pid,
        attributes=attrs or {},
        promotion=PromotionInfo(list_price=price, sale_price=None, gift=None),
    )


# --- registry parsing ---

def test_placeholder_never_becomes_a_value():
    dim = find_dimension("73", "Độ sáng")
    p = product("a", "73", 3_000_000, {"Độ sáng": "Hãng không công bố"})
    assert dimension_value(p, dim) is None


def test_resolution_ordinal_ranks_qhd_above_fullhd():
    dim = find_dimension("73", "Độ phân giải")
    qhd = product("a", "73", 0, {"Độ phân giải": "QHD (2560 x 1440)"})
    fhd = product("b", "73", 0, {"Độ phân giải": "Full HD (1920 x 1080)"})
    assert dimension_value(qhd, dim) > dimension_value(fhd, dim)


def test_response_time_is_lower_better():
    dim = find_dimension("73", "Thời gian đáp ứng")
    assert dim.kind == "numeric_lower"
    fast = product("a", "73", 0, {"Thời gian đáp ứng": "1 ms (GTG)"})
    assert dimension_value(fast, dim) == 1.0


def test_storage_terabytes_normalized_to_gb():
    dim = find_dimension("72", "Ổ cứng")
    tb = product("a", "72", 0, {"Ổ cứng": "HDD 1 TB"})
    gb = product("b", "72", 0, {"Ổ cứng": "SSD 512 GB"})
    assert dimension_value(tb, dim) == 1000.0
    assert dimension_value(gb, dim) == 512.0


def test_watch_battery_days_normalized_to_hours():
    dim = find_dimension("49", "Thời gian sử dụng")
    days = product("a", "49", 0, {"Thời gian sử dụng": "Khoảng 7 ngày"})
    hours = product("b", "49", 0, {"Thời gian sử dụng": "Khoảng 18 giờ"})
    assert dimension_value(days, dim) == 168.0
    assert dimension_value(hours, dim) == 18.0


def test_monitor_headline_is_resolution_not_size():
    assert headline_dimension("73").key == "Độ phân giải"


def test_metric_explanation_names_measures():
    text = metric_explanation("73")
    assert "Độ phân giải" in text
    assert "Thời gian đáp ứng" in text


# --- preference → dimensions ---

def test_gaming_preference_ranks_response_time():
    need = GenericNeed(category_code="73", usage_purpose="chơi game")
    dims = preferred_dimensions("73", need)
    assert dims and dims[0].key == "Thời gian đáp ứng"


def test_quiet_preference_finds_noise_dimension():
    need = GenericNeed(category_code="36", priorities=["chạy êm"])
    dims = preferred_dimensions("36", need)
    assert dims and dims[0].key == "Độ ồn"


def test_no_signal_returns_empty():
    assert preferred_dimensions("73", GenericNeed(category_code="73")) == []


# --- dynamic roles ---

def _monitor_pool():
    return [
        product("cheap", "73", 3_000_000, {"Độ phân giải": "Full HD (1920 x 1080)", "Thời gian đáp ứng": "5 ms"}),
        product("sharp", "73", 4_500_000, {"Độ phân giải": "QHD (2560 x 1440)", "Thời gian đáp ứng": "4 ms"}),
        product("fast", "73", 4_000_000, {"Độ phân giải": "Full HD (1920 x 1080)", "Thời gian đáp ứng": "1 ms (GTG)"}),
    ]


def test_no_preference_keeps_classic_roles():
    suggestions = suggest_products(
        _monitor_pool(), category_code="73", need=GenericNeed(category_code="73")
    )
    assert "best_price" in suggestions.winners
    # headline (resolution) powers best_performance transparently
    assert suggestions.winners["best_performance"].productidweb == "sharp"
    assert suggestions.role_evidence["best_performance"][0] == "Sắc nét nhất"


def test_gaming_preference_creates_dimension_role():
    need = GenericNeed(category_code="73", usage_purpose="chơi game")
    suggestions = suggest_products(_monitor_pool(), category_code="73", need=need)
    role = "dim:Thời gian đáp ứng"
    assert suggestions.winners[role].productidweb == "fast"
    label, value = suggestions.role_evidence[role]
    assert label == "Phản hồi nhanh nhất"
    assert "1 ms" in value


def test_sparse_dimension_skipped_by_data_floor():
    pool = [
        product("a", "73", 3_000_000, {"Độ phủ màu": "99% sRGB"}),
        product("b", "73", 3_500_000, {}),
        product("c", "73", 3_600_000, {}),
        product("d", "73", 3_700_000, {}),
    ]
    need = GenericNeed(category_code="73", priorities=["màu chuẩn cho đồ họa"])
    suggestions = suggest_products(pool, category_code="73", need=need)
    assert "dim:Độ phủ màu" in suggestions.skipped_roles


def test_explicit_roles_still_win():
    need = GenericNeed(
        category_code="73", usage_purpose="chơi game", requested_roles=["best_price"]
    )
    suggestions = suggest_products(
        _monitor_pool(), category_code="73", roles=need.requested_roles, need=need
    )
    assert list(suggestions.winners) == ["best_price"]


def test_render_badge_shows_dimension_value():
    need = GenericNeed(category_code="73", usage_purpose="chơi game")
    suggestions = suggest_products(_monitor_pool(), category_code="73", need=need)
    response = render_suggestions(
        suggestions, category_name="Màn hình máy tính", need=need
    )
    assert "Phản hồi nhanh nhất: 1 ms" in response.text


# --- product_qa detection and flow ---

def test_product_qa_requires_presented_products():
    state = AgentState(need=GenericNeed(category_code="73"))
    assert not _is_product_qa(state, "thang đo là gì")
    state.last_presented_ids = ["a"]
    assert _is_product_qa(state, "trong 2 cái gợi ý cái nào tốt hơn về mặt hiệu năng và hiệu năng ở đây là gì? thang đo là gì?")
    assert _is_product_qa(state, "màn nào nét hơn?")


async def test_product_qa_explains_metric_and_compares():
    pool = _monitor_pool()
    deps = AgentDependencies(products=pool)
    state = AgentState(need=GenericNeed(category_code="73"))
    state.last_presented_ids = ["cheap", "sharp"]
    reply = await run_turn(
        state,
        "trong 2 cái gợi ý cái nào tốt hơn về mặt hiệu năng và hiệu năng ở đây là gì? thang đo là gì?",
        deps,
    )
    assert reply.intent == "product_qa"
    assert "thang đo" in reply.text
    assert "Độ phân giải" in reply.text
    assert "nhỉnh hơn" in reply.text
    assert "cho em xin thêm thông tin" not in reply.text


async def test_product_qa_honest_on_missing_data():
    pool = [
        product("a", "73", 3_000_000, {"Độ phân giải": "Full HD (1920 x 1080)"}),
        product("b", "73", 3_500_000, {}),
    ]
    deps = AgentDependencies(products=pool)
    state = AgentState(need=GenericNeed(category_code="73"))
    state.last_presented_ids = ["a", "b"]
    reply = await run_turn(state, "màn nào nét hơn?", deps)
    assert "hãng không công bố" in reply.text


# --- upgraded domain rules ---

def test_monitor_size_range_kept_inclusive():
    pool = [
        product("m238", "73", 0, {"Kích thước màn hình": "23.8 inch"}),
        product("m27", "73", 0, {"Kích thước màn hình": "27 inch"}),
        product("m32", "73", 0, {"Kích thước màn hình": "32 inch"}),
    ]
    need = GenericNeed(
        category_code="73", attribute_constraints={"size": "24-27 inch"}
    )
    kept = {p.productidweb for p in apply_domain_filters(pool, need)}
    assert kept == {"m238", "m27"}


def test_washer_load_band_for_family_of_four():
    pool = [
        product("small", "115", 0, {"Khối lượng tải chính": "7 Kg"}),
        product("mid", "115", 0, {"Khối lượng tải chính": "9 Kg"}),
        product("nodata", "115", 0, {}),
    ]
    need = GenericNeed(
        category_code="115", attribute_constraints={"load": "nhà 4 người"}
    )
    kept = {p.productidweb for p in apply_domain_filters(pool, need)}
    assert kept == {"mid", "nodata"}


# --- fallback size capture ---

def test_fallback_captures_inch_range_for_monitor():
    result = fallback_understanding(
        "24-27 inch, làm việc, xem phim, tầm 3-5 triệu", active_category="73"
    )
    assert result.need_patch.attribute_constraints.get("size") == "24-27 inch"
    assert result.need_patch.budget_max == 5_000_000
    assert result.need_patch.usage_purpose == "làm việc"


def test_fallback_captures_room_area_for_aircon():
    result = fallback_understanding("tư vấn máy lạnh phòng 18m2 tầm 10 triệu")
    assert result.need_patch.attribute_constraints.get("room_area") == "18m2"


async def test_llm_result_augmented_with_missed_room_area():
    # The LLM classified fine but skipped the room area — the deterministic
    # layer fills the gap without overriding anything the model returned.
    from backend.app.agent.contracts import AgentUnderstanding
    from backend.app.agent.conversation.understand import understand_turn

    class FakeExtractor:
        async def extract(self, message, *, state_summary=""):
            return AgentUnderstanding(
                intent="new_search",
                confidence=0.9,
                need_patch=GenericNeed(category_code="36", budget_max=10_000_000),
            )

    result, flags = await understand_turn(
        "tư vấn máy lạnh phòng 18m2 tầm 10 triệu", extractor=FakeExtractor()
    )
    assert flags == []
    assert result.need_patch.attribute_constraints.get("room_area") == "18m2"
    assert result.need_patch.budget_max == 10_000_000
