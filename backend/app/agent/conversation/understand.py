"""Turn understanding: injected LLM extractor with a deterministic Vietnamese
keyword fallback (never invents numbers; flags degradation)."""

import re
from typing import Protocol

from pydantic import ValidationError

from backend.app.agent.catalog.registry import CategoryRegistry
from backend.app.agent.contracts import AgentUnderstanding, GenericNeed

FALLBACK_CONFIDENCE = 0.3

_STOP = ("dừng", "thôi khỏi", "không cần nữa", "kết thúc", "tạm biệt")
_POLICY = (
    "chính sách", "bảo hành", "đổi trả", "hoàn tiền", "trả góp",
    "khui hộp", "điều khoản", "dữ liệu cá nhân", "đổi máy", "lắp đặt mất phí",
    "phí giao", "giao hàng bao lâu", "phí lắp",
)
_COMPARE = ("so sánh", "so với", "đối chiếu", "hơn kém")
_CHANGE = ("đổi ngân sách", "thay đổi", "chuyển sang tầm", "nâng ngân sách", "hạ ngân sách")
_MORE = ("xem thêm", "thêm mẫu", "mẫu khác", "còn mẫu", "gợi ý thêm", "rẻ hơn nữa")
_AVAILABILITY = ("còn hàng", "tình trạng kho", "hết hàng", "có sẵn")
_DETAIL = ("chi tiết", "thông số", "thông tin sản phẩm", "xem kỹ")

_BUDGET = re.compile(
    r"(?:dưới|khoảng|tầm|từ)?\s*(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(triệu|tr\b|k\b|nghìn|ngàn)",
    re.IGNORECASE,
)


class UnderstandingExtractor(Protocol):
    async def extract(self, message: str, *, state_summary: str) -> AgentUnderstanding: ...


class ExtractorError(Exception):
    """Raised by extractors on provider/transport failure."""


def _parse_budget_vnd(text: str) -> tuple[int | None, int | None]:
    """Deterministic budget parse for the fallback path only; understands
    'dưới 20 triệu', 'tầm 15tr', '18-20 triệu'. Returns (min, max)."""
    low = text.lower()
    range_match = re.search(
        r"(\d{1,3})\s*[-–đến\s]+\s*(\d{1,3})\s*(triệu|tr\b)", low
    )
    if range_match:
        a, b = int(range_match.group(1)), int(range_match.group(2))
        lo, hi = min(a, b), max(a, b)
        return lo * 1_000_000, hi * 1_000_000
    match = _BUDGET.search(low)
    if not match:
        return None, None
    amount = int(re.sub(r"[.,]", "", match.group(1)))
    unit = match.group(2).strip()
    value = amount * 1_000_000 if unit.startswith(("tr", "triệu")) else amount * 1_000
    prefix = low[max(0, match.start() - 12): match.start()]
    if "từ" in prefix:
        return value, None
    return None, value


def fallback_understanding(
    message: str, *, registry: CategoryRegistry | None = None
) -> AgentUnderstanding:
    registry = registry or CategoryRegistry()
    low = message.lower()

    category = registry.detect(message)
    budget_min, budget_max = _parse_budget_vnd(message)
    need_kwargs: dict = {}
    if category is not None:
        need_kwargs["category_code"] = category.code
    if budget_min is not None:
        need_kwargs["budget_min"] = budget_min
    if budget_max is not None:
        need_kwargs["budget_max"] = budget_max
    if "rẻ nhất" in low or "giá thấp nhất" in low:
        need_kwargs["requested_roles"] = ["best_price"]

    if any(k in low for k in _STOP):
        intent = "stop"
    elif any(k in low for k in _POLICY):
        intent = "policy_question"
    elif any(k in low for k in _COMPARE):
        intent = "compare_products"
    elif any(k in low for k in _CHANGE):
        intent = "change_constraints"
    elif any(k in low for k in _MORE):
        intent = "more_recommendations"
    elif any(k in low for k in _AVAILABILITY):
        intent = "check_availability"
    elif any(k in low for k in _DETAIL):
        intent = "product_detail"
    elif category is not None:
        intent = "new_search"
    elif budget_min is not None or budget_max is not None:
        intent = "change_constraints"
    else:
        intent = "unsupported"

    return AgentUnderstanding(
        intent=intent,
        confidence=FALLBACK_CONFIDENCE,
        need_patch=GenericNeed(**need_kwargs),
    )


async def understand_turn(
    message: str,
    *,
    extractor: UnderstandingExtractor | None,
    state_summary: str = "",
    registry: CategoryRegistry | None = None,
) -> tuple[AgentUnderstanding, list[str]]:
    if extractor is not None:
        try:
            return await extractor.extract(message, state_summary=state_summary), []
        except (ExtractorError, ValidationError):
            pass
    flags = ["understanding_degraded"] if extractor is not None else []
    return fallback_understanding(message, registry=registry), flags
