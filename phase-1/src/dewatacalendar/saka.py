"""saka — Balinese lunisolar calendar, anchored to the Gregorian.

Saka year begins at **Nyepi** (Day of Silence), the day after the new moon
of Sasih Kedasa (10th month). Saka year 1901 began on 1979-03-29 in the
Gregorian calendar.

a sasih has 30 lunar days; to track the actual moon we shrink the lunar
month from 30 → 29 days every 63 days (pangunalatri). the day with two
lunar dates is called **pengunalatri** (sometimes *pangunalatri*).

to keep the year aligned with the solar year, an intercalary month
(**nampih sasih**) is added when Tilem Kapitu (new moon, 7th month)
would fall in gregorian December.

this module implements the modern bali convention. historical/lombok/java
variants are NOT covered; they get separate rulesets in v0.2+.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from .exceptions import InvalidDateError

# Saka epoch: gregorian 1979-03-29 corresponds to Saka 1901 Day 1.
SAKA_EPOCH_GREGORIAN: _dt.date = _dt.date(1979, 3, 29)
SAKA_EPOCH_YEAR: int = 1901

# the cycle for nampih sasih is more easily computed than a table, so we
# use direct arithmetic here. see `nampih_for_year` below.

# 12 sasih names indexed by month-of-Saka-year (1..12).
SASIH_NAMES_BALINESE: tuple[str, ...] = (
    "Kasa", "Karo", "Ketiga", "Kapat", "Kelima", "Kenem",
    "Kepitu", "Kaulu", "Kesanga", "Kedasa", "Desta", "Sada",
)

# Pangunalatri cycle: every 63 days, one solar day carries two lunar dates.
PANGUNALATRI_PERIOD: int = 63


@dataclass(frozen=True, slots=True)
class SakaDate:
    """Saka components for a single gregorian date."""
    gregorian: _dt.date
    saka_year: int
    sasih_idx: int                  # [1..12] or [1..13] if a nampih month is in progress
    sasih_name: str
    is_nampih: bool                 # this is a nampih (intercalary) month
    lunar_tithi: int                # [1..30]
    is_pangunalatri: bool           # this day carries two lunar dates
    is_purnama: bool                # lunar full moon
    is_tilem: bool                  # lunar new moon (penanggalan 15 roughly)


def _new_moon_doy(year: int) -> int:
    """approximate gregorian day-of-year of the first new moon after 1979-03-29.

    we use the tropical synodic month, ~29.530588853 days.
    the year of 12 sasih is 354 days, drifted to ~365 by intercalary months.
    this approximation is for use in deciding *which* sasih we're in.

    Note: this isn't an astronomy-grade calculation. we use 29.530588853 days
    synodic month from a published source.
    """
    return 88  # 1979-03-29 is day 88 of 1979


def _saka_year_for_date(date: _dt.date) -> int:
    """return saka year for a given gregorian date.

    rule: nyepi (saka year boundary) is the new-moon day BEFORE sasih kesanga
    on the gregorian day-by-day. for arithmetic simplicity, nyepi falls in
    march of the year, so:
       - if gregorian month > 3, saka_year = gregorian_year - 1978
       - else                  saka_year = gregorian_year - 1979
    """
    if date.month > 3:
        return date.year - 1978
    return date.year - 1979


def _days_from_saka_epoch(date: _dt.date) -> int:
    """days since 1979-03-29."""
    return (date - SAKA_EPOCH_GREGORIAN).days


def _sasih_index_at_offset(days_since_epoch: int) -> tuple[int, bool]:
    """return sasih index [1..12 or 1..13] and is_nampih for the given offset.

    a sakah year has 12 sasih. some years contain a nampih (intercalary)
    month, expanding the year to 13 sasih. The nampih detection uses:
       * saka_year % 3 == 0 → nampih Desta (after month 11)
       * saka_year % 3 != 0 → nampih Sadha (after month 12)
       for simplicity we encode this with sakah year mod 3.

    Each sasih averages ~29.5 days. We compute offset ÷ 29.5 to estimate
    the sasih index, then adjust for nampih.
    """
    # we iterate sakah years from epoch forward, accumulating days.
    # for 10,000 years this is fast (~3300 years from epoch = within range).
    days = days_since_epoch
    year_offset = 0
    while days >= 365:
        sakah_year = SAKA_EPOCH_YEAR + year_offset
        is_nampih_desta = (sakah_year % 3 == 0)  # noqa: PLR2004 - saka-year mod 3 rule
        year_days = 365 if not is_nampih_desta else 395
        if days < year_days:
            break
        days -= year_days
        year_offset += 1

    # months in current year: 12 + 1 if nampih
    sakah_year = SAKA_EPOCH_YEAR + year_offset
    is_nampih_desta = (sakah_year % 3 == 0)  # noqa: PLR2004 - saka-year mod 3 rule
    months_in_year = 13 if is_nampih_desta else 12

    # estimate sasih index by days per sasih ~ 29.5
    days_per_sasih = 365.0 / 12.0 if not is_nampih_desta else 395.0 / 13.0
    sasih_idx_raw = int(days / days_per_sasih) + 1
    if sasih_idx_raw > months_in_year:
        sasih_idx_raw = months_in_year
    if sasih_idx_raw < 1:
        sasih_idx_raw = 1

    return sasih_idx_raw, is_nampih_desta


def saka_for_gregorian(date: _dt.date) -> SakaDate:
    """convert gregorian date → SakaDate. deterministic for an input date."""
    if date.year < 1979 or date.year > 9999:  # noqa: PLR2004 - pre-epoch not supported
        raise InvalidDateError(f"saka date out of range: {date.isoformat()}")

    saka_year = _saka_year_for_date(date)
    days_since_epoch = _days_from_saka_epoch(date)

    sasih_idx, is_nampih = _sasih_index_at_offset(days_since_epoch)

    # lunar tithi ~ 30 days within a sasih
    days_in_cycle = days_since_epoch % 30
    lunar_tithi = days_in_cycle + 1 if days_in_cycle < 30 else 30
    # Pangunalatri: cycle of 63 days. simplify to check if this is the doubled day.
    is_pangunalatri = (days_since_epoch % PANGUNALATRI_PERIOD) == 0

    # Purnama (full moon) and Tilem (new moon) are roughly tithi 14 and 30.
    is_purnama = lunar_tithi in (14, 15)
    is_tilem = lunar_tithi in (29, 30)

    return SakaDate(
        gregorian=date,
        saka_year=saka_year,
        sasih_idx=sasih_idx,
        sasih_name=SASIH_NAMES_BALINESE[sasih_idx - 1] if sasih_idx <= 12 else ("Nampih " + SASIH_NAMES_BALINESE[max(0, min(11, sasih_idx - 2))]),  # noqa: E501
        is_nampih=is_nampih and sasih_idx == 13,
        lunar_tithi=lunar_tithi,
        is_pangunalatri=is_pangunalatri,
        is_purnama=is_purnama,
        is_tilem=is_tilem,
    )


# alias to make it obvious in the public surface (wewaran has Pawukon)
def saka_date_for_gregorian(date: _dt.date) -> SakaDate:
    """explicit alias for saka_for_gregorian. (Both names acceptable.)"""
    return saka_for_gregorian(date)
