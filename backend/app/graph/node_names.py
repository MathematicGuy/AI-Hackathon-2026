CANONICAL_TRACE_NODES = (
    "input_guardrail",
    "intent_classifier",
    "state_merge",
    "intent_router",
    "clarification_decision",
    "product_search",
    "product_normalization",
    "hard_constraint_filter",
    "availability_decision",
    "best_overall_ranking",
    "best_value_ranking",
    "cheapest_qualified_ranking",
    "ui_deduplication",
    "response_generation",
    "output_validation",
    "next_question_selection",
    "memory_write",
)

CONDITIONAL_TRACE_NODES = ("constraint_recovery",)

INPUT_GUARD_ORDER = (
    "word_count",
    "regex_payload",
    "nemo_input",
    "scope",
    "intent_classifier",
)

OUTPUT_GUARD_ORDER = (
    "instructor",
    "pydantic",
    "grounding",
    "business_rules",
    "nemo_output",
    "structured_response",
)
