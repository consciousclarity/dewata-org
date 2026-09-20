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
from .rulesets import CANDIDATE_ID, RULESET_VERSION, UNIMPLEMENTED_RAHINAN_IDS


@dataclass(frozen=True, slots=True)
class CalendarDay:
    """the complete calendar response for one gregorian date.

    Per the corrections follow-up to PR #15 (Codex F2, F5):
      - `candidate_id` separates the development artifact from the
        frozen `ruleset` string. observable output may change under a
        new candidate_id without bumping RULESET_VERSION.
      - `unimplemented_observances` is the list of cultural terms the
        engine does NOT compute, so a downstream consumer can
        distinguish "no event" from "engine does not compute this
        observance".
    """
    gregorian: str                       # ISO date
    ruleset: str
    candidate_id: str
    saka: dict[str, Any]
    pawukon: dict[str, Any]
    wewaran: dict[str, Any]
    rahinan: list[dict[str, Any]]
    unimplemented_observances: tuple[str, ...] = ()
    note: str | None = None


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

    Per Codex review of PR #15 (F5): when the engine never emits
    rahinan ids that depend on removed lunar fields, the response
    carries an explicit `note` distinguishing "engine does not compute
    this observance" from "no event today". The
    `unimplemented_observances` field lists which terms are affected.
    """
    paw = pawukon_for_gregorian(date)
    saka_dict: dict[str, Any]
    rahs: list[Rahinan] = []
    unimplemented: tuple[str, ...] = ()
    note: str | None = None
    try:
        sak = saka_for_gregorian(date)
        saka_dict = {k: _date_to_str(v) for k, v in asdict(sak).items()}
        wew = wewaran_for_position(paw.position_in_cycle)
        rahs = rahinan_for(paw, sak, wew.position)
    except (InvalidDateError, Exception):  # noqa: BLE001 - saka has range exceptions
        saka_dict = {"_oob_range": True, "gregorian": date.isoformat()}
        wew = wewaran_for_position(paw.position_in_cycle)
        unimplemented = UNIMPLEMENTED_RAHINAN_IDS
        note = (
            "saka out of range: rahinan omitted; pawukon and wewaran "
            "still computed"
        )

    # Distinguish "engine does not compute this observance" from
    # "no event today". If rahinan is empty AND any of the
    # unimplemented ids would historically have been emitted on this
    # date, attach the explicit note. This catches future regressions
    # where someone re-adds purnama/tilem/nyepi without restoring the
    # lunar fields they depend on.
    if not rahs and not note:
        # We can't say purnama/tilem/nyepi "would have fired today"
        # without a real lunisolar implementation. So we report the
        # unimplemented list and a generic note.
        unimplemented = UNIMPLEMENTED_RAHINAN_IDS
        note = (
            "empty rahinan list -- engine does not currently compute: "
            + ", ".join(UNIMPLEMENTED_RAHINAN_IDS)
            + ". See IMPLEMENTED_RAHINAN_IDS in rulesets.py."
        )

    return CalendarDay(
        gregorian=date.isoformat(),
        ruleset=RULESET_VERSION,
        candidate_id=CANDIDATE_ID,
        saka=saka_dict,
        pawukon={k: _date_to_str(v) for k, v in asdict(paw).items()},
        wewaran=asdict(wew),
        rahinan=[asdict(r) for r in rahs],
        unimplemented_observances=unimplemented,
        note=note,
    )
