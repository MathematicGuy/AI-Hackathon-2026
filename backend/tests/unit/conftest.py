"""Shared test doubles for US-116 M1 node/model observation coverage.

`RecordingObserver` mirrors the shape of the US-207 `AgentObserver` protocol
consumed by the traced nodes, capturing span names, raw payloads, and lifecycle
so focused tests can assert the priority tree without a live Langfuse SDK.
"""

from __future__ import annotations

import pytest


class RecordingSpan:
    def __init__(
        self,
        name: str,
        *,
        input: object = None,
        metadata: object = None,
        kind: str = "span",
        model: str | None = None,
        model_parameters: object = None,
    ) -> None:
        self.name = name
        self.input = input
        self.metadata = metadata
        self.kind = kind
        self.model = model
        self.model_parameters = model_parameters
        self.output: object = None
        self.updates: list[dict[str, object]] = []
        self.ended = False

    def __enter__(self) -> "RecordingSpan":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.ended = True
        return False

    def update(self, **kwargs: object) -> None:
        self.updates.append(kwargs)
        if "output" in kwargs:
            self.output = kwargs["output"]

    def end(self) -> None:
        self.ended = True


class RecordingObserver:
    def __init__(self) -> None:
        self.spans: list[RecordingSpan] = []

    def span(
        self,
        name: str,
        *,
        input: object = None,
        metadata: object = None,
        kind: str = "span",
        model: str | None = None,
        model_parameters: object = None,
    ) -> RecordingSpan:
        span = RecordingSpan(
            name,
            input=input,
            metadata=metadata,
            kind=kind,
            model=model,
            model_parameters=model_parameters,
        )
        self.spans.append(span)
        return span

    def flush(self) -> None:
        return None

    @property
    def names(self) -> list[str]:
        return [span.name for span in self.spans]

    def only(self, name: str) -> RecordingSpan:
        matches = [span for span in self.spans if span.name == name]
        assert len(matches) == 1, f"expected exactly one {name!r} span, got {len(matches)}"
        return matches[0]


@pytest.fixture
def recording_observer() -> RecordingObserver:
    return RecordingObserver()


@pytest.fixture(autouse=True)
def _isolated_agent_sessions(tmp_path, monkeypatch):
    """The agent API write-throughs session memory to AGENT_SESSION_DIR; tests
    must never read or pollute the real data/agent-sessions directory."""
    monkeypatch.setenv("AGENT_SESSION_DIR", str(tmp_path / "agent-sessions"))
