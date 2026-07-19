"""Turn understanding: injected LLM extractor with a deterministic Vietnamese
keyword fallback (never invents numbers; flags degradation)."""

import re
from typing import Protocol

from pydantic import ValidationError

from backend.app.agent.catalog.registry import CategoryRegistry
from backend.app.agent.contracts import AgentUnderstanding, GenericNeed
from backend.app.observability import AgentObserver, noop_agent_observer

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

# Bare agreement tokens — a whole-message exact match ("ok", "ừ") is small
# talk agreement, never unsupported (live-test 4: short messages must flow).
_AGREEMENT_TOKENS = {
    "ok", "oke", "okê", "okie", "ừ", "uh", "ừm", "um", "dạ", "vâng",
    "đồng ý", "yes", "được",
}

# The customer wants the stated price window GONE ("không tra trong mức đó
# nữa") — merge semantics cannot delete, so this raises clear_fields.
# OLDREF phrases reference the PREVIOUS window: any number in the sentence
# ("không tra trong mức 15 triệu nữa") is the old value, never a new budget.
_BUDGET_CLEAR_OLDREF = (
    "không tra trong mức", "ngoài mức giá", "bỏ tầm giá", "bỏ khoảng giá",
    "bỏ giới hạn giá", "bỏ giới hạn ngân sách",
)
_BUDGET_CLEAR = _BUDGET_CLEAR_OLDREF + (
    "không giới hạn giá", "không giới hạn ngân sách", "thoải mái ngân sách",
    "khoảng giá khác", "tầm giá khác", "đừng lọc giá",
)

