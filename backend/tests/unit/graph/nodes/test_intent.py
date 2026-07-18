import importlib

import pytest

from backend.app.contracts.schemas import AirConditionerNeed, IntentOutput


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-103 {self.name} module is not implemented")


@pytest.fixture
def node():
    try:
        return importlib.import_module("backend.app.graph.nodes.intent")
    except ModuleNotFoundError:
        return MissingModule("intent node")


class FakeExtractor:
    def __init__(self, output=None, *, raise_exc=None):
        self._output = output
        self._raise = raise_exc

    async def extract(self, message):
        if self._raise is not None:
            raise self._raise
        return self._output


def golden_output():
    return IntentOutput(
        intent="new_search",
        confidence=0.97,
        need_patch=AirConditionerNeed(budget_max_vnd=20000000, room_size_m2=18),
    )


# Curated Vietnamese scenarios with clear intent signals (fallback accuracy set).
SCENARIOS = [
    ("Em muốn mua máy lạnh cho phòng ngủ 18m2", "new_search"),
    ("Tư vấn máy lạnh tiết kiệm điện dưới 15 triệu", "new_search"),
    ("So sánh hai mẫu máy lạnh này giúp em", "compare_products"),
    ("So sánh Daikin với Panasonic", "compare_products"),
    ("Cho em xem thêm vài mẫu khác", "more_recommendations"),
    ("Còn mẫu nào rẻ hơn không", "more_recommendations"),
    ("Máy này còn hàng ở HCM không", "check_availability"),
    ("Kiểm tra tình trạng kho giúp em", "check_availability"),
    ("Cho em xem thông số chi tiết mẫu này", "product_detail"),
    ("Chi tiết sản phẩm AC-M1-002", "product_detail"),
    ("Thôi em không cần nữa, cảm ơn", "stop"),
    ("Dừng lại nhé", "stop"),
    ("Đổi ngân sách xuống 12 triệu", "change_constraints"),
    ("Thay đổi diện tích phòng thành 25m2", "change_constraints"),
    ("Hôm nay thời tiết đẹp nhỉ", "unsupported"),
]


async def test_classify_returns_extractor_output_without_flags(node):
    result, flags = await node.classify_and_extract(
        "Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m²",
        extractor=FakeExtractor(golden_output()),
    )
    assert result.intent == "new_search"
    assert flags == []


async def test_provider_error_falls_back_and_flags_degraded(node):
    from backend.app.models.openai_intent import ProviderError

    result, flags = await node.classify_and_extract(
        "Em muốn mua máy lạnh cho phòng 18m2",
        extractor=FakeExtractor(raise_exc=ProviderError("down")),
    )
    assert result.intent == "new_search"
    assert flags == ["intent_model_degraded"]


async def test_validation_error_falls_back_and_flags_degraded(node):
    from pydantic import ValidationError

    err = ValidationError.from_exception_data("IntentOutput", [])
    result, flags = await node.classify_and_extract(
        "Dừng lại nhé", extractor=FakeExtractor(raise_exc=err)
    )
    assert result.intent == "stop"
    assert flags == ["intent_model_degraded"]


def test_fallback_never_invents_numbers(node):
    result = node.fallback_intent("Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m2")
    assert result.intent == "new_search"
    assert result.need_patch.budget_max_vnd is None
    assert result.need_patch.room_size_m2 is None


def test_fallback_covers_eight_intents(node):
    seen = {node.fallback_intent(text).intent for text, _ in SCENARIOS}
    assert seen == {
        "new_search",
        "change_constraints",
        "more_recommendations",
        "compare_products",
        "product_detail",
        "check_availability",
        "stop",
        "unsupported",
    }


def test_fallback_accuracy_at_least_90_percent(node):
    correct = sum(
        node.fallback_intent(text).intent == expected for text, expected in SCENARIOS
    )
    assert correct / len(SCENARIOS) >= 0.90


def test_fallback_in_scope_without_shop_verb_is_new_search(node):
    # Precision: a legitimate máy lạnh question must not be dumped to unsupported.
    result = node.fallback_intent("Máy lạnh giá bao nhiêu vậy")
    assert result.intent == "new_search"


def test_fallback_output_is_valid_intent_output(node):
    result = node.fallback_intent("mua máy lạnh")
    assert isinstance(result, IntentOutput)
    assert 0.0 <= result.confidence <= 1.0
    assert 1 <= result.requested_product_count <= 10
