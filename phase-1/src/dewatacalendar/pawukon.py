"""pawukon — 210-day cycle, 10 concurrent weeks.

the cycle has no absolute numbering. day 1 of the cycle is what we choose
as the **epoch**, fixed to gregorian 1981-08-23 (a published authoritative
anchor: Cunningham 1994 gives a Pawukon-Saka correspondence at this date).

input  : gregorian date  (YYYY, M, D)
output : PawukonDate with
         position_in_cycle ∈ [1..210]
         wuku_idx          ∈ [1..30]      (1 = Sinta)
         wuku_name         str
         wuku_day          ∈ [1..7]       position within the wuku
         offset_from_epoch days since epoch

determinism:
    for fixed input date and fixed epoch, output is reproducible.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from .exceptions import InvalidDateError

# Pawukon epoch on the gregorian calendar.
# 1981-08-23 corresponds to Sasih Kasa, day 1, Wuku Sinta, Pancawara Paing,
# Saptawara Redite in Cunningham's reconstruction. Anchored to align with
# Igarashi's day-of-year arithmetic for 1981.
EPOCH: _dt.date = _dt.date(1981, 8, 23)

# 30 wuku names in cycle order, indexed 1..30. Sinta = 1, Watugunung = 30.
# Pinned to babadbali.com/pewarigaan/wuku.htm (SHA-256 3a970cf779236dda3d40800db1e66829e60d936eabaa231b43b4f010fb710af9).
# Governing source per governance decision 2026-09-19. 21/30 positions change vs prior engine state.
WUKU_NAMES_BALINESE: tuple[str, ...] = (
    "Sinta", "Landep", "Ukir", "Kulantir", "Tolu",
    "Gumbreg", "Wariga", "Warigadian", "Julungwangi", "Sungsang",
    "Dungulan", "Kuningan", "Langkir", "Medangsia", "Pujut",
    "Pahang", "Krulut", "Merakih", "Tambir", "Medangkungan",
    "Matal", "Uye", "Menail", "Prangbakat", "Bala",
    "Ugu", "Wayang", "Kelawu", "Dukut", "Watugunung",
)


@dataclass(frozen=True, slots=True)
class PawukonDate:
    """a single point on the pawukon cycle."""
    gregorian: _dt.date
    offset_from_epoch: int   # days since EPOCH (can be negative)
    position_in_cycle: int   # [1..210]
    cycle_count: int         # number of completed 210-day cycles since epoch
    wuku_idx: int            # [1..30]
    wuku_name: str           # balinese
    wuku_day: int            # [1..7]


def _position_from_offset(offset_days: int) -> PawukonDate:
    """compute PawukonDate from days-offset (can be negative).

    algorithm:
      offset = days_since_epoch (can be negative)
      cycle_pos = (offset mod 210) in [0..209], converted to [1..210]
      cycle_count = floor(offset / 210), adjusted for negative offsets
        so that EPOCH itself has cycle_count=0 and position=1.
      wuku_idx = ((cycle_pos - 1) // 7) + 1, in [1..30]
      wuku_day = ((cycle_pos - 1) % 7) + 1, in [1..7]
    """
    cycle_pos_zero_based = offset_days % 210
    cycle_pos = cycle_pos_zero_based + 1                # [1..210]
    cycle_count = offset_days // 210
    if offset_days < 0 and cycle_pos_zero_based != 0:
        cycle_count -= 1                                # negative offset adjustment
    wuku_idx = ((cycle_pos - 1) // 7) + 1               # [1..30]
    wuku_day = ((cycle_pos - 1) % 7) + 1                # [1..7]
    return PawukonDate(
        gregorian=EPOCH + _dt.timedelta(days=offset_days),
        offset_from_epoch=offset_days,
        position_in_cycle=cycle_pos,
        cycle_count=cycle_count,
        wuku_idx=wuku_idx,
        wuku_name=WUKU_NAMES_BALINESE[wuku_idx - 1],
        wuku_day=wuku_day,
    )


def pawukon_for_gregorian(date: _dt.date, *, epoch: _dt.date = EPOCH) -> PawukonDate:
    """convert gregorian date → PawukonDate."""
    if date.year < 1 or date.year > 9999:
        raise InvalidDateError(f"date out of range: {date.isoformat()}")
    offset = (date - epoch).days
    return _position_from_offset(offset)
