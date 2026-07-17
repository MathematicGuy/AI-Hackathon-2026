import importlib

import pytest

from backend.app.contracts.schemas import (
    AdvisorState,
    AirConditionerNeed,
    Assumption,
    EvidenceRef,
    ExcludedProduct,
    IntentOutput,
    NeedPriority,
    RecommendationOutput,
    RoleWinner,
    RoleWinners,
)


SNAPSHOT = "synthetic-aircon-m1-2026-07-17"


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-104 {self.name} module is not implemented")


@pytest.fixture
def state_module():
    try:
        return importlib.import_module("backend.app.graph.state")
    except ModuleNotFoundError:
        return MissingModule("workflow state")


@pytest.fixture
def merge_module():
    try:
        return importlib.import_module("backend.app.graph.nodes.merge_state")
    except ModuleNotFoundError:
        return MissingModule("state merge")


def need(**overrides):
    values = {
        "budget_max_vnd": 20_000_000,
        "room_size_m2": 18.0,
        "room_type": "bedroom",
        "sunlight_exposure": None,
        "location": "HCM",
        "priorities": [
            NeedPriority(
                name="energy_saving", importance="primary", source="explicit"
            ),
        ],
    }
    values.update(overrides)
    return AirConditionerNeed(**values)


def intent_output(patch, *, intent="new_search", constraints_changed=False):
    return IntentOutput(
        intent=intent,
        confidence=0.95,
        constraints_changed=constraints_changed,
        need_patch=patch,
    )


def winner(role):
    return RoleWinner(
        product_id="AC-M1-002",
        role=role,
        score=0.9,
        evidence=[EvidenceRef(path="sale_price_vnd", source_snapshot=SNAPSHOT)],
        reason_codes=["fits_budget"],
    )


def role_winners():
    return RoleWinners(
        best_overall=winner("best_overall"),
        best_value=winner("best_value"),
        cheapest_qualified=winner("cheapest_qualified"),
    )


def recommendation_output(customer_need):
    return RecommendationOutput(
        answer_type="recommendation",
        intent="new_search",
        customer_need=customer_need,
    )


def base_state(**overrides):
    customer_need = overrides.pop("customer_need", need())
    state = {
        "messages": [],
        "session_id": "session-1",
        "request_id": "request-1",
        "user_id": None,
        "turn_number": 3,
        "current_intent": "new_search",
        "customer_need": customer_need,
        "pending_assumptions": [],
        "confirmed_assumptions": [],
        "clarification_count": 2,
        "requested_product_count": 3,
        "shown_product_ids": ["AC-M1-001", "AC-M1-002"],
        "rejected_product_ids": [],
        "ranking_cursor": 3,
        "retrieved_product_ids": ["AC-M1-001", "AC-M1-002", "AC-M1-003"],
        "eligible_product_ids": ["AC-M1-002", "AC-M1-003"],
        "excluded_products": [
            ExcludedProduct(product_id="AC-M1-001", reasons=["over_budget"])
        ],
        "role_winners": role_winners(),
        "display_product_ids": ["AC-M1-002", "AC-M1-003"],
        "recommendation_output": recommendation_output(customer_need),
        "guardrail_flags": [],
        "trace_id": "trace-1",
    }
    state.update(overrides)
    return state


def merged_need(merge_module, current, patch, **intent_kwargs):
    return merge_module.merge_customer_need(
        current, intent_output(patch, **intent_kwargs)
    )


def test_explicit_new_value_overrides_old(merge_module):
    result = merged_need(
        merge_module, need(), AirConditionerNeed(budget_max_vnd=15_000_000)
    )
    assert result.budget_max_vnd == 15_000_000


def test_omitted_fields_preserve_state(merge_module):
    result = merged_need(
        merge_module, need(), AirConditionerNeed(budget_max_vnd=15_000_000)
    )
    assert result.room_size_m2 == 18.0
    assert result.room_type == "bedroom"
    assert result.location == "HCM"
    assert [p.name for p in result.priorities] == ["energy_saving"]


def test_explicit_null_is_not_deletion(merge_module):
    result = merged_need(
        merge_module, need(), AirConditionerNeed(budget_max_vnd=None)
    )
    assert result.budget_max_vnd == 20_000_000


def test_patch_priority_overrides_same_name(merge_module):
    current = need(
        priorities=[
            NeedPriority(
                name="energy_saving", importance="secondary", source="inferred"
            ),
            NeedPriority(
                name="low_noise", importance="secondary", source="explicit"
            ),
        ]
    )
    patch = AirConditionerNeed(
        priorities=[
            NeedPriority(
                name="energy_saving", importance="primary", source="explicit"
            )
        ]
    )
    result = merged_need(merge_module, current, patch)
    by_name = {p.name: p for p in result.priorities}
    assert by_name["energy_saving"].importance == "primary"
    assert by_name["energy_saving"].source == "explicit"
    assert by_name["low_noise"].importance == "secondary"


