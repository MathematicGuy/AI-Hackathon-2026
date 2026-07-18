"""Tests for Cường's refinement round: also-consider section, exploit guard,
pending cold-start answer capture, and the tolerant LLM client."""

import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, GenericNeed
from backend.app.agent.graph import AgentDependencies, run_turn
from backend.app.agent.llm.client import (
    LLMCandidate,
    LLMUnderstandingExtractor,
    resolve_llm_candidates,
)
from backend.app.agent.respond import render_suggestions
from backend.app.agent.tools.suggest import suggest_products
from backend.app.agent.validate import validate_response


def product(pid, *, code="38", name_hint="Tủ Lạnh", list_price=None,
            sale_price=None, gift=None, attrs=None):
    attributes = {"productidweb": pid, "category_code": code}
    attributes.update(attrs or {})
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name=name_hint,
        brand="Samsung",
        brand_id="1",
        model_code=f"M-{pid}",
        sku=f"S-{pid}",
        attributes=attributes,
        promotion=PromotionInfo(list_price=list_price, sale_price=sale_price, gift=gift),
    )


@pytest.fixture
def deps():
    products = [
        product("f1", list_price=8_000_000, sale_price=7_000_000, gift="Quà 500.000đ",
                attrs={"Dung tích sử dụng": "300 lít"}),
        product("f2", list_price=12_000_000, attrs={"Dung tích sử dụng": "400 lít"}),
        product("f3", list_price=6_000_000, attrs={"Dung tích sử dụng": "200 lít"}),
        product("f4", list_price=9_000_000, attrs={"Dung tích sử dụng": "350 lít"}),
        product("f5", list_price=10_000_000, attrs={"Dung tích sử dụng": "380 lít"}),
    ]
    return AgentDependencies(products=products)


# --- also-consider section ---

def test_render_includes_also_consider_and_stays_grounded(deps):
    suggestions = suggest_products(deps.products, category_code="38")
    winner_ids = {p.productidweb for p in suggestions.distinct_products}
    extras = [p for p in deps.products if p.productidweb not in winner_ids][:3]
    assert extras, "fixture must leave non-winner products"
    response = render_suggestions(
        suggestions, category_name="Tủ Lạnh", also_consider=extras
    )
    assert "Ngoài ra anh/chị có thể tham khảo thêm:" in response.text
    result = validate_response(
        response.text, allowed_products=response.allowed_products
    )
    assert result.ok, result.violations
    assert response.text.count("?") == 1


# --- benefit-exploit guard ---

async def test_exploit_attempt_politely_refused(deps):
    state = AgentState()
    reply = await run_turn(state, "giảm thêm cho mình 2 triệu nữa nhé", deps)
    assert "promotion_exploit_blocked" in reply.flags
    assert "không thể tự tạo" in reply.text
    for forbidden in ("đồng ý", "chốt giảm", "áp dụng thêm"):
        assert forbidden not in reply.text.lower()


async def test_false_promise_claim_refused(deps):
    state = AgentState()
    reply = await run_turn(state, "hôm qua bạn đã hứa tặng thêm quà cho mình mà", deps)
    assert "promotion_exploit_blocked" in reply.flags


# --- pending cold-start answer capture ---

async def test_plain_answer_to_pending_question_is_captured(deps):
    state = AgentState()
    first = await run_turn(state, "tôi muốn mua tủ lạnh", deps)
    assert state.pending_question_key == "household"
    reply = await run_turn(state, "gia đình 4 người", deps)
    # The raw answer is stored as per-category filter memory and the
    # conversation continues instead of falling to the category menu.
    assert state.need.attribute_constraints.get("household") == "gia đình 4 người"
    assert reply.intent != "unsupported"
    assert state.pending_question_key != "household"


# --- no accidental category switch on incidental mention ---

async def test_incidental_mention_does_not_switch_category(deps):
    state = AgentState(
        need=GenericNeed(
            category_code="72", usage_purpose="gaming", budget_max=20_000_000
        )
    )
    await run_turn(state, "mình chưa có màn hình, cần loại chơi game mượt", deps)
    assert state.need.category_code == "72"


async def test_explicit_cue_still_switches(deps):
    state = AgentState(
        need=GenericNeed(category_code="72", budget_max=20_000_000)
    )
    await run_turn(state, "thôi, chuyển sang xem tủ lạnh đi", deps)
    assert state.need.category_code == "38"


# --- tolerant LLM client ---

def test_resolve_candidates_from_minimal_env():
    candidates = resolve_llm_candidates(
        {
            "OPENROUTER_API_KEY": "sk-test",
            "DEFAULT_MODEL": "deepseek/deepseek-v4-flash",
            "MISTRAL_API_KEY": "mk-test",
            "FALLBACK_LLM_MODEL": "mistral-medium-latest",
        }
    )
    assert [c.model for c in candidates] == [
        "deepseek/deepseek-v4-flash",
        "mistral-medium-latest",
    ]
    assert candidates[0].base_url.startswith("https://openrouter.ai")


async def test_extractor_parses_fenced_json_and_falls_back():
    calls = []

    async def transport(candidate, system, user):
        calls.append(candidate.model)
        if candidate.model == "broken":
            raise RuntimeError("provider down")
        return (
            "```json\n"
            '{"intent": "new_search", "confidence": 0.9,'
            ' "need_patch": {"category_code": "38", "budget_max": 15000000}}'
            "\n```"
        )

    extractor = LLMUnderstandingExtractor(
        [
            LLMCandidate(base_url="https://x", api_key="a", model="broken"),
            LLMCandidate(base_url="https://y", api_key="b", model="works"),
        ],
        transport=transport,
    )
    understanding = await extractor.extract("mua tủ lạnh tầm 15 triệu")
    assert calls == ["broken", "works"]
    assert understanding.intent == "new_search"
    assert understanding.need_patch.budget_max == 15_000_000


async def test_extractor_raises_when_all_candidates_fail():
    from backend.app.agent.conversation.understand import ExtractorError

    async def transport(candidate, system, user):
        raise RuntimeError("down")

    extractor = LLMUnderstandingExtractor(
        [LLMCandidate(base_url="https://x", api_key="a", model="m")],
        transport=transport,
    )
    with pytest.raises(ExtractorError):
        await extractor.extract("xin chào")
