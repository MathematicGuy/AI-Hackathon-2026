"""E02 agent contracts: intents, the fixed-format need, and session state.

`GenericNeed` is THE fixed format for user preferences/requirements
(ADR-0015). It updates in three modes handled by `conversation.memory`:
incremental patch-merge, rewrite on correction, and archive+reset on a
category/shopping-intent switch (recoverable via `previous_needs`).
"""

from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AgentIntent = Literal[
    "new_search",
    "change_constraints",
    "more_recommendations",
    "compare_products",
    "product_detail",
    "check_availability",
    "policy_question",
    "stop",
    "unsupported",
]

# Default suggestion roles (Cường 2026-07-18): best price, best value, best
# performance — unless the user explicitly requests otherwise.
SuggestionRole = Literal["best_price", "best_value", "best_performance"]
DEFAULT_ROLES: tuple[str, ...] = ("best_price", "best_value", "best_performance")
PresentationType = Literal["text", "recommendation", "comparison"]
PresentationMessage = Annotated[str, Field(min_length=1, max_length=500)]


class GenericNeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_code: str | None = None
    usage_purpose: str | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    brand_prefs: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    attribute_constraints: dict[str, str] = Field(default_factory=dict)
    location: str | None = None
    requested_roles: list[str] = Field(default_factory=list)


class AgentUnderstanding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: AgentIntent
    confidence: float = Field(ge=0, le=1)
    need_patch: GenericNeed = Field(default_factory=GenericNeed)
    product_refs: list[str] = Field(default_factory=list)


class PresentationBadge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=120)


class PresentationHighlight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=120)
    value: str | None = Field(default=None, max_length=500)


class PresentedProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1, max_length=128)
    productidweb: str | None = Field(default=None, min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=300)
    brand: str | None = Field(default=None, max_length=120)
    effective_price_vnd: int | None = Field(default=None, ge=0)
    list_price_vnd: int | None = Field(default=None, ge=0)
    discount_percent: float | None = Field(default=None, ge=0, le=100)
    promotion_text: str | None = Field(default=None, max_length=500)
    badges: list[PresentationBadge] = Field(default_factory=list, max_length=10)
    highlights: list[PresentationHighlight] = Field(default_factory=list, max_length=3)
    image_url: str | None = Field(default=None, max_length=2048)
    product_url: str | None = Field(default=None, max_length=2048)
    rating: float | None = Field(default=None, ge=0, le=5)
    sold_count: int | None = Field(default=None, ge=0)


class ComparisonValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str = Field(min_length=1, max_length=128)
    value: str | None = Field(default=None, max_length=500)


class ComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=120)
    values: list[ComparisonValue] = Field(default_factory=list, max_length=10)


class AgentPresentation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: PresentationType = "text"
    products: list[PresentedProduct] = Field(default_factory=list, max_length=10)
    comparison_rows: list[ComparisonRow] = Field(default_factory=list, max_length=7)
    follow_up_questions: list[PresentationMessage] = Field(
        default_factory=list, max_length=1
    )
    warnings: list[PresentationMessage] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_shape(self) -> "AgentPresentation":
        skus = [product.sku for product in self.products]
        if len(skus) != len(set(skus)):
            raise ValueError("presentation product SKUs must be unique")
        if self.type == "text":
            if self.products or self.comparison_rows:
                raise ValueError("text presentation cannot contain products or rows")
            return self
        if self.type == "recommendation":
            if not self.products:
                raise ValueError("recommendation presentation requires products")
            if self.comparison_rows:
                raise ValueError("recommendation presentation cannot contain rows")
            return self
        if len(self.products) < 2:
            raise ValueError("comparison presentation requires at least two products")
        expected_skus = set(skus)
        for row in self.comparison_rows:
            row_skus = [value.sku for value in row.values]
            if len(row_skus) != len(skus) or set(row_skus) != expected_skus:
                raise ValueError(
                    "comparison rows require exactly one value per product SKU"
                )
        return self


@dataclass
class AgentState:
    session_id: str = "local"
    turn_number: int = 0
    current_intent: str = "new_search"
    need: GenericNeed = field(default_factory=GenericNeed)
    previous_needs: dict[str, GenericNeed] = field(default_factory=dict)
    asked_questions: dict[str, list[str]] = field(default_factory=dict)
    clarification_count: dict[str, int] = field(default_factory=dict)
    shown_product_ids: dict[str, list[str]] = field(default_factory=dict)
    rejected_product_ids: dict[str, list[str]] = field(default_factory=dict)
    # Product memory: the concrete records last presented, so follow-ups like
    # "cái thứ hai" or comparisons can resolve without a new search.
    last_presented_ids: list[str] = field(default_factory=list)
    # The cold-start question awaiting an answer; the next reply that carries
    # no structured signal is captured as this question's answer.
    pending_question_key: str | None = None
    guardrail_flags: list[str] = field(default_factory=list)

    @property
    def category_code(self) -> str | None:
        return self.need.category_code

    def asked_for(self, category_code: str) -> list[str]:
        return self.asked_questions.setdefault(category_code, [])

    def shown_for(self, category_code: str) -> list[str]:
        return self.shown_product_ids.setdefault(category_code, [])
