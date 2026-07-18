"""Injected intent classifier and need extractor.

The extractor calls an injected OpenAI-compatible client, validates the
structured output into the frozen ``IntentOutput`` contract, and retries the
structured parse once. A transport/provider failure raises ``ProviderError``;
a schema failure after the retry raises ``ValidationError``. The node layer
turns either into a deterministic fallback.
"""

from typing import Any, Protocol

from pydantic import ValidationError

from backend.app.contracts.schemas import IntentOutput
from backend.app.observability import AgentObserver, noop_agent_observer


class ProviderError(Exception):
    """Raised when the intent provider client fails to return a response."""


class IntentClient(Protocol):
    async def complete(self, *, model: str, message: str) -> dict[str, Any]: ...


class IntentExtractor(Protocol):
    async def extract(self, message: str) -> IntentOutput: ...


class OpenAIIntentExtractor:
    def __init__(
        self,
        client: IntentClient,
        *,
        model: str,
        max_retries: int = 1,
        observer: AgentObserver | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.max_retries = max_retries
        self.observer = observer or noop_agent_observer()

    async def extract(self, message: str) -> IntentOutput:
        last_error: ValidationError | None = None
        for attempt in range(self.max_retries + 1):
            with self.observer.span(
                "intent_model_call",
                kind="generation",
                model=self.model,
                input={"model": self.model, "message": message},
                metadata={"attempt": attempt + 1, "role": "main"},
            ) as generation:
                try:
                    raw = await self.client.complete(model=self.model, message=message)
                except Exception as exc:  # provider / transport failure
                    generation.update(
                        error={"type": type(exc).__name__}, output={"fallback": True}
                    )
                    raise ProviderError(str(exc)) from exc
                generation.update(output=raw)
                try:
                    return IntentOutput.model_validate(raw)
                except ValidationError as exc:
                    last_error = exc
                    generation.update(
                        error={"type": type(exc).__name__}, output={"fallback": True}
                    )
        assert last_error is not None
        raise last_error
