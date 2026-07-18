from __future__ import annotations

import os
import re
from contextvars import ContextVar, Token
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Literal, Protocol, Self


_REDACTED = "[REDACTED]"
_SECRET_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "auth_token",
    "access_token",
    "credential",
    "credentials",
    "password",
    "private_key",
    "secret",
    "secret_key",
    "token",
}
_SECRET_ENV_NAMES = {
    "LANGFUSE_SECRET_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "AZURE_OPENAI_API_KEY",
}


def _normalise_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _is_secret_key(key: object) -> bool:
    normalised = _normalise_key(key)
    known = {_normalise_key(name) for name in _SECRET_KEYS}
    return (
        normalised in known
        or "secret" in normalised
        or "credential" in normalised
        or normalised.endswith("apikey")
        or normalised.endswith("authorization")
    )


def _secret_values() -> set[str]:
    names = set(_SECRET_ENV_NAMES)
    names.update(
        name
        for name in os.environ
        if any(marker in name.upper() for marker in ("SECRET", "API_KEY", "TOKEN", "PASSWORD"))
    )
    return {value for name in names if (value := os.getenv(name))}


def redact_payload(value: object) -> object:
    """Recursively redact secret-keyed values and configured secret values."""
    secrets = _secret_values()

    def scrub(item: object) -> object:
        if isinstance(item, dict):
            result: dict[object, object] = {}
            for key, child in item.items():
                if _is_secret_key(key):
                    result[key] = _REDACTED
                else:
                    result[key] = scrub(child)
            return result
        if isinstance(item, list):
            return [scrub(child) for child in item]
        if isinstance(item, tuple):
            return tuple(scrub(child) for child in item)
        if isinstance(item, set):
            return {scrub(child) for child in item}
        if isinstance(item, str) and item in secrets:
            return _REDACTED
        return item

    try:
        return scrub(value)
    except Exception:
        return _REDACTED


class AgentObserver(Protocol):
    def start_turn(
        self,
        *,
        trace_id: str,
        session_id: str,
        request_id: str,
        user_id: str | None,
        input: object,
        metadata: dict[str, object],
    ) -> AbstractContextManager[TurnObservation]: ...

    def span(
        self,
        name: str,
        *,
        input: object,
        metadata: dict[str, object] | None = None,
        kind: Literal["span", "generation"] = "span",
        model: str | None = None,
        model_parameters: dict[str, object] | None = None,
    ) -> AbstractContextManager[ObservationHandle]: ...

    def flush(self) -> None: ...


@dataclass
class TurnObservation:
    trace_id: str
    session_id: str
    request_id: str
    user_id: str | None
    _raw: Any = None
    _degraded: bool = False

    @property
    def observability_degraded(self) -> bool:
        return self._degraded

    def update(self, **kwargs: object) -> None:
        if self._raw is None:
            return
        try:
            self._raw.update(**{key: redact_payload(value) for key, value in kwargs.items()})
        except Exception:
            self._degraded = True


class ObservationHandle(AbstractContextManager[Self]):
    def __init__(self, raw: Any, turn: TurnObservation | None) -> None:
        self._raw = raw
        self._turn = turn
        self._ended = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.end()

    def update(self, **kwargs: object) -> None:
        if self._raw is None:
            return
        try:
            self._raw.update(**{key: redact_payload(value) for key, value in kwargs.items()})
        except Exception:
            if self._turn is not None:
                self._turn._degraded = True

    def end(self) -> None:
        if self._ended:
            return
        self._ended = True
        if self._raw is None:
            return
        try:
            self._raw.end()
        except Exception:
            if self._turn is not None:
                self._turn._degraded = True


class _TurnContext(AbstractContextManager[TurnObservation]):
    def __init__(
        self,
        observer: LangfuseAgentObserver,
        turn: TurnObservation,
        parent_token: Token[Any],
        turn_token: Token[Any],
    ) -> None:
        self._observer = observer
        self._turn = turn
        self._parent_token = parent_token
        self._turn_token = turn_token

    def __enter__(self) -> TurnObservation:
        return self._turn

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._observer._end_turn(self._turn, self._parent_token, self._turn_token)


class _ObservationContext(AbstractContextManager[ObservationHandle]):
    def __init__(self, observer: LangfuseAgentObserver, handle: ObservationHandle, token: Token[Any]) -> None:
        self._observer = observer
        self._handle = handle
        self._token = token

    def __enter__(self) -> ObservationHandle:
        return self._handle

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._handle.end()
        self._observer._current_parent.reset(self._token)


