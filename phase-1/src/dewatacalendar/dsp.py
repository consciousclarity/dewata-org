"""DSP calendar endpoints — thin wrapper around dewatacalendar.api."""

from __future__ import annotations

import datetime as _dt
import logging
import os
from typing import Final

from fastapi import APIRouter, HTTPException, Query

from dewatacalendar.api import compose_day
from dewatacalendar.exceptions import InvalidDateError
from dewatacalendar.rulesets import RULESET_VERSION

_log = logging.getLogger(__name__)

# Inclusive end-start cap, in days. 366 covers any single civil year
# including a leap day, which is the natural request size and matches
# the de facto "give me one year of calendar data" use case.
#
# 366 is a HARD safety ceiling. The engine can compute any range, but
# the API surface does not expose more than 366 inclusive days under
# any environment configuration. Operators who need longer ranges
# must build a separate capacity-reviewed path (pagination, streaming,
# authentication, rate limiting, or asynchronous export).
DEFAULT_MAX_RANGE_DAYS: Final = 366

RANGE_LIMIT_CONFIG_VAR: Final = "DEWATA_MAX_RANGE_DAYS"
RANGE_ERROR_ID: Final = "range_too_large"
RANGE_ERROR_CODE: Final = "RANGE_LIMIT_EXCEEDED"


def _resolve_max_range_days() -> int:
    """Resolve `DEWATA_MAX_RANGE_DAYS` from the environment.

    The result is always a value in `[1, 366]` (inclusive). Anything
    else — unset, empty, non-integer, ≤ 0, or > 366 — falls back to
    `DEFAULT_MAX_RANGE_DAYS` and logs a WARN. The cap never raises
    above 366; this is a non-negotiable safety ceiling.
    """
    raw = os.environ.get(RANGE_LIMIT_CONFIG_VAR)
    if raw is None or raw.strip() == "":
        return DEFAULT_MAX_RANGE_DAYS
    try:
        value = int(raw)
    except ValueError:
        _log.warning(
            "%s=%r is not an integer; falling back to default %d",
            RANGE_LIMIT_CONFIG_VAR, raw, DEFAULT_MAX_RANGE_DAYS,
        )
        return DEFAULT_MAX_RANGE_DAYS
    if value < 1 or value > DEFAULT_MAX_RANGE_DAYS:
        _log.warning(
            "%s=%r outside [1, %d]; falling back to default %d",
            RANGE_LIMIT_CONFIG_VAR, value, DEFAULT_MAX_RANGE_DAYS, DEFAULT_MAX_RANGE_DAYS,
        )
        return DEFAULT_MAX_RANGE_DAYS
    return value


# Resolved once at module import. The API process loads this module at
# startup, so invalid configuration is caught here and never reaches a
# request handler.
_MAX_RANGE_DAYS: Final[int] = _resolve_max_range_days()


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
    r"""Return a bulk range of inclusive `[start, end]` calendar days.

    The inclusive day count is hard-capped at 366. A request that
    exceeds the cap receives HTTP 413. The cap is fixed at 366; the
    environment variable `DEWATA_MAX_RANGE_DAYS` may configure a
    *smaller* value (1..366) but cannot raise the limit above 366,
    because 366 is the documented safety ceiling and larger ranges
    re-open the audited denial-of-service path.

    **Response format.** `fmt=json` (default) returns
    ``{"start": ..., "end": ..., "count": <int>, "items": [...]}``
    where `items` is the array of full `CalendarDay` objects, identical
    to the original wire shape. `fmt=jsonl` returns a single string
    of one JSON object per line. **Single-date behavior** (`start ==
    end`) returns `count: 1` through the same inclusive loop; there is
    no separate code path.

    **HTTP status codes.**

    * 200 — well-formed range within the cap. The body shape is
      `{"start": ..., "end": ..., "count": <int>, "items": [...]}`.
    * 400 — `end < start` (body:
      `{"detail": {"error": "range_reversed", "message": "end before start"}}`)
      OR `start`/`end` matches the regex but is not a real calendar
      day (e.g. `2026-09-99`). The body shape is
      `{"detail": {"error": "invalid_date", "field": "<start|end>",
                   "message": "must be a valid Gregorian date in
                              YYYY-MM-DD format"}}`. The message is a
      fixed stable string; no Python exception text or internal paths
      are exposed.
    * 413 — well-formed range that exceeds the configured cap.
      Body shape:

      ```json
      {
        "detail": {
          "error": "range_too_large",
          "code": "RANGE_LIMIT_EXCEEDED",
          "max_days": 366,
          "requested_days": <int>
        }
      }
      ```

      `error` is the stable machine-readable identifier.
      `code` is the parallel dispute-style reference.
      `max_days` and `requested_days` are integers the client can
      act on. No filesystem paths or internal error text.
    * 422 — issued by FastAPI itself when `start` or `end` fails the
      `YYYY-MM-DD` regex pattern (e.g. `not-a-date`). The body shape
      is FastAPI's default `{"detail": [...]}` validation envelope.

    **Why HTTP 413 (RFC 7231 section 6.5.11).** "The 413 (Request
    Entity Too Large) status code indicates that the request is larger
    than the server is willing to process." That is the literal
    semantic match. Codes considered and rejected: 400 (would
    conflate malformed vs. oversize), 403 (implying authorisation),
    422 (a body-validation code applied here to a query-parameter
    capacity check).

    **Configuration.** `DEWATA_MAX_RANGE_DAYS` may be set to an integer
    between 1 and 366 inclusive to lower the cap. Set values outside
    that range (unset, empty, non-integer, <= 0, > 366) fall back to
    the default 366 and log a WARN. The cap is read once at module
    import; restart the API process to change it.

    **If longer ranges are needed.** A request that exceeds the
    366-day safety ceiling is rejected. Longer ranges require a
    separate capacity-reviewed design (pagination, streaming,
    authentication, rate limiting, or asynchronous export). Adding
    a knob that lifts the ceiling is **not** the answer.
    """
    try:
        s = _dt.date.fromisoformat(start)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_date",
                "field": "start",
                "message": "must be a valid Gregorian date in YYYY-MM-DD format",
            },
        ) from None
    try:
        e = _dt.date.fromisoformat(end)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_date",
                "field": "end",
                "message": "must be a valid Gregorian date in YYYY-MM-DD format",
            },
        ) from None
    if e < s:
        raise HTTPException(
            status_code=400,
            detail={"error": "range_reversed", "message": "end before start"},
        )
    requested_days = (e - s).days + 1  # inclusive
    if requested_days > _MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=413,
            detail={
                "error": RANGE_ERROR_ID,
                "code": RANGE_ERROR_CODE,
                "max_days": _MAX_RANGE_DAYS,
                "requested_days": requested_days,
            },
        )
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


def get_configured_max_range_days() -> int:
    """return the active range cap (for diagnostics and tests)."""
    return _MAX_RANGE_DAYS
