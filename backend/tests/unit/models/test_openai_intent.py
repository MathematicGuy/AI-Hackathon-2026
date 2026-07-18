import importlib

import pytest
from pydantic import ValidationError

from backend.app.contracts.schemas import IntentOutput


TEST_MODEL = "test-intent-model"


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-103 {self.name} module is not implemented")


@pytest.fixture
def models():
    try:
        return importlib.import_module("backend.app.models.openai_intent")
    except ModuleNotFoundError:
        return MissingModule("openai intent")


def test_module_does_not_depend_on_contract_model_constant():
    try:
        importlib.import_module("backend.app.models.openai_intent")
    except ImportError as exc:
        pytest.fail(f"intent adapter still depends on a removed contract symbol: {exc}")


GOLDEN = {
    "intent": "new_search",
    "confidence": 0.97,
    "requested_product_count": 3,
    "constraints_changed": False,
    "need_patch": {
        "category": "air_conditioner",
        "budget_max_vnd": 20000000,
        "room_size_m2": 18,
        "priorities": [
            {"name": "energy_saving", "importance": "primary", "source": "explicit"},
            {"name": "low_noise", "importance": "secondary", "source": "explicit"},
        ],
    },
}

INVALID = {"intent": "banana", "confidence": 0.5, "need_patch": {"category": "air_conditioner"}}


class FakeClient:
    def __init__(self, responses, *, raise_exc=None):
        self._responses = list(responses)
        self._raise = raise_exc
        self.calls = []

    async def complete(self, *, model, message):
        self.calls.append({"model": model, "message": message})
        if self._raise is not None:
            raise self._raise
        return self._responses.pop(0)


async def test_extractor_returns_golden_need(models):
    client = FakeClient([GOLDEN])
    extractor = models.OpenAIIntentExtractor(client, model=TEST_MODEL)
    result = await extractor.extract("Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m²")
    assert isinstance(result, IntentOutput)
    assert result.intent == "new_search"
    assert result.need_patch.budget_max_vnd == 20000000
    assert result.need_patch.room_size_m2 == 18
    priorities = {p.name: p for p in result.need_patch.priorities}
    assert priorities["energy_saving"].importance == "primary"
    assert priorities["low_noise"].importance == "secondary"


async def test_extractor_forwards_injected_model(models):
    client = FakeClient([GOLDEN])
    extractor = models.OpenAIIntentExtractor(client, model=TEST_MODEL)
    assert extractor.model == TEST_MODEL
    await extractor.extract("mua máy lạnh")
    assert client.calls[0]["model"] == TEST_MODEL


async def test_extractor_retries_once_on_invalid_then_succeeds(models):
    client = FakeClient([INVALID, GOLDEN])
    extractor = models.OpenAIIntentExtractor(client, model=TEST_MODEL)
    result = await extractor.extract("mua máy lạnh")
    assert result.intent == "new_search"
    assert len(client.calls) == 2


async def test_extractor_raises_provider_error_on_client_failure(models):
    client = FakeClient([], raise_exc=RuntimeError("boom"))
    extractor = models.OpenAIIntentExtractor(client, model=TEST_MODEL)
    with pytest.raises(models.ProviderError):
        await extractor.extract("mua máy lạnh")


async def test_extractor_raises_validation_after_retry_exhausted(models):
    client = FakeClient([INVALID, INVALID])
    extractor = models.OpenAIIntentExtractor(client, model=TEST_MODEL)
    with pytest.raises(ValidationError):
        await extractor.extract("mua máy lạnh")
    assert len(client.calls) == 2


async def test_extractor_records_generation_with_raw_io(models, recording_observer):
    client = FakeClient([GOLDEN])
    extractor = models.OpenAIIntentExtractor(
        client, model="configured-model", observer=recording_observer
    )
    result = await extractor.extract("máy lạnh phòng 18m2")
    generation = recording_observer.only("intent_model_call")
    assert generation.kind == "generation"
    assert generation.model == "configured-model"
    assert generation.input == {
        "model": "configured-model",
        "message": "máy lạnh phòng 18m2",
    }
    assert generation.output == GOLDEN
    assert result.intent == "new_search"
    assert "api_key" not in repr(generation).lower()


async def test_extractor_records_error_generation_on_provider_failure(
    models, recording_observer
):
    client = FakeClient([], raise_exc=RuntimeError("boom"))
    extractor = models.OpenAIIntentExtractor(
        client, model=TEST_MODEL, observer=recording_observer
    )
    with pytest.raises(models.ProviderError):
        await extractor.extract("mua máy lạnh")
    generation = recording_observer.only("intent_model_call")
    assert generation.updates[-1]["error"] == {"type": "RuntimeError"}
    assert generation.ended


async def test_extractor_records_one_generation_per_retry_attempt(
    models, recording_observer
):
    client = FakeClient([INVALID, GOLDEN])
    extractor = models.OpenAIIntentExtractor(
        client, model=TEST_MODEL, observer=recording_observer
    )
    result = await extractor.extract("mua máy lạnh")
    assert result.intent == "new_search"
    assert recording_observer.names == ["intent_model_call", "intent_model_call"]
