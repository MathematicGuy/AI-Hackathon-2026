"""Intent classification + need extraction node with deterministic fallback.

The primary path uses an injected `IntentExtractor` (GPT-5.4 Nano). On provider
or schema failure the node falls back to a deterministic keyword classifier and
flags `intent_model_degraded`. The fallback never invents numeric values — it
only classifies intent and leaves the need patch empty.
"""

from pydantic import ValidationError

from backend.app.contracts.schemas import AirConditionerNeed, IntentOutput
from backend.app.models.openai_intent import IntentExtractor, ProviderError

FALLBACK_CONFIDENCE = 0.3

_STOP = ("dừng", "thôi", "không cần", "ngừng", "kết thúc")
_COMPARE = ("so sánh", "so với", "đối chiếu")
_CHANGE = ("đổi ", "thay đổi", "chuyển sang", "điều chỉnh")
_MORE = ("xem thêm", "thêm mẫu", "mẫu khác", "còn mẫu nào", "gợi ý thêm", "rẻ hơn", "nhiều hơn")
_AVAILABILITY = ("còn hàng", "tình trạng", "kho", "hết hàng", "có sẵn", "giao hàng")
_DETAIL = ("chi tiết", "thông số", "xem kỹ", "thông tin sản phẩm")
_IN_SCOPE = ("máy lạnh", "may lanh", "điều hòa", "điều hoà", "dieu hoa")


def _classify(low: str) -> str:
    if any(k in low for k in _STOP):
        return "stop"
    if any(k in low for k in _COMPARE):
        return "compare_products"
    if any(k in low for k in _CHANGE):
        return "change_constraints"
    if any(k in low for k in _MORE):
        return "more_recommendations"
    if any(k in low for k in _AVAILABILITY):
        return "check_availability"
    if any(k in low for k in _DETAIL):
        return "product_detail"
    # Any máy lạnh mention with no other signal is treated as a search request,
    # not unsupported — the degraded fallback must not overfire a legitimate
    # in-scope question (e.g. "máy lạnh giá bao nhiêu").
    if any(k in low for k in _IN_SCOPE):
        return "new_search"
    return "unsupported"


def fallback_intent(message: str) -> IntentOutput:
    intent = _classify(message.lower())
    return IntentOutput(
        intent=intent,
        confidence=FALLBACK_CONFIDENCE,
        constraints_changed=(intent == "change_constraints"),
        need_patch=AirConditionerNeed(),
    )


async def classify_and_extract(
    message: str, *, extractor: IntentExtractor
) -> tuple[IntentOutput, list[str]]:
    try:
        return await extractor.extract(message), []
    except (ProviderError, ValidationError):
        return fallback_intent(message), ["intent_model_degraded"]
