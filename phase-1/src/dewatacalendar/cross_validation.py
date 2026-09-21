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
from dataclasses import asdict, dataclass, field
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

    Field-comparison semantics (round-2 clarification):
      - `fields_ok` records the boolean comparison result. For
        `saka_year`, this is True only when the **public** engine value
        equals the expected value, OR when the reference does not
        specify an expected value (None).
      - `fields_unavailable` records whether a public engine field was
        required by the reference but the engine returned None. The
        diagnostic field's agreement with expected does NOT mark the
        public field as available.
      - `fields_diagnostic_match` records whether a separate diagnostic
        value (e.g. `saka_year_diagnostic_january_rollover`) agreed
        with the expected. This is informational and never feeds into
        `fields_ok` or `status`.

    status values:
      - "match": all required public fields equal expected; no
        public field was unavailable.
      - "disputed": at least one public field disagrees with expected
        (and was not unavailable).
      - "incomplete_public": at least one required public field was
        unavailable. Diagnostic agreement does not satisfy this. The
        outcome cannot be a "match" until the public field is
        available.
    """
    date: str
    source: str
    page: int | None
    expected: dict[str, Any]
    actual: dict[str, Any]
    fields_ok: dict[str, bool]
    status: str                    # 'match' | 'disputed' | 'incomplete_public'
    rule_id: str
    notes: str
    fields_unavailable: dict[str, bool] = field(default_factory=dict)
    fields_diagnostic_match: dict[str, bool] = field(default_factory=dict)
    fields_disagree_available: dict[str, bool] = field(default_factory=dict)
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

    Field-comparison semantics (round-2 clarification):
      - When the public engine value is None but the reference specifies
        an expected value, `fields_ok[field]` is False and
        `fields_unavailable[field]` is True. The diagnostic value is
        compared separately and recorded in
        `fields_diagnostic_match[field]`; it never satisfies
        `fields_ok`.
      - When the reference does not specify an expected value
        (`expected[field] is None`), `fields_ok[field]` is True and
        neither the public nor diagnostic field is required.
      - `status` is "match" only when every required public field is
        available and agrees. "incomplete_public" if at least one
        required public field was unavailable. "disputed" otherwise.

    The diagnostic value is exposed for downstream dispute packet
    authors and the harness; it is not a substitute for the public
    field.
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
    fields_unavailable: dict[str, bool] = {}
    fields_diagnostic_match: dict[str, bool] = {}
    for field_name, exp_v in expected_norm.items():
        act_v = actual.get(field_name)
        # Reference does not specify this field: pass through.
        if exp_v is None:
            fields_ok[field_name] = True
            continue
        # Special case for saka_year: track unavailability and the
        # diagnostic agreement separately. The public field is required
        # but unavailable; the diagnostic comparison is informational.
        if field_name == "saka_year" and act_v is None:
            fields_ok[field_name] = False
            fields_unavailable[field_name] = True
            if diagnostic_saka_year is not None:
                fields_diagnostic_match[field_name] = (
                    diagnostic_saka_year == exp_v
                )
            continue
        # Default case: public-field comparison only.
        fields_ok[field_name] = act_v == exp_v

    # Status semantics (round-2 precedence, fixed for round-3 precedence
    # correction):
    #   1. If any AVAILABLE required public field disagrees with expected:
    #      status = "disputed". The disagreement is the primary signal;
    #      unavailability of another field does not hide it.
    #   2. Else if any required field is unavailable: status =
    #      "incomplete_public". No disagreement, but a required field
    #      cannot be evaluated against the reference.
    #   3. Else: status = "match". All required fields available and
    #      agreed.
    # The precedence correction prevents the unavailable-year path from
    # masking substantive disagreements on pawukon / sasih / saka fields
    # when the public saka_year is unavailable.

    # Compute the subset of fields_ok that disagree on AVAILABLE fields.
    # `fields_ok[k]` is False for unavailable k too; we want to ignore
    # those when deciding whether a substantive disagreement exists.
    fields_disagree_available: dict[str, bool] = {
        k: False for k in fields_ok
    }
    for k, v in fields_ok.items():
        if fields_unavailable.get(k):
            continue
        fields_disagree_available[k] = not v

    disagreement_parts: list[str] = []
    if any(fields_disagree_available.values()):
        disagreement_parts = sorted(
            k for k, v in fields_disagree_available.items() if v
        )

    if disagreement_parts:
        status = "disputed"
        notes_parts = [
            "engine public output disagrees with published source on "
            f"available field(s): {', '.join(disagreement_parts)} "
            "-- human review required"
        ]
        if any(fields_unavailable.values()):
            notes_parts.append(
                "required public field(s) unavailable: "
                + ", ".join(sorted(k for k, v in fields_unavailable.items() if v))
            )
        if fields_diagnostic_match:
            notes_parts.append(
                "diagnostic agreement (informational, not a public match): "
                + ", ".join(
                    f"{k}={'yes' if v else 'no'}"
                    for k, v in sorted(fields_diagnostic_match.items())
                )
            )
        notes = "; ".join(notes_parts)
    elif any(fields_unavailable.values()):
        status = "incomplete_public"
        notes_parts = [
            "required public field(s) unavailable: "
            + ", ".join(sorted(k for k, v in fields_unavailable.items() if v))
        ]
        if fields_diagnostic_match:
            notes_parts.append(
                "diagnostic agreement (informational, not a public match): "
                + ", ".join(
                    f"{k}={'yes' if v else 'no'}"
                    for k, v in sorted(fields_diagnostic_match.items())
                )
            )
        notes = "; ".join(notes_parts)
    elif all(fields_ok.values()):
        status = "match"
        notes = "all required public fields match published source"
    else:
        # Defensive: should not be reachable, since disagreement_parts
        # would have been non-empty if any fields_ok[k] was False and
        # the field was available. Treat as disputed.
        status = "disputed"
        notes = (
            "engine public output disagrees with published source -- "
            "human review required"
        )

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
        fields_unavailable=fields_unavailable,
        fields_diagnostic_match=fields_diagnostic_match,
        fields_disagree_available=fields_disagree_available,
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
