"""public api for the dewata calendar engine.

this module is the single import for downstream consumers; it exposes
the deterministic, versioned calendar functions.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from typing import Any

from .exceptions import InvalidDateError
from .pawukon import pawukon_for_gregorian, PawukonDate
from .saka import saka_for_gregorian, SakaDate
from .wewaran import wewaran_for_position, Wewaran
from .rahinan import rahinan_for, Rahinan
from .rulesets import RULESET_VERSION, RULESET_METADATA


@dataclass(frozen=True, slots=True)
class CalendarDay:
    """the complete calendar response for one gregorian date."""
    gregorian: str                       # ISO date
    ruleset: str
    saka: dict[str, Any]
    pawukon: dict[str, Any]
    wewaran: dict[str, Any]
    rahinan: list[dict[str, Any]]


def _date_to_str(value: object) -> object:
    """convert any nested `_dt.date` to its isoformat string."""
    if isinstance(value, _dt.date):
        return value.isoformat()
    return value


def compose_day(date: _dt.date) -> CalendarDay:
    """compute the full calendar state for a gregorian date.

    pawukon works for any year 1..9999. saka requires year >= 1979.
    if the date is pre-1979, saka fields carry `_oob_range: true` and
    rahinan is empty (cannot compute without a saka anchor).
    """
    paw = pawukon_for_gregorian(date)
    saka_dict: dict[str, Any]
    rahs: list[Rahinan] = []
    try:
        sak = saka_for_gregorian(date)
        saka_dict = {k: _date_to_str(v) for k, v in asdict(sak).items()}
        wew = wewaran_for_position(paw.position_in_cycle)
        rahs = rahinan_for(paw, sak, wew.position)
    except (InvalidDateError, Exception):  # noqa: BLE001 - saka has range exceptions
        saka_dict = {"_oob_range": True, "gregorian": date.isoformat()}
        wew = wewaran_for_position(paw.position_in_cycle)

    return CalendarDay(
        gregorian=date.isoformat(),
        ruleset=RULESET_VERSION,
        saka=saka_dict,
        pawukon={k: _date_to_str(v) for k, v in asdict(paw).items()},
        wewaran=asdict(wew),
        rahinan=[asdict(r) for r in rahs],
    )
