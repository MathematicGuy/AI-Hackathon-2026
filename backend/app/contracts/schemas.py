from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


INTENT_MODEL = "gpt-5.4-nano"
EXPLANATION_PROVIDER = "openrouter"
EXPLANATION_MODEL = "deepseek/deepseek-v4-flash"

Intent = Literal[
    "new_search",
    "change_constraints",
    "more_recommendations",
    "compare_products",
    "product_detail",
    "check_availability",
    "stop",
    "unsupported",
]
RecommendationRole = Literal[
    "best_overall",
    "best_value",
    "cheapest_qualified",
]
BadgeKind = Literal[
    "best_overall",
    "best_value",
    "cheapest_qualified",
    "best_for_primary_priority",
]
AnswerType = Literal[
    "clarification",
    "recommendation",
    "comparison",
    "more_products",
    "product_detail",
    "no_match",
    "guardrail_block",
    "stop",
]
PriorityImportance = Literal["primary", "secondary"]
PrioritySource = Literal["explicit", "inferred"]
StockStatus = Literal["available", "unavailable", "unknown"]
WorthPayingMore = Literal["yes", "no", "conditional", "insufficient_data"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdvisorRequest(ContractModel):
    session_id: str | None = None
    request_id: str | None = None
    user_id: str | None = None
    message: str = Field(min_length=1)
    region_code: str | None = None


class AdvisorError(ContractModel):
    session_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    error_code: str
    message: str
    retryable: bool


class NeedPriority(ContractModel):
    name: str
    importance: PriorityImportance
    source: PrioritySource = "explicit"


class AirConditionerNeed(ContractModel):
    category: Literal["air_conditioner"] = "air_conditioner"
    budget_max_vnd: int | None = Field(default=None, ge=0)
    room_size_m2: float | None = Field(default=None, gt=0)
    room_type: str | None = None
    sunlight_exposure: str | None = None
    location: str | None = None
    priorities: list[NeedPriority] = Field(default_factory=list)


class IntentOutput(ContractModel):
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    requested_product_count: int = Field(default=3, ge=1, le=10)
    constraints_changed: bool = False
    need_patch: AirConditionerNeed


class Assumption(ContractModel):
    field: str
    assumed_value: Any
    reason: str
    impact: str
    confirmation_status: Literal["unconfirmed", "confirmed", "rejected"]


class EvidenceRef(ContractModel):
    path: str
    source_snapshot: str


class NormalizedAirConditioner(ContractModel):
    product_id: str
    external_key: str
    name: str
    brand: str
    model: str | None = None
    sale_price_vnd: int | None = Field(default=None, ge=0)
    list_price_vnd: int | None = Field(default=None, ge=0)
    discount_percent: float | None = Field(default=None, ge=0)
    region_code: str | None = None
    stock_status: StockStatus
    horsepower_hp: float | None = Field(default=None, gt=0)
    cooling_capacity_btu: int | None = Field(default=None, gt=0)
    recommended_room_area_min_m2: float | None = Field(default=None, ge=0)
    recommended_room_area_max_m2: float | None = Field(default=None, ge=0)
    inverter: bool | None = None
    cspf: float | None = Field(default=None, ge=0)
    energy_label_stars: int | None = Field(default=None, ge=0)
    rated_power_w: float | None = Field(default=None, ge=0)
    annual_energy_kwh: float | None = Field(default=None, ge=0)
    indoor_noise_min_db: float | None = Field(default=None, ge=0)
    indoor_noise_max_db: float | None = Field(default=None, ge=0)
    warranty_months: int | None = Field(default=None, ge=0)
    installation_cost_vnd: int | None = Field(default=None, ge=0)
    promotion_text: str | None = None
    technical_specifications: dict[str, Any] = Field(default_factory=dict)
    product_information: dict[str, Any] = Field(default_factory=dict)
    rating: float | None = Field(default=None, ge=0)
    sold_count: int | None = Field(default=None, ge=0)
    source_url: HttpUrl
    source_snapshot: str


class ExcludedProduct(ContractModel):
    product_id: str
    reasons: list[str] = Field(min_length=1)


class FilterResult(ContractModel):
    eligible_products: list[NormalizedAirConditioner]
    excluded_products: list[ExcludedProduct]


class ProductSearchResult(ContractModel):
    products: list[dict[str, Any]]
    next_cursor: int | None = Field(default=None, ge=0)
    total_candidates: int = Field(ge=0)
    has_more: bool
    source_snapshot: str


class RoleWinner(ContractModel):
    product_id: str
    role: RecommendationRole
    score: float | None
    evidence: list[EvidenceRef] = Field(min_length=1)
    reason_codes: list[str] = Field(min_length=1)


class RoleWinners(ContractModel):
    best_overall: RoleWinner
    best_value: RoleWinner
    cheapest_qualified: RoleWinner

    @model_validator(mode="after")
    def roles_match_fields(self):
        expected = {
            "best_overall": self.best_overall,
            "best_value": self.best_value,
            "cheapest_qualified": self.cheapest_qualified,
        }
        for field_name, winner in expected.items():
            if winner.role != field_name:
                raise ValueError(f"{field_name} winner has role {winner.role}")
        return self


class ProductCard(ContractModel):
    product_id: str
    name: str
    badges: list[BadgeKind] = Field(min_length=1)
    selection_reason: str | None = None
    brand: str | None = None
    model: str | None = None
    sale_price_vnd: int | None = Field(default=None, ge=0)
    stock_status: StockStatus = "unknown"
    why_it_fits: str | None = None
    main_selling_point: str
    practical_benefit: str | None = None
    tradeoffs: list[str] = Field(min_length=1)
    when_not_to_choose: str | None = None
    evidence: list[EvidenceRef] = Field(min_length=1)


class PricePremiumVerdict(ContractModel):
    product_id: str
    compared_with_product_id: str
    verdict: WorthPayingMore
    reason: str
    evidence: list[EvidenceRef]


class ProductCitation(ContractModel):
    product_id: str
    path: str
    source_url: HttpUrl | None = None


class RecommendationOutput(ContractModel):
    answer_type: AnswerType
    intent: Intent
    customer_need: AirConditionerNeed
    assumption_summary: list[Assumption] = Field(default_factory=list)
    clarification_question: str | None = None
    role_winners: RoleWinners | None = None
    product_cards: list[ProductCard] = Field(default_factory=list)
    price_premium_verdicts: list[PricePremiumVerdict] = Field(default_factory=list)
    next_question: str | None = None
    citations: list[ProductCitation] = Field(default_factory=list)
    has_more_products: bool = False
    next_cursor: int | None = Field(default=None, ge=0)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def product_cards_are_unique(self):
        product_ids = [card.product_id for card in self.product_cards]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("product_cards must be unique by product_id")
        return self


class AdvisorResponse(ContractModel):
    session_id: str
    request_id: str
    trace_id: str
    data: RecommendationOutput


class AdvisorState(TypedDict):
    messages: list[Any]
    session_id: str
    request_id: str
    user_id: str | None
    turn_number: int
    current_intent: Intent
    customer_need: AirConditionerNeed
    pending_assumptions: list[Assumption]
    confirmed_assumptions: list[Assumption]
    clarification_count: int
    requested_product_count: int
    shown_product_ids: list[str]
    rejected_product_ids: list[str]
    ranking_cursor: int
    retrieved_product_ids: list[str]
    eligible_product_ids: list[str]
    excluded_products: list[ExcludedProduct]
    role_winners: RoleWinners | None
    display_product_ids: list[str]
    recommendation_output: RecommendationOutput | None
    guardrail_flags: list[str]
    trace_id: str
