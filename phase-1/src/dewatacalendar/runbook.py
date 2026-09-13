"""runbook for cross-validation disputes.

when an expected vector disagrees with the engine, this module:

1. records the dispute with full provenance.
2. classifies the dispute as one of: epoch_offset, rule_drift, calendar_variant.
3. supports manual resolution: keep-as-disputed, accept-corpus, update-engine.

this is the operational interface. the human reviewer uses this.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from .cross_validation import CrossValidationOutcome


DISPUTES_LOG = Path(__file__).resolve().parent.parent.parent / "docs" / "runbook" / "disputes.json"


ResolutionStatus = Literal["pending", "accepted", "rejected", "variant"]


@dataclass
class DisputeRecord:
    """a record of one cross-validation dispute."""
    date: str
    source: str
    page: int | None
    rule_id: str
    classification: Literal["epoch_offset", "rule_drift", "calendar_variant", "transcription"]
    resolution: ResolutionStatus
    notes: str
    recorded_at: str

    @classmethod
    def from_outcome(cls, o: CrossValidationOutcome, classification: str, notes: str) -> "DisputeRecord":
        return cls(
            date=o.date,
            source=o.source,
            page=o.page,
            rule_id=o.rule_id,
            classification=classification,  # type: ignore[arg-type]
            resolution="pending",
            notes=notes,
            recorded_at=datetime.utcnow().isoformat() + "Z",
        )


def classify(outcome: CrossValidationOutcome) -> tuple[str, str]:
    """heuristic classification of a dispute. returns (classification, notes)."""
    fields = outcome.fields_ok
    pos_ok = fields.get("pawukon_position", False)
    wuku_ok = fields.get("pawukon_wuku_idx", False)
    saka_ok = fields.get("saka_year", False)
    sasih_ok = fields.get("sasih_idx", False)

    # pure sasih-only disagreement → regional variant
    if pos_ok and wuku_ok and saka_ok and not sasih_ok:
        return (
            "calendar_variant",
            "sasih ordering differs from publication; this often reflects a "
            "lombok/java/bali regional variant. record which variant, do not "
            "automatically change the engine ruleset.",
        )
    # saka-and-sasih both disagree → almost certainly a variant
    if pos_ok and wuku_ok and not saka_ok and not sasih_ok:
        return (
            "calendar_variant",
            "saka year + sasih both disagree; this is most plausibly a regional "
            "variant (lombok/java/bali) or a different epoch convention. record "
            "which variant, do not automatically change the engine ruleset.",
        )
    # saka disagrees but sasih agrees → epoch arithmetic only
    if pos_ok and wuku_ok and not saka_ok:
        return (
            "epoch_offset",
            "pawukon matches publication; saka year is offset by source-specific "
            "epoch arithmetic. verify saka-year formula against the source's stated "
            "convention before bumping ruleset.",
        )
    # pawukon itself disagrees
    if not pos_ok and not wuku_ok:
        return (
            "rule_drift",
            "pawukon position disagrees with publication; engine ruleset may "
            "differ from source. human review of cycle anchor and ruleset id needed.",
        )
    if not sasih_ok:
        return (
            "calendar_variant",
            "sasih ordering differs from publication; this often reflects a "
            "lombok/java/bali regional variant. record which variant, do not "
            "automatically change the engine ruleset.",
        )
    return ("transcription", "manual transcription / typo in corpus — verify by hand.")
