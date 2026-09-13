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
from .published_cunningham import load_cunningham_corpus  # noqa: F401 — re-export
from .published_igarashi import load_igarashi_corpus  # noqa: F401 — re-export


CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "conformance" / "published"


@dataclass(frozen=True, slots=True)
class CrossValidationOutcome:
    """the outcome of comparing one published vector against the engine."""
    date: str
    source: str
    page: int | None
    expected: dict[str, Any]
    actual: dict[str, Any]
    fields_ok: dict[str, bool]
    status: str                    # 'match' | 'drift' | 'disputed'
    rule_id: str
    notes: str


def _carrying_dict(d: dict[str, Any], key: str) -> dict | object:
    return d[key] if key in d else "-"


def cross_validate_one(expected_gregorian: str, expected: dict, source: str, page: int | None, rule_id: str) -> CrossValidationOutcome:
    """compare one expected vector to what the engine produces."""
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
    )


def cross_validate_all() -> list[CrossValidationOutcome]:
    """cross-validate every published corpus against the engine."""
    out: list[CrossValidationOutcome] = []
    out.extend(_run_corpus_file("cunningham_1994"))
    out.extend(_run_corpus_file("igarashi_1999"))
    return out


def _run_corpus_file(name: str) -> list[CrossValidationOutcome]:
    """load json corpus `name.json` and run cross-validation for each row."""
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
            )
        )
    return out


def format_outcome(o: CrossValidationOutcome) -> str:
    """render an outcome as a multi-line text block (indonesian-friendly)."""
    ok = lambda b: "OK" if b else "DRIFT"
    fields = " ".join(f"{k.replace('_', ' ')}={ok(v)}" for k, v in o.fields_ok.items())
    return (
        f"date        : {o.date}\n"
        f"sumber      : {o.source}\n"
        f"halaman     : {o.page}\n"
        f"ruleset     : {o.rule_id}\n"
        f"status      : {o.status}\n"
        f"expected    : {o.expected}\n"
        f"actual      : {o.actual}\n"
        f"detail      : {fields}\n"
        f"catatan     : {o.notes}"
    )


def to_dict(o: CrossValidationOutcome) -> dict[str, Any]:
    """serialize an outcome to a JSON-safe dict."""
    return asdict(o)
