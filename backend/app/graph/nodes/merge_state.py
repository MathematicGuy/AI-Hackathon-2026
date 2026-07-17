"""Pure state-merge node: correction precedence and ranking invalidation."""

from backend.app.contracts.schemas import (
    AirConditionerNeed,
    IntentOutput,
    NeedPriority,
)
from backend.app.graph.state import WorkflowState

HARD_CONSTRAINT_FIELDS = ("budget_max_vnd", "room_size_m2", "location")


def _explicit_fields(intent_output: IntentOutput) -> set[str]:
    return intent_output.need_patch.model_fields_set - {"category"}


def _merge_priorities(
    current: list[NeedPriority], patched: list[NeedPriority]
) -> list[NeedPriority]:
    patched_names = {priority.name for priority in patched}
    kept = [
        priority for priority in current if priority.name not in patched_names
    ]
    return list(patched) + kept


def _primary_names(need: AirConditionerNeed) -> set[str]:
    return {
        priority.name
        for priority in need.priorities
        if priority.importance == "primary"
    }


def _hard_constraint_changed(
    current: AirConditionerNeed, merged: AirConditionerNeed
) -> bool:
    for field in HARD_CONSTRAINT_FIELDS:
        if getattr(current, field) != getattr(merged, field):
            return True
    return _primary_names(current) != _primary_names(merged)


def merge_customer_need(
    current: AirConditionerNeed, intent_output: IntentOutput
) -> AirConditionerNeed:
    patch = intent_output.need_patch
    updates = {}
    for field in _explicit_fields(intent_output):
        if field == "priorities":
            updates["priorities"] = _merge_priorities(
                current.priorities, patch.priorities
            )
            continue
        value = getattr(patch, field)
        if value is None:
            # Explicit null is not deletion in M1; keep the current value.
            continue
        updates[field] = value
    return current.model_copy(update=updates)


def merge_state(state: WorkflowState) -> WorkflowState:
    intent_output = state["latest_intent_output"]
    current_need = state["customer_need"]
    merged_need = merge_customer_need(current_need, intent_output)
    explicit = _explicit_fields(intent_output)

    result = dict(state)
    result["customer_need"] = merged_need
    result["current_intent"] = intent_output.intent
    result["turn_number"] = state["turn_number"] + 1
    result["requested_product_count"] = intent_output.requested_product_count
    result["pending_assumptions"] = [
        assumption
        for assumption in state["pending_assumptions"]
        if assumption.field not in explicit
    ]

    if _hard_constraint_changed(current_need, merged_need):
        result["retrieved_product_ids"] = []
        result["eligible_product_ids"] = []
        result["excluded_products"] = []
        result["role_winners"] = None
        result["display_product_ids"] = []
        result["recommendation_output"] = None

    if intent_output.intent == "new_search" and merged_need != current_need:
        result["clarification_count"] = 0

    return result
