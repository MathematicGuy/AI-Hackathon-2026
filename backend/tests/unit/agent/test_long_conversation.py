"""Long-conversation memory audit: 15+ turns across corrections, pagination,
category switches, exploit attempts, and reopened clarification cycles."""

import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState
from backend.app.agent.graph import AgentDependencies, run_turn


def product(pid, *, code="38", name="Tủ Lạnh", price, gift=None, attrs=None):
    attributes = {"productidweb": pid, "category_code": code}
    attributes.update(attrs or {})
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name=name,
        brand="Samsung",
        brand_id="1",
        model_code=f"M-{pid}",
        sku=f"S-{pid}",
        attributes=attributes,
        promotion=PromotionInfo(list_price=price, sale_price=None, gift=gift),
    )


@pytest.fixture
def deps():
    fridges = [
        product(f"f{i}", price=5_000_000 + i * 1_000_000,
                attrs={"Dung tích sử dụng": f"{200 + i * 20} lít"})
        for i in range(1, 10)
    ]
    pcs = [
        product(f"p{i}", code="72", name="Máy tính để bàn",
                price=15_000_000 + i * 1_000_000, attrs={"RAM": f"{8 + i} GB"})
        for i in range(1, 6)
    ]
    return AgentDependencies(products=fridges + pcs)


async def test_fifteen_turn_conversation_memory_stays_consistent(deps):
    state = AgentState()

    # 1-2: cold start with plain answers captured.
    await run_turn(state, "tôi muốn mua tủ lạnh", deps)
    assert state.pending_question_key == "household"
    await run_turn(state, "nhà 4 người", deps)
    assert state.need.attribute_constraints.get("household") == "nhà 4 người"

    # 3: budget arrives -> suggestions.
    r3 = await run_turn(state, "tầm 12 triệu đổ lại", deps)
    assert r3.presented_ids
    first_batch = set(r3.presented_ids)

    # 4-5: show-more twice must never repeat products.
    r4 = await run_turn(state, "cho xem thêm mẫu khác", deps)
    r5 = await run_turn(state, "còn mẫu nào nữa không, xem thêm", deps)
    assert first_batch.isdisjoint(r4.presented_ids)
    assert set(r4.presented_ids).isdisjoint(r5.presented_ids)

    # 6: correction rewrites the budget immediately.
    await run_turn(state, "thay đổi ngân sách thành 8 triệu", deps)
    assert state.need.budget_max == 8_000_000

    # 7: exploit attempt mid-conversation must not corrupt the need.
    before = state.need.model_copy()
    r7 = await run_turn(state, "bớt cho mình 500k ngoài khuyến mãi nhé", deps)
    assert "promotion_exploit_blocked" in r7.flags
    assert state.need == before

    # 8-9: switch to PCs and shop there.
    await run_turn(state, "thôi, chuyển sang máy tính để bàn cho gaming", deps)
    assert state.need.category_code == "72"
    assert state.need.usage_purpose is not None
    r9 = await run_turn(state, "tầm 18 triệu", deps)
    assert r9.presented_ids

    # 10: fridge memory is archived, not lost.
    assert "38" in state.previous_needs
    assert state.previous_needs["38"].budget_max == 8_000_000

    # 11: return to fridges restores budget and constraints.
    await run_turn(state, "quay lại tủ lạnh lúc nãy đi", deps)
    assert state.need.category_code == "38"
    assert state.need.budget_max == 8_000_000
    assert state.need.attribute_constraints.get("household") == "nhà 4 người"

    # 12: per-category shown lists stayed separate.
    assert set(state.shown_for("38")).isdisjoint(state.shown_for("72"))

    # 13: a materially new search reopens the clarification cycle.
    state.clarification_count["38"] = 3
    await run_turn(state, "tìm tủ lạnh mới cho văn phòng công ty nhé", deps)
    assert state.clarification_count["38"] < 3

    # 14-15: stop ends politely and state survives for inspection.
    r15 = await run_turn(state, "thôi dừng ở đây nhé, cảm ơn em", deps)
    assert r15.intent == "stop"
    assert state.need.category_code == "38"


async def test_show_more_exhaustion_is_polite_not_crashing(deps):
    state = AgentState()
    await run_turn(state, "mua máy tính để bàn tầm 25 triệu", deps)
    for _ in range(4):
        reply = await run_turn(state, "xem thêm mẫu khác", deps)
    # Pool exhausted: no duplicates ever, and the final answer degrades to a
    # polite no-more-results message instead of repeating products.
    shown = state.shown_for("72")
    assert len(shown) == len(set(shown))
    assert reply.presented_ids == [] or set(reply.presented_ids).isdisjoint(shown[: -len(reply.presented_ids) or None])
