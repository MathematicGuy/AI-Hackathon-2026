from contextlib import AbstractContextManager
from typing import Self

from fastapi.testclient import TestClient

from backend.app.agent import demo
from backend.app.agent.api import create_agent_app
from backend.app.agent.contracts import AgentState
from backend.app.agent.graph import AgentDependencies, AgentReply


class RecordingTurn(AbstractContextManager[Self]):
    def __init__(self, observer: "RecordingObserver") -> None:
        self.observer = observer

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def update(self, **kwargs: object) -> None:
        self.observer.updates.append(kwargs)


class RecordingObserver:
    def __init__(self, *, fail_flush: bool = False) -> None:
        self.fail_flush = fail_flush
        self.turns: list[dict[str, object]] = []
        self.updates: list[dict[str, object]] = []
        self.flush_count = 0

    def start_turn(self, **kwargs: object) -> RecordingTurn:
        self.turns.append(kwargs)
        return RecordingTurn(self)

    def flush(self) -> None:
        self.flush_count += 1
        if self.fail_flush:
            raise RuntimeError("flush unavailable")


def _client(observer: RecordingObserver) -> TestClient:
    deps = AgentDependencies(products=[])
    deps.observer = observer
    return TestClient(create_agent_app(deps), raise_server_exceptions=False)


def _agent_body(body: dict[str, object]) -> dict[str, object]:
    return {
        key: body[key]
        for key in ("session_id", "intent", "text", "flags", "presented_ids")
    }


def test_api_correlates_root_turn_and_flushes_once() -> None:
    observer = RecordingObserver()

    with _client(observer) as client:
        response = client.post(
            "/api/v1/agent/respond",
            json={"session_id": "session-observation", "message": "tư vấn sản phẩm"},
        )

    assert response.status_code == 200
    body = response.json()
    assert len(observer.turns) == 1
    root = observer.turns[0]
    assert body["trace_id"] == root["trace_id"]
    assert body["session_id"] == root["session_id"] == "session-observation"
    assert body["request_id"] == root["request_id"]
    assert root["user_id"] is None
    assert root["metadata"] == {"environment": "hackathon", "turn_number": 1}

    root_input = root["input"]
    assert isinstance(root_input, dict)
    assert root_input["message"] == "tư vấn sản phẩm"
    assert isinstance(root_input["state"], AgentState)
    assert root_input["state"].session_id == "session-observation"

    assert len(observer.updates) == 1
    root_output = observer.updates[0]["output"]
    assert isinstance(root_output, dict)
    assert isinstance(root_output["reply"], AgentReply)
    assert root_output["reply"].text == body["text"]
    assert root_output["state"] is root_input["state"]
    assert observer.flush_count == 1


def test_flush_failure_keeps_http_200_and_agent_body() -> None:
    healthy_observer = RecordingObserver()
    failing_observer = RecordingObserver(fail_flush=True)

    with _client(healthy_observer) as healthy_client:
        healthy_response = healthy_client.post(
            "/api/v1/agent/respond",
            json={"session_id": "session-observation", "message": "tư vấn sản phẩm"},
        )
    with _client(failing_observer) as failing_client:
        failing_response = failing_client.post(
            "/api/v1/agent/respond",
            json={"session_id": "session-observation", "message": "tư vấn sản phẩm"},
        )

    assert healthy_response.status_code == 200
    assert failing_response.status_code == 200
    assert _agent_body(failing_response.json()) == _agent_body(healthy_response.json())
    assert failing_observer.flush_count == 1


async def test_demo_creates_root_per_turn_and_flushes_before_exit(monkeypatch) -> None:
    observer = RecordingObserver()
    deps = AgentDependencies(products=[])
    deps.observer = observer
    messages = iter(["tư vấn sản phẩm", "exit"])
    monkeypatch.setattr(
        demo.AgentDependencies,
        "from_default_paths",
        lambda: deps,
    )
    monkeypatch.setattr("builtins.input", lambda _: next(messages))

    await demo.main()

    assert len(observer.turns) == 1
    root = observer.turns[0]
    assert root["session_id"] == "demo"
    assert root["metadata"] == {"environment": "hackathon", "turn_number": 1}
    assert len(observer.updates) == 1
    assert observer.flush_count == 1
