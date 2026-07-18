from __future__ import annotations

from dataclasses import dataclass
import asyncio

from backend.app.observability.langfuse import (
    LangfuseAgentObserver,
    noop_agent_observer,
)


@dataclass
class FakeObservation:
    name: str
    parent: FakeObservation | None = None
    as_type: str = "span"
    input: object = None
    metadata: object = None
    ended: bool = False
    updates: list[dict[str, object]] | None = None

    def __post_init__(self) -> None:
        self.updates = []

    def start_observation(self, **kwargs):
        child = FakeObservation(
            name=kwargs["name"],
            parent=self,
            as_type=kwargs.get("as_type", "span"),
            input=kwargs.get("input"),
            metadata=kwargs.get("metadata"),
        )
        self.registry.append(child)
        return child

    def update(self, **kwargs) -> None:
        self.updates.append(kwargs)

    def end(self) -> None:
        self.ended = True

    @property
    def registry(self) -> list[FakeObservation]:
        root = self
        while root.parent is not None:
            root = root.parent
        return getattr(root, "_registry", [root])


class FakeLangfuse:
    def __init__(self) -> None:
        self.observations: list[FakeObservation] = []
        self.flush_calls = 0

    def start_observation(self, **kwargs):
        root = FakeObservation(
            name=kwargs["name"],
            as_type=kwargs.get("as_type", "span"),
            input=kwargs.get("input"),
            metadata=kwargs.get("metadata"),
        )
        root._registry = self.observations
        self.observations.append(root)
        return root

    def flush(self) -> None:
        self.flush_calls += 1


class RaisingLangfuse:
    def start_observation(self, **kwargs):
        raise RuntimeError("langfuse unavailable")

    def flush(self) -> None:
        raise RuntimeError("flush unavailable")


class RaisingLifecycleObservation(FakeObservation):
    def update(self, **kwargs) -> None:
        raise RuntimeError("update unavailable")

    def end(self) -> None:
        raise RuntimeError("end unavailable")


class RaisingLifecycleLangfuse(FakeLangfuse):
    def start_observation(self, **kwargs):
        root = RaisingLifecycleObservation(
            name=kwargs["name"],
            as_type=kwargs.get("as_type", "span"),
            input=kwargs.get("input"),
            metadata=kwargs.get("metadata"),
        )
        root._registry = self.observations
        self.observations.append(root)
        return root


def test_nested_priority_observation_closes_under_root() -> None:
    backend = FakeLangfuse()
    observer = LangfuseAgentObserver(backend)

    with observer.start_turn(
        trace_id="a" * 32,
        session_id="session-1",
        request_id="request-1",
        user_id=None,
        input={"message": "hello"},
        metadata={"environment": "test"},
    ):
        with observer.span(
            "input_guardrail", input={"message": "hello"}
        ) as span:
            span.update(output={"blocked": False})

    assert [item.name for item in backend.observations] == [
        "agent_turn",
        "input_guardrail",
    ]
    assert all(item.ended for item in backend.observations)
    assert backend.observations[1].parent is backend.observations[0]
    assert backend.observations[1].updates[-1]["output"] == {"blocked": False}


def test_payload_scrubs_secret_keys_but_keeps_raw_message() -> None:
    backend = FakeLangfuse()
    observer = LangfuseAgentObserver(backend)

    with observer.start_turn(
        trace_id="b" * 32,
        session_id="session-1",
        request_id="request-1",
        user_id=None,
        input={
            "message": "máy lạnh 18m2",
            "API_KEY": "secret",
            "nested": [{"Credentials": {"password": "pw"}}],
        },
        metadata={"AUTHORIZATION": "Bearer secret", "turn_number": 1},
    ):
        pass

    root = backend.observations[0]
    assert root.input == {
        "message": "máy lạnh 18m2",
        "API_KEY": "[REDACTED]",
        "nested": [{"Credentials": "[REDACTED]"}],
    }
    assert root.metadata == {
        "AUTHORIZATION": "[REDACTED]",
        "turn_number": 1,
    }


def test_sdk_and_flush_failures_never_escape() -> None:
    observer = LangfuseAgentObserver(RaisingLangfuse())

    with observer.start_turn(
        trace_id="c" * 32,
        session_id="session-1",
        request_id="request-1",
        user_id=None,
        input={},
        metadata={},
    ) as turn:
        with observer.span("input_guardrail", input={}) as span:
            span.update(output={"blocked": False})

    observer.flush()
    assert turn.observability_degraded is True


def test_update_and_end_failures_are_contained() -> None:
    observer = LangfuseAgentObserver(RaisingLifecycleLangfuse())

    with observer.start_turn(
        trace_id="e" * 32,
        session_id="session-1",
        request_id="request-1",
        user_id=None,
        input={},
        metadata={},
    ) as turn:
        with observer.span("input_guardrail", input={}) as span:
            span.update(output={"blocked": False})

    assert turn.observability_degraded is True


def test_default_factory_is_noop_when_disabled_or_keys_missing(monkeypatch) -> None:
    from backend.app.observability import default_agent_observer

    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_ENABLED", raising=False)
    assert default_agent_observer().__class__.__name__ == "NoopAgentObserver"

    monkeypatch.setenv("LANGFUSE_ENABLED", "false")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    assert default_agent_observer().__class__.__name__ == "NoopAgentObserver"


def test_async_contextvar_parentage_isolated() -> None:
    backend = FakeLangfuse()
    observer = LangfuseAgentObserver(backend)

    async def run(trace_id: str, name: str) -> None:
        with observer.start_turn(
            trace_id=trace_id,
            session_id=name,
            request_id=name,
            user_id=None,
            input={},
            metadata={},
        ):
            await asyncio.sleep(0)
            with observer.span(name, input={}):
                await asyncio.sleep(0)

    async def gather() -> None:
        await asyncio.gather(run("f" * 32, "first"), run("0" * 32, "second"))

    asyncio.run(gather())
    roots = [item for item in backend.observations if item.parent is None]
    assert len(roots) == 2
    assert all(
        child.parent in roots
        for child in backend.observations
        if child.parent is not None
    )


def test_noop_observer_preserves_trace_id() -> None:
    observer = noop_agent_observer()

    with observer.start_turn(
        trace_id="d" * 32,
        session_id="session-1",
        request_id="request-1",
        user_id=None,
        input={},
        metadata={},
    ) as turn:
        assert turn.trace_id == "d" * 32
        with observer.span("input_guardrail", input={}) as span:
            span.update(output={"blocked": False})

    observer.flush()
