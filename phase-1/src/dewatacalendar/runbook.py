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
    classification: Literal[
        "epoch_offset",
        "rule_drift",
        "calendar_variant",
        "transcription",
        "unavailable_public_field",
    ]
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
    """heuristic classification of a dispute. returns (classification, notes).

    Classification rules (round-2):
      - If the public `saka_year` is unavailable, classify as
        `unavailable_public_field` -- do NOT auto-classify as
        `epoch_offset` or `calendar_variant`. The unavailable status is
        a property of the engine's public contract, not a substantive
        disagreement between engine and reference.
      - If the public engine output disagrees with the reference on a
        substantive field, classify as `epoch_offset` / `calendar_variant`
        / `rule_drift` / `transcription` per the heuristics below.
    """
    fields = outcome.fields_ok
    unavailable = outcome.fields_unavailable

    pos_ok = fields.get("pawukon_position", False)
    wuku_ok = fields.get("pawukon_wuku_idx", False)
    saka_ok = fields.get("saka_year", False)
    sasih_ok = fields.get("sasih_idx", False)

    # If a required public field was unavailable, do not auto-classify
    # the disagreement as epoch_offset or calendar_variant. The
    # unavailability is a separate, well-defined state.
    if unavailable.get("saka_year"):
        diag = outcome.fields_diagnostic_match.get("saka_year")
        diag_note = (
            f" diagnostic saka_year matches expected: {diag}."
            if diag is not None
            else " diagnostic saka_year not produced."
        )
        return (
            "unavailable_public_field",
            "public saka_year is unavailable (engine contract per "
            "PR #15 corrections round 2); this is not an epoch error or "
            "regional variant."
            + diag_note
        )

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
