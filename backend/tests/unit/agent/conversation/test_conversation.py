import pytest

from backend.app.agent.contracts import (
    DEFAULT_ROLES,
    AgentState,
    AgentUnderstanding,
    GenericNeed,
)
from backend.app.agent.conversation import coldstart, memory
from backend.app.agent.conversation.scenario_data import SCENARIOS
from backend.app.agent.conversation.understand import (
    fallback_understanding,
    understand_turn,
)


# --- contracts ---

def test_default_roles_are_price_value_performance():
    assert DEFAULT_ROLES == ("best_price", "best_value", "best_performance")


def test_agent_intent_includes_policy_question():
    understanding = AgentUnderstanding(intent="policy_question", confidence=0.9)
    assert understanding.intent == "policy_question"


# --- scenarios ---

def test_all_14_categories_have_scenarios():
    assert len(SCENARIOS) == 14
    for code, scenario in SCENARIOS.items():
        assert scenario["questions"], f"category {code} needs questions"


def test_budget_is_never_the_first_question():
    # The most material narrowing feature is asked before budget everywhere.
    for code, scenario in SCENARIOS.items():
        assert scenario["questions"][0]["key"] != "budget", code


# --- cold-start question selection ---

def new_state(**need_kwargs):
    return AgentState(need=GenericNeed(**need_kwargs))


def test_first_question_is_most_material(monkeypatch):
    state = new_state(category_code="115")
    question = coldstart.next_question(state)
    assert question.key == "load"


def test_answered_question_not_asked_again():
    state = new_state(category_code="72", usage_purpose="văn phòng")
    question = coldstart.next_question(state)
    assert question.key == "budget"


def test_purpose_followups_injected_for_gaming():
    state = new_state(
        category_code="72", usage_purpose="gaming", budget_max=20_000_000
    )
    question = coldstart.next_question(state)
    assert question.key == "gaming_display"


def test_asked_but_unanswered_question_not_repeated():
    state = new_state(category_code="38")
    first = coldstart.next_question(state)
    coldstart.record_asked(state, first)
    second = coldstart.next_question(state)
    assert second.key != first.key


def test_cycle_stops_after_three_questions():
    state = new_state(category_code="49")
    for _ in range(3):
        question = coldstart.next_question(state)
        assert question is not None
        coldstart.record_asked(state, question)
    assert coldstart.next_question(state) is None


def test_material_minimum_requires_category_plus_narrowing():
    assert coldstart.has_material_minimum(GenericNeed()) is False
    assert coldstart.has_material_minimum(GenericNeed(category_code="38")) is False
    assert coldstart.has_material_minimum(
        GenericNeed(category_code="38", budget_max=15_000_000)
    ) is True


# --- memory: three update modes ---

def test_patch_merge_explicit_wins_omitted_persists():
    state = new_state(category_code="72", usage_purpose="gaming", budget_max=20_000_000)
    understanding = AgentUnderstanding(
        intent="change_constraints",
        confidence=0.9,
        need_patch=GenericNeed(budget_max=15_000_000),
    )
    memory.apply_turn(state, understanding)
    assert state.need.budget_max == 15_000_000
    assert state.need.usage_purpose == "gaming"
    assert state.need.category_code == "72"


def test_category_switch_archives_and_restores():
    state = new_state(category_code="72", usage_purpose="gaming", budget_max=20_000_000)
    switch = AgentUnderstanding(
        intent="new_search",
        confidence=0.9,
        need_patch=GenericNeed(category_code="38"),
    )
    memory.apply_turn(state, switch)
    assert state.need.category_code == "38"
    assert state.need.usage_purpose is None
    assert "72" in state.previous_needs

    back = AgentUnderstanding(
        intent="new_search",
        confidence=0.9,
        need_patch=GenericNeed(category_code="72"),
    )
    memory.apply_turn(state, back)
    assert state.need.category_code == "72"
    assert state.need.usage_purpose == "gaming"
    assert state.need.budget_max == 20_000_000


def test_session_brand_prefs_carry_across_switch():
    state = new_state(category_code="72", brand_prefs=["Samsung"])
    switch = AgentUnderstanding(
        intent="new_search",
        confidence=0.9,
        need_patch=GenericNeed(category_code="38"),
    )
    memory.apply_turn(state, switch)
    assert state.need.brand_prefs == ["Samsung"]


def test_brand_prefs_merge_unique():
    need = memory.merge_need(
        GenericNeed(brand_prefs=["LG"]), GenericNeed(brand_prefs=["Samsung", "LG"])
    )
    assert need.brand_prefs == ["LG", "Samsung"]


# --- understanding fallback ---

def test_fallback_detects_category_and_budget_range():
    understanding = fallback_understanding(
        "mình muốn mua máy tính để bàn gaming tầm 18-20 triệu"
    )
    assert understanding.intent == "new_search"
    assert understanding.need_patch.category_code == "72"
    assert understanding.need_patch.budget_min == 18_000_000
    assert understanding.need_patch.budget_max == 20_000_000


def test_fallback_detects_policy_question():
    understanding = fallback_understanding("cho hỏi chính sách đổi trả thế nào")
    assert understanding.intent == "policy_question"


def test_fallback_cheapest_preference_overrides_roles():
    understanding = fallback_understanding("tìm tủ lạnh rẻ nhất giúp mình")
    assert understanding.need_patch.requested_roles == ["best_price"]


def test_fallback_never_invents_budget():
    understanding = fallback_understanding("tư vấn máy giặt cho nhà 4 người")
    assert understanding.need_patch.budget_max is None
    assert understanding.need_patch.budget_min is None


async def test_understand_turn_degrades_on_extractor_failure():
    class Boom:
        async def extract(self, message, *, state_summary):
            from backend.app.agent.conversation.understand import ExtractorError

            raise ExtractorError("down")

    understanding, flags = await understand_turn(
        "mua tủ lạnh tầm 10 triệu", extractor=Boom()
    )
    assert understanding.intent == "new_search"
    assert flags == ["understanding_degraded"]
