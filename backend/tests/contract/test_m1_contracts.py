import json
from pathlib import Path
from typing import get_args

from pydantic import TypeAdapter

from backend.app.contracts.schemas import (
    EXPLANATION_MODEL,
    EXPLANATION_PROVIDER,
    INTENT_MODEL,
    AdvisorError,
    AdvisorRequest,
    AdvisorResponse,
    AdvisorState,
    AnswerType,
    BadgeKind,
    EvidenceRef,
    Intent,
    NormalizedAirConditioner,
    ProductCard,
    RecommendationRole,
)
from backend.app.graph.node_names import (
    CANONICAL_TRACE_NODES,
    CONDITIONAL_TRACE_NODES,
    INPUT_GUARD_ORDER,
    OUTPUT_GUARD_ORDER,
)


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "aircon-m1-test-data"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_frozen_enums_and_model_routing():
    assert set(get_args(Intent)) == {
        "new_search",
        "change_constraints",
        "more_recommendations",
        "compare_products",
        "product_detail",
        "check_availability",
        "stop",
        "unsupported",
    }
    assert set(get_args(RecommendationRole)) == {
        "best_overall",
        "best_value",
        "cheapest_qualified",
    }
    assert set(get_args(AnswerType)) == {
        "clarification",
        "recommendation",
        "comparison",
        "more_products",
        "product_detail",
        "no_match",
        "guardrail_block",
        "stop",
    }
    assert INTENT_MODEL == "gpt-5.4-nano"
    assert EXPLANATION_PROVIDER == "openrouter"
    assert EXPLANATION_MODEL == "deepseek/deepseek-v4-flash"


def test_executable_contract_additions():
    error = AdvisorError(
        error_code="catalog_unavailable",
        message="Tạm thời không thể tải dữ liệu.",
        retryable=True,
    )
    alternative = ProductCard(
        product_id="AC-M1-004",
        name="Alternative",
        badges=["best_for_primary_priority"],
        selection_reason="useful_distinct_alternative",
        main_selling_point="Dữ liệu kiểm thử",
        tradeoffs=["Dữ liệu tổng hợp"],
        evidence=[
            EvidenceRef(
                path="$.normalized_fixture.cspf",
                source_snapshot="synthetic-aircon-m1-2026-07-17",
            )
        ],
    )

    assert error.session_id is None
    assert alternative.selection_reason == "useful_distinct_alternative"
    assert set(get_args(BadgeKind)) == {
        "best_overall",
        "best_value",
        "cheapest_qualified",
        "best_for_primary_priority",
    }
    assert CONDITIONAL_TRACE_NODES == ("constraint_recovery",)


def test_frozen_graph_and_guardrail_order():
    assert CANONICAL_TRACE_NODES == (
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
    assert INPUT_GUARD_ORDER == (
        "word_count",
        "regex_payload",
        "nemo_input",
        "scope",
        "intent_classifier",
    )
    assert OUTPUT_GUARD_ORDER == (
        "instructor",
        "pydantic",
        "grounding",
        "business_rules",
        "nemo_output",
        "structured_response",
    )


def test_mock_request_and_response_validate_and_serialize():
    request = AdvisorRequest.model_validate(read_json(FIXTURES / "m1-request.json"))
    response = AdvisorResponse.model_validate(read_json(FIXTURES / "m1-response.json"))

    assert request.message
    assert response.data.answer_type == "recommendation"
    assert response.model_dump(mode="json")["data"]["role_winners"]["best_overall"][
        "product_id"
    ] == "AC-M1-002"
    card_ids = [card.product_id for card in response.data.product_cards]
    assert len(card_ids) == len(set(card_ids)) == 3


def test_advisor_state_freezes_required_workflow_fields():
    required = {
        "messages",
        "session_id",
        "request_id",
        "user_id",
        "turn_number",
        "current_intent",
        "customer_need",
        "pending_assumptions",
        "confirmed_assumptions",
        "clarification_count",
        "requested_product_count",
        "shown_product_ids",
        "rejected_product_ids",
        "ranking_cursor",
        "retrieved_product_ids",
        "eligible_product_ids",
        "excluded_products",
        "role_winners",
        "display_product_ids",
        "recommendation_output",
        "guardrail_flags",
        "trace_id",
    }
    assert required == set(AdvisorState.__required_keys__)
    TypeAdapter(AdvisorState)


def test_committed_catalog_has_14_valid_synthetic_products():
    catalog = read_json(DATA / "aircon-m1-catalog-enriched.json")

    assert len(catalog) == 14
    assert len({product["product_id"] for product in catalog}) == 14
    assert all(product["is_synthetic"] is True for product in catalog)
    normalized = [
        NormalizedAirConditioner.model_validate(product["normalized_fixture"])
        for product in catalog
    ]
    assert all(product.source_snapshot == "synthetic-aircon-m1-2026-07-17" for product in normalized)


def test_eval_dataset_and_manifest_match_frozen_contract():
    cases = [
        json.loads(line)
        for line in (DATA / "aircon-m1-eval-cases.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    manifest = read_json(DATA / "aircon-m1-data-validation.json")

    assert len(cases) == manifest["eval_case_count"] == 26
    assert manifest["catalog_product_count"] == 14
    assert manifest["status"] == "pass"
    assert manifest["synthetic_data_only"] is True
    assert manifest["required_intent_coverage_complete"] is True
    covered_intents = {
        case["expected"]["intent"]
        for case in cases
        if "intent" in case["expected"]
    }
    assert covered_intents == set(get_args(Intent))
    assert set(manifest["intent_coverage"]) == set(get_args(Intent))


def test_golden_winners_and_smoke_scenarios_are_frozen():
    cases = {
        case["eval_case_id"]: case
        for case in (
            json.loads(line)
            for line in (DATA / "aircon-m1-eval-cases.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
    }
    smoke = read_json(FIXTURES / "m1-smoke-scenarios.json")

    assert cases["AIRCON-M1-001"]["expected"]["role_winners"] == {
        "best_overall": "AC-M1-002",
        "best_value": "AC-M1-003",
        "cheapest_qualified": "AC-M1-006",
    }
    assert len(smoke) == 10
    assert {scenario["intent"] for scenario in smoke} <= set(get_args(Intent))
    assert {scenario["expected_answer_type"] for scenario in smoke} <= set(
        get_args(AnswerType)
    )