class LangfuseAgentObserver:
    def __init__(self, client: Any) -> None:
        self._client = client
        self._current_parent: ContextVar[ObservationHandle | None] = ContextVar(
            "langfuse_current_parent", default=None
        )
        self._current_turn: ContextVar[TurnObservation | None] = ContextVar(
            "langfuse_current_turn", default=None
        )
        self._last_turn: ContextVar[TurnObservation | None] = ContextVar(
            "langfuse_last_turn", default=None
        )

    def start_turn(
        self,
        *,
        trace_id: str,
        session_id: str,
        request_id: str,
        user_id: str | None,
        input: object,
        metadata: dict[str, object],
    ) -> _TurnContext:
        turn = TurnObservation(trace_id, session_id, request_id, user_id)
        kwargs: dict[str, object] = {
            "name": "agent_turn",
            "as_type": "span",
            "trace_context": {"trace_id": trace_id},
            "input": redact_payload(input),
            "metadata": redact_payload(metadata),
        }
        try:
            turn._raw = self._client.start_observation(**kwargs)
        except Exception:
            turn._degraded = True
        parent_token = self._current_parent.set(ObservationHandle(turn._raw, turn))
        turn_token = self._current_turn.set(turn)
        self._last_turn.set(turn)
        return _TurnContext(self, turn, parent_token, turn_token)

    def _end_turn(
        self,
        turn: TurnObservation,
        parent_token: Token[Any],
        turn_token: Token[Any],
    ) -> None:
        if turn._raw is not None:
            try:
                turn._raw.end()
            except Exception:
                turn._degraded = True
        self._current_parent.reset(parent_token)
        self._current_turn.reset(turn_token)

    def span(
        self,
        name: str,
        *,
        input: object,
        metadata: dict[str, object] | None = None,
        kind: Literal["span", "generation"] = "span",
        model: str | None = None,
        model_parameters: dict[str, object] | None = None,
    ) -> _ObservationContext:
        turn = self._current_turn.get()
        parent = self._current_parent.get()
        raw = None
        if turn is not None and parent is not None and parent._raw is not None:
            kwargs: dict[str, object] = {
                "name": name,
                "as_type": kind,
                "input": redact_payload(input),
            }
            if metadata is not None:
                kwargs["metadata"] = redact_payload(metadata)
            if model is not None:
                kwargs["model"] = model
            if model_parameters is not None:
                kwargs["model_parameters"] = redact_payload(model_parameters)
            try:
                raw = parent._raw.start_observation(**kwargs)
            except Exception:
                turn._degraded = True
        handle = ObservationHandle(raw, turn)
        token = self._current_parent.set(handle)
        return _ObservationContext(self, handle, token)

    def flush(self) -> None:
        try:
            self._client.flush()
        except Exception:
            turn = self._current_turn.get() or self._last_turn.get()
            if turn is not None:
                turn._degraded = True


class NoopAgentObserver:
    def start_turn(self, **kwargs: object) -> _NoopTurnContext:
        turn = TurnObservation(
            trace_id=str(kwargs.get("trace_id", "")),
            session_id=str(kwargs.get("session_id", "")),
            request_id=str(kwargs.get("request_id", "")),
            user_id=kwargs.get("user_id") if isinstance(kwargs.get("user_id"), str) else None,
        )
        return _NoopTurnContext(turn)

    def span(self, name: str, **kwargs: object) -> AbstractContextManager[ObservationHandle]:
        return _NoopObservationContext()

    def flush(self) -> None:
        return None


class _NoopObservationContext(AbstractContextManager[ObservationHandle]):
    def __init__(self) -> None:
        self._handle = ObservationHandle(None, None)

    def __enter__(self) -> ObservationHandle:
        return self._handle

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None


class _NoopTurnContext(AbstractContextManager[TurnObservation]):
    def __init__(self, turn: TurnObservation) -> None:
        self._turn = turn

    def __enter__(self) -> TurnObservation:
        return self._turn

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None


def noop_agent_observer() -> NoopAgentObserver:
    return NoopAgentObserver()


def default_agent_observer() -> AgentObserver:
    enabled = os.getenv("LANGFUSE_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not enabled or not public_key or not secret_key:
        return noop_agent_observer()
    try:
        from langfuse import Langfuse

        kwargs: dict[str, object] = {"public_key": public_key, "secret_key": secret_key}
        if base_url := os.getenv("LANGFUSE_BASE_URL"):
            kwargs["host"] = base_url
        return LangfuseAgentObserver(Langfuse(**kwargs))
    except Exception:
        return noop_agent_observer()
