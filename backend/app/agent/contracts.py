"""E02 agent contracts: intents, the fixed-format need, and session state.

`GenericNeed` is THE fixed format for user preferences/requirements
(ADR-0015). It updates in three modes handled by `conversation.memory`:
incremental patch-merge, rewrite on correction, and archive+reset on a
category/shopping-intent switch (recoverable via `previous_needs`).
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
    guardrail_flags: list[str] = field(default_factory=list)

    @property
    def category_code(self) -> str | None:
        return self.need.category_code

    def asked_for(self, category_code: str) -> list[str]:
        return self.asked_questions.setdefault(category_code, [])

    def shown_for(self, category_code: str) -> list[str]:
        return self.shown_product_ids.setdefault(category_code, [])