def test_pending_assumption_superseded_by_explicit_field(merge_module):
    pending = Assumption(
        field="sunlight_exposure",
        assumed_value="normal",
        reason="not mentioned",
        impact="capacity",
        confirmation_status="unconfirmed",
    )
    state = base_state(pending_assumptions=[pending])
    state["latest_intent_output"] = intent_output(
        AirConditionerNeed(sunlight_exposure="direct")
    )
    result = merge_module.merge_state(state)
    assert result["pending_assumptions"] == []


def test_confirmed_assumptions_survive(merge_module):
    confirmed = Assumption(
        field="room_type",
        assumed_value="bedroom",
        reason="user confirmed",
        impact="noise weighting",
        confirmation_status="confirmed",
    )
    state = base_state(confirmed_assumptions=[confirmed])
    state["latest_intent_output"] = intent_output(
        AirConditionerNeed(budget_max_vnd=15_000_000)
    )
    result = merge_module.merge_state(state)
    assert result["confirmed_assumptions"] == [confirmed]


def test_clarification_count_resets_on_material_new_search(merge_module):
    state = base_state()
    state["latest_intent_output"] = intent_output(
        AirConditionerNeed(room_size_m2=25.0), intent="new_search"
    )
    result = merge_module.merge_state(state)
    assert result["clarification_count"] == 0


def test_clarification_count_preserved_without_material_change(merge_module):
    state = base_state()
    state["latest_intent_output"] = intent_output(
        AirConditionerNeed(), intent="more_recommendations"
    )
    result = merge_module.merge_state(state)
    assert result["clarification_count"] == 2


@pytest.mark.parametrize(
    "patch",
    [
        AirConditionerNeed(budget_max_vnd=12_000_000),
        AirConditionerNeed(room_size_m2=25.0),
        AirConditionerNeed(location="HN"),
        AirConditionerNeed(
            priorities=[
                NeedPriority(
                    name="low_noise", importance="primary", source="explicit"
                )
            ]
        ),
    ],
)
def test_hard_constraint_change_invalidates_derived_state(merge_module, patch):
    state = base_state()
    state["latest_intent_output"] = intent_output(
        patch, intent="change_constraints"
    )
    result = merge_module.merge_state(state)
    assert result["retrieved_product_ids"] == []
    assert result["eligible_product_ids"] == []
    assert result["excluded_products"] == []
    assert result["role_winners"] is None
    assert result["display_product_ids"] == []
    assert result["recommendation_output"] is None


def test_merge_never_touches_cursor_or_shown_ids(merge_module):
    state = base_state()
    state["latest_intent_output"] = intent_output(
        AirConditionerNeed(budget_max_vnd=12_000_000),
        intent="change_constraints",
    )
    result = merge_module.merge_state(state)
    assert result["ranking_cursor"] == 3
    assert result["shown_product_ids"] == ["AC-M1-001", "AC-M1-002"]


def test_non_hard_constraint_change_preserves_derived_state(merge_module):
    state = base_state()
    state["latest_intent_output"] = intent_output(
        AirConditionerNeed(room_type="living_room"),
        intent="change_constraints",
    )
    result = merge_module.merge_state(state)
    assert result["retrieved_product_ids"] == [
        "AC-M1-001",
        "AC-M1-002",
        "AC-M1-003",
    ]
    assert result["eligible_product_ids"] == ["AC-M1-002", "AC-M1-003"]
    assert result["role_winners"] is not None
    assert result["recommendation_output"] is not None


def test_merge_updates_intent_turn_and_requested_count(merge_module):
    state = base_state()
    output = intent_output(
        AirConditionerNeed(), intent="more_recommendations"
    )
    output = output.model_copy(update={"requested_product_count": 5})
    state["latest_intent_output"] = output
    result = merge_module.merge_state(state)
    assert result["current_intent"] == "more_recommendations"
    assert result["turn_number"] == 4
    assert result["requested_product_count"] == 5


def test_merge_state_is_pure(merge_module):
    state = base_state()
    state["latest_intent_output"] = intent_output(
        AirConditionerNeed(budget_max_vnd=12_000_000),
        intent="change_constraints",
    )
    merge_module.merge_state(state)
    assert state["customer_need"].budget_max_vnd == 20_000_000
    assert state["retrieved_product_ids"] == [
        "AC-M1-001",
        "AC-M1-002",
        "AC-M1-003",
    ]


def test_workflow_state_covers_public_advisor_state(state_module):
    workflow_keys = set(state_module.WorkflowState.__annotations__)
    public_keys = set(AdvisorState.__annotations__)
    assert public_keys <= workflow_keys
    transient_keys = {
        "latest_intent_output",
        "raw_products",
        "normalized_products",
        "evidence_by_product",
        "display_selections",
        "memory_flags",
    }
    assert transient_keys <= workflow_keys
    assert transient_keys <= set(state_module.WorkflowState.__optional_keys__)
