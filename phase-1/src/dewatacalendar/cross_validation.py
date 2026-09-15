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
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .api import compose_day  # noqa: PLC0415
from .corpus_status import (  # noqa: PLC0415
    can_satisfy_validation_gate,
    corpus_status_for,
)
from .published_cunningham import load_cunningham_corpus  # noqa: F401 — re-export
from .published_igarashi import load_igarashi_corpus  # noqa: F401 — re-export


CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "conformance" / "published"


@dataclass(frozen=True, slots=True)
class CrossValidationOutcome:
    """the outcome of comparing one published vector against the engine.

    `corpus_status` records the authority status of the source corpus
    per phase-1/conformance/STATUS.json. downstream consumers MUST
    check `corpus_status` before treating any field of `expected` or
    `actual` as authoritative. an outcome with status
    UNVERIFIED / NON_AUTHORITATIVE is informational; an outcome with
    status ATTESTED may satisfy an independent-reference validation
    gate.
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
    corpus_status: str = "UNVERIFIED"
    corpus_may_satisfy_validation_gate: bool = False


def _carrying_dict(d: dict[str, Any], key: str) -> dict | object:
    return d[key] if key in d else "-"


def cross_validate_one(expected_gregorian: str, expected: dict, source: str, page: int | None, rule_id: str, corpus_basename: str = "") -> CrossValidationOutcome:
    """compare one expected vector to what the engine produces.

    `corpus_basename` is used to look up the corpus's authority
    status in phase-1/conformance/STATUS.json. if not provided,
    the status defaults to UNVERIFIED (fail-closed).
    """
    date = _dt.date.fromisoformat(expected_gregorian)
    day = compose_day(date)

    actual: dict[str, Any] = {
        "pawukon_position": day.pawukon["position_in_cycle"],
        "pawukon_wuku_idx": day.pawukon["wuku_idx"],
        "saka_year": day.saka.get("saka_year") if not day.saka.get("_oob_range") else None,
        "sasih_idx": day.saka.get("sasih_idx") if not day.saka.get("_oob_range") else None,
    }
    expected_norm = {
        "pawukon_position": expected["pawukon_position"],
        "pawukon_wuku_idx": expected["pawukon_wuku_idx"],
        "saka_year": expected.get("saka_year"),
        "sasih_idx": expected.get("sasih_idx"),
    }
    fields_ok: dict[str, bool] = {}
    for field, exp_v in expected_norm.items():
        act_v = actual.get(field)
        if exp_v is None:
            fields_ok[field] = True
            continue
        fields_ok[field] = act_v == exp_v

    status = "match" if all(fields_ok.values()) else "disputed"
    notes = (
        "all fields match published source"
        if status == "match"
        else "engine disagrees with published source — human review required"
    )

    cstatus = corpus_status_for(corpus_basename) if corpus_basename else None
    from .corpus_status import CorpusStatus  # noqa: PLC0415 - lazy
    corpus_status_str = cstatus.value if cstatus is not None else CorpusStatus.UNVERIFIED.value
    may_gate = can_satisfy_validation_gate(corpus_status_str)

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
        corpus_status=corpus_status_str,
        corpus_may_satisfy_validation_gate=may_gate,
    )


def cross_validate_all() -> list[CrossValidationOutcome]:
    """cross-validate every published corpus against the engine.

    returns outcomes annotated with each corpus's authority status.
    the function does NOT raise if a corpus is UNVERIFIED or
    NON_AUTHORITATIVE — it loads and compares anyway, and records
    the status on each outcome. callers that need to gate behavior
    on corpus authority should check
    `outcome.corpus_may_satisfy_validation_gate` (or call
    `can_satisfy_validation_gate(outcome.corpus_status)` directly).
    """
    out: list[CrossValidationOutcome] = []
    out.extend(_run_corpus_file("cunningham_1994"))
    out.extend(_run_corpus_file("igarashi_1999"))
    return out


def _run_corpus_file(name: str) -> list[CrossValidationOutcome]:
    """load json corpus `name.json` and run cross-validation for each row.

    each row's outcome carries the corpus's authority status. the
    corpus's `may_satisfy_validation_gate` field is propagated per
    outcome so downstream consumers cannot accidentally treat an
    UNVERIFIED corpus's values as authoritative.
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

    includes the corpus's authority status. outcomes with status
    UNVERIFIED / NON_AUTHORITATIVE are explicitly labeled as such so
    readers do not mistake diagnostic output for ground truth.
    """
    ok = lambda b: "OK" if b else "DRIFT"
    fields = " ".join(f"{k.replace('_', ' ')}={ok(v)}" for k, v in o.fields_ok.items())
    gate_marker = (
        "AUTHORITATIVE"
        if o.corpus_may_satisfy_validation_gate
        else f"NON-AUTHORITATIVE ({o.corpus_status})"
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


def to_dict(o: CrossValidationOutcome) -> dict[str, Any]:
    """serialize an outcome to a JSON-safe dict."""
    return asdict(o)
