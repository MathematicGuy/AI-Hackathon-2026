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
    ) -> None:
        self.client = client
        self.model = model
        self.max_retries = max_retries

    async def extract(self, message: str) -> IntentOutput:
        last_error: ValidationError | None = None
        for _ in range(self.max_retries + 1):
            try:
                raw = await self.client.complete(model=self.model, message=message)
            except Exception as exc:  # provider / transport failure
                raise ProviderError(str(exc)) from exc
            try:
                return IntentOutput.model_validate(raw)
            except ValidationError as exc:
                last_error = exc
        assert last_error is not None
        raise last_error
