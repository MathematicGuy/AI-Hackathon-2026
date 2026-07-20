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
    "catalog_overview",
    "price_range_query",
    "promotion_inquiry",
    "smalltalk",
    "question_clarification",
    "product_qa",
    "stop",
    "unsupported",
]

# Default suggestion roles (Cường 2026-07-18): best price, best value, best
# performance — unless the user explicitly requests otherwise ("rẻ nhất" →
# best_price only, "đắt nhất/cao cấp nhất" → most_expensive).
SuggestionRole = Literal[
    "best_price", "best_value", "best_performance", "most_expensive"
]
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
    # Explicit deletions ("bỏ giới hạn giá") — merge semantics treat None as
    # "keep", so removals need their own channel. Currently: "budget".
    clear_fields: list[str] = Field(default_factory=list)



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
    # no structured signal is captured as this question's answer. The text is
    # kept alongside the key so the extractor sees the actual question and an
    # echo of it ("mục đích sử dụng tủ lạnh á?") can be told apart from an
    # answer.
    pending_question_key: str | None = None
    pending_question_text: str | None = None
    # Last few (user, bot) exchanges, trimmed — conversation context for the
    # LLM extractor.
    recent_turns: list[tuple[str, str]] = field(default_factory=list)
    guardrail_flags: list[str] = field(default_factory=list)

    @property
    def category_code(self) -> str | None:
        return self.need.category_code

    def asked_for(self, category_code: str) -> list[str]:
        return self.asked_questions.setdefault(category_code, [])

    def shown_for(self, category_code: str) -> list[str]:
        return self.shown_product_ids.setdefault(category_code, [])

    # --- durable session memory (JSON write-through; live-test 4) ---
    # Only the fields that constitute the customer's memory persist; per-turn
    # ephemera (guardrail flags, recent turns) stay in-process.

    def to_json_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "turn_number": self.turn_number,
            "current_intent": self.current_intent,
            "need": self.need.model_dump(),
            "previous_needs": {
                category: need.model_dump()
                for category, need in self.previous_needs.items()
            },
            "asked_questions": dict(self.asked_questions),
            "clarification_count": dict(self.clarification_count),
            "shown_product_ids": dict(self.shown_product_ids),
            "rejected_product_ids": dict(self.rejected_product_ids),
            "last_presented_ids": list(self.last_presented_ids),
            "pending_question_key": self.pending_question_key,
            "pending_question_text": self.pending_question_text,
        }

    @classmethod
    def from_json_dict(cls, payload: dict) -> "AgentState":
        return cls(
            session_id=payload.get("session_id", "local"),
            turn_number=payload.get("turn_number", 0),
            current_intent=payload.get("current_intent", "new_search"),
            need=GenericNeed(**payload.get("need", {})),
            previous_needs={
                category: GenericNeed(**need)
                for category, need in payload.get("previous_needs", {}).items()
            },
            asked_questions=dict(payload.get("asked_questions", {})),
            clarification_count=dict(payload.get("clarification_count", {})),
            shown_product_ids=dict(payload.get("shown_product_ids", {})),
            rejected_product_ids=dict(payload.get("rejected_product_ids", {})),
            last_presented_ids=list(payload.get("last_presented_ids", [])),
            pending_question_key=payload.get("pending_question_key"),
            pending_question_text=payload.get("pending_question_text"),
        )
