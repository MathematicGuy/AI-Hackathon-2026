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
_CATALOG_OVERVIEW = (
    "bán cái gì", "bán những gì", "có những loại hàng", "loại hàng nào",
    "có những ngành", "danh mục", "những mặt hàng", "mặt hàng nào",
    "có loại nào", "những sản phẩm gì",
)
_PRICE_RANGE = (
    "range giá", "tầm giá bao nhiêu", "giá rơi vào", "giá từ bao nhiêu",
    "khoảng giá", "giá dao động", "vùng giá",
)
_PROMOTION_INQUIRY = (
    "chương trình khuyến mãi", "đang có khuyến mãi", "khuyến mãi nào",
    "khuyến mãi gì", "ưu đãi gì", "ưu đãi nào", "đang giảm giá nào",
)
_SMALLTALK = (
    "cảm ơn", "cám ơn", "chào em", "xin chào", "hello", "hi em",
    "nóng quá", "lạnh quá", "nóng bức", "oi bức", "mưa quá",
    "đồng ý", "ok em", "oke", "được đó", "hay đấy", "tốt quá", "ừ em",
)

# Money units tolerate live-chat typos: "trịu", "trieu", bare "tr", "củ".
_MILLION_UNIT = r"triệu|trịu|trieu|tr\b|củ\b"
_BUDGET = re.compile(
    r"(?:dưới|khoảng|tầm|từ)?\s*(\d{1,3}(?:[.,]\d{3})*|\d+)\s*"
    rf"({_MILLION_UNIT}|k\b|nghìn|ngàn)",
    re.IGNORECASE,
)

# "đắt nhất/mắc nhất/xịn nhất" — the customer wants the top-priced model.
_MOST_EXPENSIVE = ("đắt nhất", "mắc nhất", "xịn nhất", "cao cấp nhất")
# Generic product references that mean "continue this consultation".
_CONTINUATION_HINTS = ("máy", "mẫu", "cái", "con", "em nó", "sản phẩm", "loại")

# Obvious usage purposes the deterministic fallback can extract safely.
_PURPOSE_MARKERS = (
    "gaming", "chơi game", "văn phòng", "đồ họa", "học online", "cho bé học",
    "livestream", "thể thao", "kinh doanh", "gia đình", "làm việc",
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
        rf"(\d{{1,3}})\s*[-–đến\s]+\s*(\d{{1,3}})\s*({_MILLION_UNIT})", low
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
    value = (
        amount * 1_000_000
        if unit.startswith(("tr", "củ")) or unit in ("triệu", "trịu", "trieu")
        else amount * 1_000
    )
    prefix = low[max(0, match.start() - 12): match.start()]
    if "từ" in prefix:
        return value, None
    return None, value


def fallback_understanding(
    message: str,
    *,
    registry: CategoryRegistry | None = None,
    active_category: str | None = None,
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
    if any(
        k in low for k in ("rẻ nhất", "giá thấp nhất", "rẻ càng tốt", "càng rẻ")
    ):
        need_kwargs["requested_roles"] = ["best_price"]
    elif any(k in low for k in _MOST_EXPENSIVE):
        need_kwargs["requested_roles"] = ["most_expensive"]
    for purpose in _PURPOSE_MARKERS:
        if purpose in low:
            need_kwargs["usage_purpose"] = purpose
            break

    # Price/promotion questions are catalog questions, never policy — even if
    # the LLM route is down (Cường's live-test finding).
    if any(k in low for k in _STOP):
        intent = "stop"
    elif any(k in low for k in _PRICE_RANGE):
        intent = "price_range_query"
    elif any(k in low for k in _PROMOTION_INQUIRY):
        intent = "promotion_inquiry"
    elif any(k in low for k in _CATALOG_OVERVIEW):
        intent = "catalog_overview"
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
    elif any(k in low for k in _MOST_EXPENSIVE) and (
        category is not None or active_category is not None
    ):
        intent = "more_recommendations"
    elif category is not None:
        intent = "new_search"
    elif budget_min is not None or budget_max is not None:
        intent = "change_constraints"
    elif any(k in low for k in _SMALLTALK):
        intent = "smalltalk"
    elif active_category is not None and any(
        hint in low for hint in _CONTINUATION_HINTS
    ):
        # Mid-consultation follow-up that names no category and matches no
        # marker ("máy đắt nhất đi em") — stay in the product flow instead of
        # dumping the category menu (Cường's live-test 2 finding).
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
    active_category: str | None = None,
) -> tuple[AgentUnderstanding, list[str]]:
    if extractor is not None:
        try:
            return await extractor.extract(message, state_summary=state_summary), []
        except (ExtractorError, ValidationError):
            pass
    flags = ["understanding_degraded"] if extractor is not None else []
    return (
        fallback_understanding(
            message, registry=registry, active_category=active_category
        ),
        flags,
    )
