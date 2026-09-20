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

    Classification rules (round-3 precedence, fixed for round-3
    precedence correction):
      - If the public engine output disagrees with the reference on
        AVAILABLE required fields (pawukon_position, pawukon_wuku_idx,
        saka_year, sasih_idx), classify per the substantive heuristics
        below -- even when another field (e.g. saka_year) is
        unavailable. The unavailable field is added as a NOTE on the
        classification; it does not replace the substantive finding.
      - Else if a required field was unavailable with no substantive
        disagreement on the AVAILABLE fields, classify as
        `unavailable_public_field`. The unavailable status is a
        property of the engine's public contract, not a substantive
        disagreement between engine and reference.
      - The diagnostic value is recorded in the notes for human readers.

    The substantive heuristics operate on the available-field truth
    values (skipping unavailable fields). Unavailable fields cannot
    be said to "disagree" -- we simply do not have the value, so the
    heuristics that check whether a field agrees or disagrees apply
    only to available fields.
    """
    fields = outcome.fields_ok
    unavailable = outcome.fields_unavailable

    # Helper: read a field's truth value, treating unavailable fields
    # as "unknown" (None). The substantive heuristics below use None
    # explicitly to avoid conflating "disagrees" with "unavailable".
    def _available_ok(k: str) -> bool | None:
        if unavailable.get(k):
            return None
        return fields.get(k, False)

    pos_ok = _available_ok("pawukon_position")
    wuku_ok = _available_ok("pawukon_wuku_idx")
    saka_ok = _available_ok("saka_year")
    sasih_ok = _available_ok("sasih_idx")

    # Compute a "saka_year unavailable" note for any classification
    # that is not already `unavailable_public_field`.
    unavailable_note_extra = ""
    if unavailable.get("saka_year"):
        diag = outcome.fields_diagnostic_match.get("saka_year")
        diag_note = (
            f" diagnostic saka_year matches expected: {diag}."
            if diag is not None
            else " diagnostic saka_year not produced."
        )
        unavailable_note_extra = (
            " [addendum: saka_year was unavailable on this row; "
            "classification above is based on the available "
            "field(s)."
            + diag_note
            + "]"
        )

    # pure sasih-only disagreement on an available sasih field
    # (saka_year may or may not be unavailable)
    if pos_ok is True and wuku_ok is True and sasih_ok is False:
        return (
            "calendar_variant",
            "sasih ordering differs from publication; this often reflects a "
            "lombok/java/bali regional variant. record which variant, do not "
            "automatically change the engine ruleset."
            + unavailable_note_extra,
        )
    # saka-and-sasih both disagree (both available and disagree)
    if (
        pos_ok is True
        and wuku_ok is True
        and saka_ok is False
        and sasih_ok is False
    ):
        return (
            "calendar_variant",
            "saka year + sasih both disagree; this is most plausibly a regional "
            "variant (lombok/java/bali) or a different epoch convention. record "
            "which variant, do not automatically change the engine ruleset."
            + unavailable_note_extra,
        )
    # saka disagrees (available and disagrees), sasih agrees
    if pos_ok is True and wuku_ok is True and saka_ok is False:
        return (
            "epoch_offset",
            "pawukon matches publication; saka year is offset by source-specific "
            "epoch arithmetic. verify saka-year formula against the source's stated "
            "convention before bumping ruleset."
            + unavailable_note_extra,
        )
    # pawukon itself disagrees on available pawukon fields
    if pos_ok is False and wuku_ok is False:
        return (
            "rule_drift",
            "pawukon position disagrees with publication; engine ruleset may "
            "differ from source. human review of cycle anchor and ruleset id needed."
            + unavailable_note_extra,
        )
    # sasih disagrees on an available sasih field
    if sasih_ok is False:
        return (
            "calendar_variant",
            "sasih ordering differs from publication; this often reflects a "
            "lombok/java/bali regional variant. record which variant, do not "
            "automatically change the engine ruleset."
            + unavailable_note_extra,
        )
    # All available fields agree. If any required field was
    # unavailable, the substantive check is inconclusive -- classify
    # as `unavailable_public_field`, not as a substantive epoch or
    # variant claim.
    if any(unavailable.values()):
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
    # All required fields were available and agreed.
    return ("transcription", "manual transcription / typo in corpus — verify by hand.")
