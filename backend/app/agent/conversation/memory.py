"""Fixed-format preference memory with three update modes (ADR-0015):
incremental patch-merge, rewrite on correction, and archive+reset on a
category switch — with restore when the user returns to a previous category."""

from backend.app.agent.contracts import AgentState, AgentUnderstanding, GenericNeed

_SESSION_FIELDS = ("brand_prefs", "location")


def merge_need(current: GenericNeed, patch: GenericNeed) -> GenericNeed:
    """US-104 semantics on the generic need: explicitly set fields win
    (corrections included), omitted fields persist, explicit null is not
    deletion. List/dict fields merge additively; restated keys replace."""
    updates: dict = {}
    explicit = patch.model_fields_set
    for field in explicit:
        value = getattr(patch, field)
        if field == "brand_prefs" and value:
            merged = list(current.brand_prefs)
            merged.extend(brand for brand in value if brand not in merged)
            updates[field] = merged
        elif field == "priorities" and value:
            merged = list(current.priorities)
            merged.extend(p for p in value if p not in merged)
            updates[field] = merged
        elif field == "attribute_constraints" and value:
            merged_map = dict(current.attribute_constraints)
            merged_map.update(value)
            updates[field] = merged_map
        elif field == "requested_roles" and value:
            updates[field] = list(value)
        elif value is not None and value != [] and value != {}:
            updates[field] = value
        # Explicit None/empty: keep the current value (not a deletion in-session).
    return current.model_copy(update=updates)


def apply_turn(state: AgentState, understanding: AgentUnderstanding) -> AgentState:
    patch = understanding.need_patch
    new_category = patch.category_code
    current_category = state.need.category_code

    if (
        new_category is not None
        and current_category is not None
        and new_category != current_category
    ):
        # Category switch: archive the current need; restore the previous need
        # for the new category when the user is returning to it.
        state.previous_needs[current_category] = state.need
        restored = state.previous_needs.pop(new_category, None)
        if restored is not None:
            base = restored
        else:
            base = GenericNeed(category_code=new_category)
            for field in _SESSION_FIELDS:
                value = getattr(state.need, field)
                if value:
                    base = base.model_copy(update={field: value})
        state.need = merge_need(base, patch)
    else:
        state.need = merge_need(state.need, patch)

    state.current_intent = understanding.intent
    state.turn_number += 1
    if understanding.intent == "new_search" and new_category is None:
        # Brand-new search without a detected category keeps the need but the
        # clarification cycle restarts for the current category.
        pass
    return state
