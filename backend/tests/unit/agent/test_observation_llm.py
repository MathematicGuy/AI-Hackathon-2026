from contextlib import AbstractContextManager
from typing import Self

import pytest

from backend.app.agent.graph import AgentDependencies
from backend.app.agent.llm.client import (
    LLMCandidate,
    LLMPolisher,
    LLMUnderstandingExtractor,
)


class RecordingHandle(AbstractContextManager[Self]):
    def __init__(self, record: dict[str, object]) -> None:
        self.record = record

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def update(self, **kwargs: object) -> None:
        self.record.setdefault("updates", []).append(kwargs)


class RecordingObserver:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def span(self, name: str, **kwargs: object) -> RecordingHandle:
        record: dict[str, object] = {"name": name, **kwargs}
        self.records.append(record)
        return RecordingHandle(record)


class ActiveOnlyHandle(RecordingHandle):
    def __init__(self, record: dict[str, object]) -> None:
        super().__init__(record)
        self.ended = False

    def __exit__(self, exc_type, exc, tb) -> None:
        self.ended = True

    def update(self, **kwargs: object) -> None:
        if self.ended:
            raise AssertionError("generation updated after context exit")
        super().update(**kwargs)


class ActiveOnlyObserver(RecordingObserver):
    def span(self, name: str, **kwargs: object) -> ActiveOnlyHandle:
        record: dict[str, object] = {"name": name, **kwargs}
        self.records.append(record)
        return ActiveOnlyHandle(record)


def _candidates() -> list[LLMCandidate]:
    return [
        LLMCandidate("https://openrouter.ai/api/v1", "openrouter-secret", "primary"),
        LLMCandidate("https://api.mistral.ai/v1", "mistral-secret", "fallback"),
    ]


def _latest(record: dict[str, object]) -> dict[str, object]:
    updates = record["updates"]
    assert isinstance(updates, list) and updates
    latest = updates[-1]
    assert isinstance(latest, dict)
    return latest


@pytest.mark.asyncio
async def test_understanding_records_prompts_raw_output_and_fallback() -> None:
    observer = RecordingObserver()
    calls: list[str] = []

    async def transport(candidate, system, user):
        calls.append(candidate.model)
        if candidate.model == "primary":
            raise RuntimeError("provider down")
        return '{"intent":"new_search","confidence":0.9,"need_patch":{}}'

    extractor = LLMUnderstandingExtractor(
        _candidates(), transport=transport, observer=observer
    )
    result = await extractor.extract("mua tủ lạnh tầm 15 triệu")

    assert result.intent == "new_search"
    assert calls == ["primary", "fallback"]
    assert [record["name"] for record in observer.records] == [
        "understanding_model_call",
        "understanding_model_call",
    ]
    first, second = observer.records
    assert first["kind"] == "generation"
    assert first["model"] == "primary"
    assert first["model_parameters"] == {"temperature": 0}
    # `attempt` records which try produced this span, so a transient-error
    # retry on the same candidate is visible in the trace rather than hidden
    # (US-125 added the retry; US-207 asks for provider-attempt visibility).
    assert first["metadata"] == {
        "candidate_index": 0,
        "provider": "openrouter",
        "role": "understanding",
        "attempt": 1,
    }
    assert first["input"]["user"] == "mua tủ lạnh tầm 15 triệu"
    assert first["input"]["system"]
    assert _latest(first)["output"] == {"fallback": True}
    assert _latest(first)["error"] == {"type": "RuntimeError"}
    assert "provider down" not in repr(observer.records)
    assert "authorization" not in repr(observer.records).lower()
    assert _latest(second)["output"].startswith("{")
    assert "openrouter-secret" not in repr(observer.records)
    assert "mistral-secret" not in repr(observer.records)


@pytest.mark.asyncio
async def test_polisher_records_generation_and_preserves_fallback_order() -> None:
    observer = RecordingObserver()
    calls: list[str] = []

    async def transport(candidate, system, user):
        calls.append(candidate.model)
        if candidate.model == "primary":
            raise RuntimeError("provider down")
        return "Dạ em gợi ý mẫu này ạ?"

    polisher = LLMPolisher(_candidates(), transport=transport, observer=observer)
    result = await polisher.polish("Em gợi ý mẫu này ạ?")

    assert result == "Dạ em gợi ý mẫu này ạ?"
    assert calls == ["primary", "fallback"]
    assert [record["name"] for record in observer.records] == [
        "response_polish_model_call",
        "response_polish_model_call",
    ]
    first, second = observer.records
    assert first["model_parameters"] == {"temperature": 0.4}
    assert first["metadata"] == {
        "candidate_index": 0,
        "provider": "openrouter",
        "role": "response_polish",
    }
    assert first["input"]["system"]
    assert first["input"]["user"] == "Em gợi ý mẫu này ạ?"
    assert _latest(first)["output"] == {"fallback": True}
    assert _latest(second)["output"] == "Dạ em gợi ý mẫu này ạ?"


@pytest.mark.asyncio
async def test_tracing_failure_does_not_change_model_result() -> None:
    class RaisingObserver:
        def span(self, name: str, **kwargs: object):
            raise RuntimeError("tracing unavailable")

    async def transport(candidate, system, user):
        return '{"intent":"stop","confidence":1,"need_patch":{}}'

    extractor = LLMUnderstandingExtractor(
        [_candidates()[0]], transport=transport, observer=RaisingObserver()
    )
    result = await extractor.extract("dừng lại")
    assert result.intent == "stop"


@pytest.mark.asyncio
async def test_failed_generation_updates_before_observation_ends() -> None:
    observer = ActiveOnlyObserver()

    async def transport(candidate, system, user):
        if candidate.model == "primary":
            raise RuntimeError("https://user:secret@example.invalid Authorization: Bearer key")
        return '{"intent":"stop","confidence":1,"need_patch":{}}'

    extractor = LLMUnderstandingExtractor(
        _candidates(), transport=transport, observer=observer
    )
    result = await extractor.extract("dừng lại")

    assert result.intent == "stop"
    first = observer.records[0]
    assert _latest(first)["error"] == {"type": "RuntimeError"}
    assert _latest(first)["output"] == {"fallback": True}
    assert "secret" not in repr(observer.records)
    assert "authorization" not in repr(observer.records).lower()


def test_default_dependencies_inject_one_observer_into_llm_factories(monkeypatch) -> None:
    observer = RecordingObserver()
    seen: dict[str, object] = {}

    class Adapter:
        def load(self):
            return []

    def fake_extractor(*, observer):
        seen["extractor"] = observer
        return object()

    def fake_polisher(*, observer):
        seen["polisher"] = observer
        return object()

    monkeypatch.setattr("backend.app.observability.default_agent_observer", lambda: observer)
    monkeypatch.setattr("backend.app.agent.catalog.dataset_adapter.default_adapter", lambda: Adapter())
    monkeypatch.setattr("backend.app.agent.llm.client.default_extractor", fake_extractor)
    monkeypatch.setattr("backend.app.agent.llm.client.default_polisher", fake_polisher)

    deps = AgentDependencies.from_default_paths(with_llm=True)

    assert deps.observer is observer
    assert seen == {"extractor": observer, "polisher": observer}
