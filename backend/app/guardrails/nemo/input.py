"""NeMo input rail protocol and the default M1 (unavailable) rail."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NemoVerdict:
    allowed: bool
    available: bool


class NemoInputRail(Protocol):
    def check(self, message: str) -> NemoVerdict: ...


class UnavailableInputRail:
    """Default M1 rail. Real NeMo Guardrails is not integrated in Milestone 1,
    so the rail reports unavailable and the deterministic checks fail closed for
    anything not clearly low-risk in-scope shopping."""

    def check(self, message: str) -> NemoVerdict:
        return NemoVerdict(allowed=False, available=False)


def default_input_rail() -> NemoInputRail:
    return UnavailableInputRail()