# Same clear semantics for the other sticky preferences (audit round 5).
_BRAND_CLEAR = ("hãng nào cũng được", "bỏ hãng", "không cần hãng", "hãng gì cũng được")
_PRIORITY_CLEAR = ("bỏ ưu tiên", "không cần ưu tiên", "ưu tiên gì cũng được")
_ROLE_CLEAR = (
    "gợi ý bình thường", "tư vấn bình thường", "đừng chỉ rẻ nhất",
    "đủ các lựa chọn", "như ban đầu", "đầy đủ các vai",
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

# Screen-size mention ("24-27 inch", "27 inch", '24"') — captured as a size
# constraint for screen categories (monitor 73, tablet 30).
_SIZE_INCH = re.compile(
    r"(\d{1,2}(?:[.,]\d)?)\s*(?:-|–|đến\s*)?\s*(\d{1,2}(?:[.,]\d)?)?\s*(?:inch|in\b|\")",
    re.IGNORECASE,
)
_SCREEN_CATEGORIES = ("73", "30")

# Room area ("phòng 18m2", "20 m²") — feeds the air-conditioner coverage rule.
_ROOM_AREA = re.compile(r"(\d{1,3})\s*m(?:²|2)\b", re.IGNORECASE)
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


# Bound direction from context: "trên 10 triệu" is a FLOOR, "dưới"/no prefix
# a ceiling; suffixes "trở lên"/"đổ lại" flip likewise (audit round 5 — the
# old parser only knew "từ" and read "trên 10 triệu" as a maximum).
_MIN_PREFIXES = ("từ", "trên", "hơn", "tối thiểu", "ít nhất", "khởi điểm")
_MIN_SUFFIXES = ("trở lên", "đổ lên")
_MAX_SUFFIXES = ("đổ lại", "trở xuống", "đổ xuống")
# Compact forms: "1tr5" = 1.5 triệu; "3 triệu rưỡi" = 3.5 triệu.
_COMPACT_TR = re.compile(r"(\d{1,3})\s*tr\s*(\d)\b")
_HALF = re.compile(rf"(\d{{1,3}})\s*(?:{_MILLION_UNIT})\s*rưỡi")


def _bound_from_context(low: str, start: int, end: int, value: int):
    # The window includes the match itself: _BUDGET's optional prefix group
    # consumes "từ/dưới..." so a before-start window would never see it
    # (latent since round 1 — "từ 8 triệu" parsed as a ceiling).
    prefix = low[max(0, start - 14): end]
    suffix = low[end: end + 14]
    if any(s in suffix for s in _MIN_SUFFIXES):
        return value, None
    if any(s in suffix for s in _MAX_SUFFIXES):
        return None, value
    if any(p in prefix for p in _MIN_PREFIXES):
        return value, None
    return None, value


def _parse_budget_vnd(text: str) -> tuple[int | None, int | None]:
    """Deterministic budget parse for the fallback path only; understands
    'dưới 20 triệu', 'trên 10 triệu' (floor), 'tầm 15tr', '18-20 triệu',
    '1tr5', '3 triệu rưỡi'. Returns (min, max)."""
    low = text.lower()
    range_match = re.search(
        rf"(\d{{1,3}})\s*[-–đến\s]+\s*(\d{{1,3}})\s*({_MILLION_UNIT})", low
    )
    if range_match:
        a, b = int(range_match.group(1)), int(range_match.group(2))
        lo, hi = min(a, b), max(a, b)
        return lo * 1_000_000, hi * 1_000_000
    half_match = _HALF.search(low)
    if half_match:
        value = int(half_match.group(1)) * 1_000_000 + 500_000
        return _bound_from_context(low, half_match.start(), half_match.end(), value)
    compact_match = _COMPACT_TR.search(low)
    if compact_match:
        value = (
            int(compact_match.group(1)) * 1_000_000
            + int(compact_match.group(2)) * 100_000
        )
        return _bound_from_context(
            low, compact_match.start(), compact_match.end(), value
        )
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
    return _bound_from_context(low, match.start(), match.end(), value)


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
    effective_category = (
        category.code if category is not None else active_category
    )
    if effective_category in _SCREEN_CATEGORIES:
        size_match = _SIZE_INCH.search(low)
        if size_match:
            need_kwargs["attribute_constraints"] = {"size": size_match.group(0)}
    elif effective_category == "36":
        area_match = _ROOM_AREA.search(low)
        if area_match:
            need_kwargs["attribute_constraints"] = {
                "room_area": area_match.group(0)
            }

    # A budget-clear phrase lifts the price window. OLDREF phrases treat any
    # number in the sentence as the OLD window ("không tra trong mức 15 triệu
    # nữa" must not re-set 15tr); other clear phrases with a new number let
    # the parsed budget override instead.
    clear_fields: list[str] = []
    if any(k in low for k in _BUDGET_CLEAR_OLDREF):
        clear_fields.append("budget")
        need_kwargs.pop("budget_min", None)
        need_kwargs.pop("budget_max", None)
        budget_min = budget_max = None
    elif (
        any(k in low for k in _BUDGET_CLEAR)
        and budget_min is None
        and budget_max is None
    ):
        clear_fields.append("budget")
    if any(k in low for k in _BRAND_CLEAR):
        clear_fields.append("brands")
    if any(k in low for k in _PRIORITY_CLEAR):
        clear_fields.append("priorities")
    if any(k in low for k in _ROLE_CLEAR) and not need_kwargs.get(
        "requested_roles"
    ):
        clear_fields.append("roles")

    # Price/promotion questions are catalog questions, never policy — even if
    # the LLM route is down (Cường's live-test finding).
    if low.strip(" .!~") in _AGREEMENT_TOKENS:
        intent = "smalltalk"
    elif clear_fields:
        intent = "change_constraints"
    elif any(k in low for k in _STOP):
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
        clear_fields=clear_fields,
    )


