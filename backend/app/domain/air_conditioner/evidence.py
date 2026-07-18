"""Evidence container for normalized air-conditioner products."""

from dataclasses import dataclass

from backend.app.contracts.schemas import EvidenceRef, NormalizedAirConditioner


def make_evidence(path: str, source_snapshot: str) -> EvidenceRef:
    """Build an evidence reference rooted at a `$` JSONPath into the source."""
    return EvidenceRef(path=path, source_snapshot=source_snapshot)


@dataclass(frozen=True, slots=True)
class NormalizedProduct:
    """A normalized product with per-field provenance.

    `evidence` maps a populated normalized field name to the source location it
    was derived from. `missing_fields` lists normalized fields left `null`
    because the source value was absent.
    """

    product: NormalizedAirConditioner
    evidence: dict[str, EvidenceRef]
    missing_fields: tuple[str, ...]
