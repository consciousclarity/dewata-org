"""DSP calendar endpoints — thin wrapper around dewatacalendar.api."""

from __future__ import annotations

import datetime as _dt

from fastapi import APIRouter, HTTPException, Query

from dewatacalendar.api import compose_day
from dewatacalendar.exceptions import InvalidDateError
from dewatacalendar.rulesets import RULESET_VERSION


router = APIRouter(prefix="/dsp/v0.1/calendar", tags=["calendar"])


@router.get("/ruleset")
def ruleset() -> dict[str, str]:
    return {"version": RULESET_VERSION}


@router.get("/date/{date}")
def get_date(date: str) -> dict:
    """return the full calendar state for one gregorian date (YYYY-MM-DD)."""
    try:
        d = _dt.date.fromisoformat(date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"date format: {exc}") from exc
    try:
        day = compose_day(d)
    except InvalidDateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    from dataclasses import asdict  # noqa: PLC0415 - lazy
    return asdict(day)


@router.get("/range")
def get_range(
    start: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    fmt: str = Query("json", pattern=r"^(json|jsonl)$"),
) -> dict | str:
    """return a bulk range. fmt=json returns an object; fmt=jsonl returns newline JSON lines."""
    s = _dt.date.fromisoformat(start)
    e = _dt.date.fromisoformat(end)
    if e < s:
        raise HTTPException(status_code=400, detail="end before start")
    out = []
    d = s
    while d <= e:
        out.append(_as_dict(compose_day(d)))
        d += _dt.timedelta(days=1)
    if fmt == "jsonl":
        import json  # noqa: PLC0415 - lazy
        return "\n".join(json.dumps(r, ensure_ascii=False) for r in out)
    return {"start": start, "end": end, "count": len(out), "items": out}


def _as_dict(obj) -> dict:
    from dataclasses import asdict  # noqa: PLC0415 - lazy
    return asdict(obj)
