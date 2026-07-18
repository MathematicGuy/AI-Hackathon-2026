import importlib

import pytest
from pydantic import ValidationError

from backend.app.contracts.schemas import INTENT_MODEL, IntentOutput


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
    extractor = models.OpenAIIntentExtractor(client)
    result = await extractor.extract("Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m²")
    assert isinstance(result, IntentOutput)
    assert result.intent == "new_search"
    assert result.need_patch.budget_max_vnd == 20000000
    assert result.need_patch.room_size_m2 == 18
    priorities = {p.name: p for p in result.need_patch.priorities}
    assert priorities["energy_saving"].importance == "primary"
    assert priorities["low_noise"].importance == "secondary"


async def test_extractor_uses_exact_intent_model(models):
    client = FakeClient([GOLDEN])
    extractor = models.OpenAIIntentExtractor(client)
    assert extractor.model == INTENT_MODEL == "gpt-5.4-nano"
    await extractor.extract("mua máy lạnh")
    assert client.calls[0]["model"] == "gpt-5.4-nano"


async def test_extractor_retries_once_on_invalid_then_succeeds(models):
    client = FakeClient([INVALID, GOLDEN])
    extractor = models.OpenAIIntentExtractor(client)
    result = await extractor.extract("mua máy lạnh")
    assert result.intent == "new_search"
    assert len(client.calls) == 2


async def test_extractor_raises_provider_error_on_client_failure(models):
    client = FakeClient([], raise_exc=RuntimeError("boom"))
    extractor = models.OpenAIIntentExtractor(client)
    with pytest.raises(models.ProviderError):
        await extractor.extract("mua máy lạnh")


async def test_extractor_raises_validation_after_retry_exhausted(models):
    client = FakeClient([INVALID, INVALID])
    extractor = models.OpenAIIntentExtractor(client)
    with pytest.raises(ValidationError):
        await extractor.extract("mua máy lạnh")
    assert len(client.calls) == 2