def _augment_understanding(
    message: str,
    understanding: AgentUnderstanding,
    *,
    active_category: str | None,
) -> AgentUnderstanding:
    """Fill fields the LLM missed using the deterministic extractors — never
    override what the model DID return (live finding: the model skipped
    'phòng 18m2' and the room got re-asked)."""
    patch = understanding.need_patch
    low = message.lower()
    updates: dict = {}
    oldref_clear = any(k in low for k in _BUDGET_CLEAR_OLDREF)
    if oldref_clear:
        # Any number in an old-reference clear sentence is the OLD window —
        # neutralize a budget the model may have re-parsed from it.
        if patch.budget_min is not None:
            updates["budget_min"] = None
        if patch.budget_max is not None:
            updates["budget_max"] = None
    elif patch.budget_min is None and patch.budget_max is None:
        budget_min, budget_max = _parse_budget_vnd(message)
        if budget_min is not None:
            updates["budget_min"] = budget_min
        if budget_max is not None:
            updates["budget_max"] = budget_max
    elif patch.budget_min is not None and patch.budget_max is None:
        # The model keeps reading bare amounts ("tầm 40 triệu") as floors.
        # Our context parser is authoritative on bound direction: when it
        # says ceiling-only for this message, flip the misread (genuine
        # floor phrases like "trên 40 triệu" parse as (X, None) and stand).
        det_min, det_max = _parse_budget_vnd(message)
        if det_min is None and det_max is not None:
            updates["budget_min"] = None
            updates["budget_max"] = det_max
    category = patch.category_code or active_category
    constraints = dict(patch.attribute_constraints)
    if category in _SCREEN_CATEGORIES and "size" not in constraints:
        size_match = _SIZE_INCH.search(low)
        if size_match:
            constraints["size"] = size_match.group(0)
    elif category == "36" and "room_area" not in constraints:
        area_match = _ROOM_AREA.search(low)
        if area_match:
            constraints["room_area"] = area_match.group(0)
    if constraints != dict(patch.attribute_constraints):
        updates["attribute_constraints"] = constraints
    clear_fields = list(understanding.clear_fields)
    if "budget" not in clear_fields and (
        oldref_clear
        or (
            any(k in low for k in _BUDGET_CLEAR)
            and patch.budget_min is None
            and patch.budget_max is None
            and "budget_min" not in updates
            and "budget_max" not in updates
        )
    ):
        clear_fields.append("budget")
    if not updates and clear_fields == understanding.clear_fields:
        return understanding
    return understanding.model_copy(
        update={
            "need_patch": patch.model_copy(update=updates),
            "clear_fields": clear_fields,
        }
    )


async def understand_turn(
    message: str,
    *,
    extractor: UnderstandingExtractor | None,
    state_summary: str = "",
    registry: CategoryRegistry | None = None,
    active_category: str | None = None,
    observer: AgentObserver | None = None,
) -> tuple[AgentUnderstanding, list[str]]:
    observer = observer or noop_agent_observer()
    with observer.span(
        "understanding",
        input={"message": message, "state_summary": state_summary},
        metadata={"extractor_configured": extractor is not None},
    ) as observation:
        fallback_reason: str | None = None
        flags: list[str] = []
        understanding: AgentUnderstanding | None = None
        if extractor is not None:
            try:
                extracted = await extractor.extract(
                    message, state_summary=state_summary
                )
                understanding = _augment_understanding(
                    message, extracted, active_category=active_category
                )
            except (ExtractorError, ValidationError) as exc:
                fallback_reason = type(exc).__name__
                flags = ["understanding_degraded"]
        else:
            fallback_reason = "extractor_unconfigured"

        if understanding is None:
            with observer.span(
                "understanding_fallback",
                input={"message": message, "state_summary": state_summary},
                metadata={"reason": fallback_reason},
            ) as fallback_observation:
                understanding = fallback_understanding(
                    message, registry=registry, active_category=active_category
                )
                fallback_observation.update(
                    output={
                        "intent": understanding.intent,
                        "confidence": understanding.confidence,
                        "need_patch": understanding.need_patch.model_dump(),
                    },
                    metadata={"reason": fallback_reason},
                )

        observation.update(
            output={
                "intent": understanding.intent,
                "confidence": understanding.confidence,
                "need_patch": understanding.need_patch.model_dump(),
                "flags": flags,
            },
            metadata={"fallback_used": fallback_reason is not None},
        )
        return understanding, flags
