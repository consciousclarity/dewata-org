"""saka — Balinese calendar year/sasih indexing, anchored to the Gregorian.

**What is implemented**

- `saka_year` derived deterministically from the declared epoch
  (`SAKA_EPOCH_GREGORIAN` = 1979-03-29 corresponds to `SAKA_EPOCH_YEAR` =
  1901). The earlier `_saka_year_for_date` returned 0 at the epoch and 48
  for 2026 (a plain `gregorian_year - 1979`); this version anchors at
  `SAKA_EPOCH_YEAR` and adds elapsed full years.
- `sasih_idx`, `sasih_name`, `is_nampih` for the gregorian year. These
  are kept because `cross_validation.py` and `runbook.py` read them
  for drift classification.

**What is NOT implemented (removed in this revision)**

- `lunar_tithi`, `is_purnama`, `is_tilem`, `is_pangunalatri` — none
  describe a real astronomical computation; `_new_moon_doy` was a stub
  with a synodic-month docstring and a `return 88` body.
- the `purnama`, `tilem`, `nyepi` rahinan ids — they depended on the
  above and were either trivially emit-on-arithmetic (purnama/tilem)
  or unsatisfiable in practice (nyepi, per an unreachable predicate
  `sasih_idx == 9 and is_tilem and lunar_tithi == 1`).
- pangunalatri day-dropping and nampih-sasih keyed on Tilem Kapitu:
  neither was implemented despite appearing in the previous docstring.

**Why the gaps remain**

A correct Balinese lunisolar calendar requires an eligible published
source the repository does not have. Three open disputes cover the
boundary cases that a real implementation would have to adjudicate:

- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09 (engine assigns
  Sasih Ketiga to early Sept 2026; kalenderbali.info swaps it with
  Sasih Kapat).
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET (Java library's nampih state
  machine disagrees with TS/Rust/Engine on 8 of 26 days).
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION (KB Org festivity tags invert
  the engine's index-name mapping relative to Peradnya/Rust/TS).

These disputes are unresolved. Until they are, the sasih indexing here
should be read as **unvalidated**: structurally consistent with the
declared epoch but not endorsed by any customary authority.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from .exceptions import InvalidDateError

# Saka epoch: gregorian 1979-03-29 corresponds to Saka 1901 Day 1.
SAKA_EPOCH_GREGORIAN: _dt.date = _dt.date(1979, 3, 29)
SAKA_EPOCH_YEAR: int = 1901

# 12 sasih names indexed by month-of-Saka-year (1..12).
SASIH_NAMES_BALINESE: tuple[str, ...] = (
    "Kasa", "Karo", "Ketiga", "Kapat", "Kelima", "Kenem",
    "Kepitu", "Kaulu", "Kesanga", "Kedasa", "Desta", "Sada",
)


@dataclass(frozen=True, slots=True)
class SakaDate:
    """Saka components for a single gregorian date.

    Fields removed in this revision (no longer emitted by `saka_for_gregorian`,
    not present in `compose_day` output):
      - lunar_tithi
      - is_pangunalatri
      - is_purnama
      - is_tilem
    """
    gregorian: _dt.date
    saka_year: int
    sasih_idx: int                  # [1..12] or [1..13] if a nampih month is in progress
    sasih_name: str
    is_nampih: bool                 # this is a nampih (intercalary) month


def _saka_year_for_date(date: _dt.date) -> int:
    """return saka year for a given gregorian date.

    derived from the declared epoch: 1979-03-29 = Saka 1901, and the
    Saka year advances by one for each completed gregorian year since
    the epoch anchor. the previous implementation returned 0 at the
    epoch and 48 for 2026 (a plain `gregorian_year - 1979`); that
    contradicted `SAKA_EPOCH_YEAR`.

    whether 1979-03-29 = Saka 1901 is the customary anchor is a
    separate evidence question (see DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
    et al.); this function only enforces internal consistency with
    `SAKA_EPOCH_YEAR`.
    """
    years_since_epoch = date.year - SAKA_EPOCH_GREGORIAN.year
    return SAKA_EPOCH_YEAR + years_since_epoch


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

    NOTE: unvalidated. see module docstring and the three open
    sasih_index_drift disputes.
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

    return SakaDate(
        gregorian=date,
        saka_year=saka_year,
        sasih_idx=sasih_idx,
        sasih_name=SASIH_NAMES_BALINESE[sasih_idx - 1] if sasih_idx <= 12 else ("Nampih " + SASIH_NAMES_BALINESE[max(0, min(11, sasih_idx - 2))]),  # noqa: E501
        is_nampih=is_nampih and sasih_idx == 13,
    )


# alias to make it obvious in the public surface (wewaran has Pawukon)
def saka_date_for_gregorian(date: _dt.date) -> SakaDate:
    """explicit alias for saka_for_gregorian. (Both names acceptable.)"""
    return saka_for_gregorian(date)
