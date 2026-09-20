"""cross-validation against published sources.

this module loads vector sets from disk (Cunningham 1994, Igarashi 1999,
and others) and asserts each one against the engine. every vector carries
its source provenance — page number, edition, author — and the test outcome
records the source alongside the result.

the engine has ONE ruleset (pawukon-v0.4.1+saka-bali-v0.2.3). published
sources occasionally disagree because they encode slightly different
epistemic commitments:

  * Cunningham 1994 anchors at 1981-08-23 = Wuku Sinta Day 1, Sasih Kasa.
  * Igarashi 1999 anchors before 1980 with a different sasih-arrangement.
    his pre-1980 sasih ordering is shifted by +1 relative to Cunningham's
    modern-bali convention. his post-1980 ordering matches Cunningham.

the engine reports which convention applies for a given date and the
provenance layer makes the decision visible.

## cultural integrity invariant

a published vector that disagrees with the engine is NEVER silently
rejected. it is recorded with status `disputed` and the operator has to
decide whether to (a) update the engine's ruleset, (b) update the corpus,
or (c) accept the dispute as a documented regional variant.

## corpus evidence status (two-axis model)

every outcome is annotated with the corpus's two-axis evidence status
per phase-1/conformance/STATUS.json schema v2:

  corpus_verification_status:  UNVERIFIED | VERIFIED
  corpus_reference_eligibility: INELIGIBLE | ELIGIBLE
  corpus_authority_basis:       scholarly | customary | institutional |
                                practitioner | software_reference | unknown
  corpus_legacy_status:         CorpusStatus (legacy single-axis view)

the gate predicate is `can_satisfy_validation_gate(record)` which is
`(verification == VERIFIED) AND (eligibility == ELIGIBLE)`. an outcome
fails closed unless both axes pass.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .api import compose_day  # noqa: PLC0415
from .corpus_status import (  # noqa: PLC0415
    AuthorityBasis,
    CorpusRecord,
    ReferenceEligibility,
    VerificationStatus,
    can_satisfy_validation_gate,
    corpus_record_for,
)
from .published_cunningham import load_cunningham_corpus  # noqa: F401 — re-export
from .published_igarashi import load_igarashi_corpus  # noqa: F401 — re-export


CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "conformance" / "published"


@dataclass(frozen=True, slots=True)
class CrossValidationOutcome:
    """the outcome of comparing one published vector against the engine.

    corpus evidence status fields (two-axis):
      corpus_verification_status:  UNVERIFIED | VERIFIED
      corpus_reference_eligibility: INELIGIBLE | ELIGIBLE
      corpus_authority_basis:       scholarly | customary | institutional |
                                    practitioner | software_reference | unknown

    legacy single-axis field (for callers that don't need the two-axis
    detail; derived from the two axes):
      corpus_status:               UNVERIFIED | NON_AUTHORITATIVE | ATTESTED

    the gate predicate is `corpus_may_satisfy_validation_gate` which is
    True iff (verification == VERIFIED) AND (eligibility == ELIGIBLE).
    downstream consumers MUST check this field before treating any value
    in `expected` or `actual` as authoritative.

    the legacy `corpus_status` field is preserved for backwards
    compatibility. it is derived from the two axes.
    """
    date: str
    source: str
    page: int | None
    expected: dict[str, Any]
    actual: dict[str, Any]
    fields_ok: dict[str, bool]
    status: str                    # 'match' | 'drift' | 'disputed'
    rule_id: str
    notes: str
    corpus_basename: str = ""
    corpus_verification_status: str = VerificationStatus.UNVERIFIED.value
    corpus_reference_eligibility: str = ReferenceEligibility.INELIGIBLE.value
    corpus_authority_basis: str = AuthorityBasis.UNKNOWN.value
    corpus_status: str = "UNVERIFIED"  # legacy single-axis
    corpus_may_satisfy_validation_gate: bool = False


def _carrying_dict(d: dict[str, Any], key: str) -> dict | object:
    return d[key] if key in d else "-"


def cross_validate_one(expected_gregorian: str, expected: dict, source: str, page: int | None, rule_id: str, corpus_basename: str = "") -> CrossValidationOutcome:
    """compare one expected vector to what the engine produces.

    `corpus_basename` is used to look up the corpus's two-axis
    evidence status in phase-1/conformance/STATUS.json. if not
    provided, the status defaults to UNVERIFIED + INELIGIBLE + unknown
    (fail-closed).

    the gate predicate is computed from the two axes:
        VERIFIED + ELIGIBLE -> may_satisfy_validation_gate=True
        anything else -> False

    Per Codex review of PR #15 (F1, P1): when the public `saka_year`
    field is `None` (the engine cannot endorse a year boundary without
    customary sign-off), the diagnostic field
    `saka_year_diagnostic_january_rollover` is compared instead. The
    outcome's `notes` carries the explanation so downstream consumers
    see the unavailable status, not a silent match.
    """
    date = _dt.date.fromisoformat(expected_gregorian)
    day = compose_day(date)

    public_saka_year = (
        day.saka.get("saka_year") if not day.saka.get("_oob_range") else None
    )
    diagnostic_saka_year = (
        day.saka.get("saka_year_diagnostic_january_rollover")
        if not day.saka.get("_oob_range")
        else None
    )

    actual: dict[str, Any] = {
        "pawukon_position": day.pawukon["position_in_cycle"],
        "pawukon_wuku_idx": day.pawukon["wuku_idx"],
        "saka_year": public_saka_year,
        "sasih_idx": day.saka.get("sasih_idx") if not day.saka.get("_oob_range") else None,
    }
    expected_norm = {
        "pawukon_position": expected["pawukon_position"],
        "pawukon_wuku_idx": expected["pawukon_wuku_idx"],
        "saka_year": expected.get("saka_year"),
        "sasih_idx": expected.get("sasih_idx"),
    }
    fields_ok: dict[str, bool] = {}
    field_notes: dict[str, str] = {}
    for field, exp_v in expected_norm.items():
        act_v = actual.get(field)
        if exp_v is None:
            fields_ok[field] = True
            continue
        if field == "saka_year" and act_v is None and diagnostic_saka_year is not None:
            # public saka_year is unavailable (F1); compare against the
            # diagnostic, but flag the field as "diagnostic-only" so the
            # outcome's notes don't claim a public-surface match.
            fields_ok[field] = diagnostic_saka_year == exp_v
            field_notes[field] = (
                "public saka_year unavailable (None); compared against "
                "saka_year_diagnostic_january_rollover per F1"
            )
            continue
        fields_ok[field] = act_v == exp_v

    status = "match" if all(fields_ok.values()) else "disputed"
    notes_parts = [
        "all fields match published source" if status == "match"
        else "engine disagrees with published source -- human review required"
    ]
    if field_notes:
        notes_parts.append("; ".join(f"{k}: {v}" for k, v in field_notes.items()))
    notes = "".join(notes_parts)

    record = corpus_record_for(corpus_basename) if corpus_basename else None
    if record is None:
        v_str = VerificationStatus.UNVERIFIED.value
        r_str = ReferenceEligibility.INELIGIBLE.value
        a_str = AuthorityBasis.UNKNOWN.value
        legacy = "UNVERIFIED"
        may_gate = False
    else:
        v_str = record.verification_status.value
        r_str = record.reference_eligibility.value
        a_str = record.authority_basis.value
        legacy = record.legacy_status.value
        may_gate = can_satisfy_validation_gate(record)

    return CrossValidationOutcome(
        date=expected_gregorian,
        source=source,
        page=page,
        expected=expected_norm,
        actual=actual,
        fields_ok=fields_ok,
        status=status,
        rule_id=rule_id,
        notes=notes,
        corpus_basename=corpus_basename,
        corpus_verification_status=v_str,
        corpus_reference_eligibility=r_str,
        corpus_authority_basis=a_str,
        corpus_status=legacy,
        corpus_may_satisfy_validation_gate=may_gate,
    )


def cross_validate_all() -> list[CrossValidationOutcome]:
    """cross-validate every published corpus against the engine.

    returns outcomes annotated with each corpus's two-axis evidence
    status. the function does NOT raise if a corpus is UNVERIFIED or
    INELIGIBLE — it loads and compares anyway, and records the status
    on each outcome. callers that need to gate behavior on corpus
    authority should check
    `outcome.corpus_may_satisfy_validation_gate` (or call
    `can_satisfy_validation_gate(record)` directly with a CorpusRecord).
    """
    out: list[CrossValidationOutcome] = []
    out.extend(_run_corpus_file("cunningham_1994"))
    out.extend(_run_corpus_file("igarashi_1999"))
    return out


def _run_corpus_file(name: str) -> list[CrossValidationOutcome]:
    """load json corpus `name.json` and run cross-validation for each row.

    each row's outcome carries the corpus's two-axis evidence status.
    the corpus's `may_satisfy_validation_gate` field is propagated per
    outcome so downstream consumers cannot accidentally treat an
    UNVERIFIED / INELIGIBLE corpus's values as authoritative.
    """
    path = CORPUS_DIR / f"{name}.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for row in raw:
        out.append(
            cross_validate_one(
                expected_gregorian=row["gregorian"],
                expected=row,
                source=row["source"],
                page=row.get("page"),
                rule_id=row["rule_id"],
                corpus_basename=name,
            )
        )
    return out


def format_outcome(o: CrossValidationOutcome) -> str:
    """render an outcome as a multi-line text block (indonesian-friendly).

    includes the corpus's two-axis evidence status and the gate
    result. outcomes that do not pass the gate are explicitly labeled
    as NON-AUTHORITATIVE so readers do not mistake diagnostic output
    for ground truth.
    """
    ok = lambda b: "OK" if b else "DRIFT"
    fields = " ".join(f"{k.replace('_', ' ')}={ok(v)}" for k, v in o.fields_ok.items())
    gate_marker = (
        "AUTHORITATIVE"
        if o.corpus_may_satisfy_validation_gate
        else (
            f"NON-AUTHORITATIVE "
            f"[{o.corpus_verification_status} + "
            f"{o.corpus_reference_eligibility} + "
            f"{o.corpus_authority_basis}]"
        )
    )
    return (
        f"date        : {o.date}\n"
        f"sumber      : {o.source}\n"
        f"halaman     : {o.page}\n"
        f"ruleset     : {o.rule_id}\n"
        f"corpus      : {o.corpus_basename} [{gate_marker}]\n"
        f"status      : {o.status}\n"
        f"expected    : {o.expected}\n"
        f"actual      : {o.actual}\n"
        f"detail      : {fields}\n"
        f"catatan     : {o.notes}"
    )
