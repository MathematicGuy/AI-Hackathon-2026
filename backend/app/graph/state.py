"""Internal workflow state for M1; extends the frozen public AdvisorState."""

from typing import Any

from backend.app.contracts.schemas import (
    AdvisorState,
    EvidenceRef,
    IntentOutput,
    NormalizedAirConditioner,
)


class WorkflowState(AdvisorState, total=False):
    latest_intent_output: IntentOutput
    raw_products: list[dict[str, Any]]
    normalized_products: list[NormalizedAirConditioner]
    evidence_by_product: dict[str, list[EvidenceRef]]
    display_selections: list[str]
    memory_flags: list[str]
