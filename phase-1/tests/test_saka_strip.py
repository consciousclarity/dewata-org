"""strip-and-gate regression tests for the Saka module.

These tests pin three properties after the 2026-09-20 strip of
unimplemented fields and rahinan from `saka.py` and `rahinan.py`:

1. `_saka_year_for_date` is anchored at `SAKA_EPOCH_YEAR` for
   `SAKA_EPOCH_GREGORIAN` (the prior implementation returned 0 at
   the epoch and 48 for 2026).

2. `compose_day` does not surface the four removed fields
   (`lunar_tithi`, `is_purnama`, `is_tilem`, `is_pangunalatri`)
   anywhere in the `saka` dict.

3. The engine never emits `purnama`, `tilem`, or `nyepi` rahinan ids
   over a multi-year scan. This is a regression guard: if anyone
   re-adds those ids without first implementing a real lunisolar
   source and resolving the open sasih_index_drift disputes, this
   test fails.
"""

from __future__ import annotations

import datetime as _dt

import pytest

from dewatacalendar.api import compose_day
from dewatacalendar.saka import (
    SAKA_EPOCH_GREGORIAN,
    SAKA_EPOCH_YEAR,
    saka_for_gregorian,
)


# Fields removed from SakaDate in the strip revision.
# Listed as constants so the regression assertion reads cleanly.
REMOVED_SAKA_FIELDS = (
    "lunar_tithi",
    "is_purnama",
    "is_tilem",
    "is_pangunalatri",
)


# Rahinan ids whose emission depended on the removed saka fields and
# which the engine must therefore never produce.
REMOVED_RAHINAN_IDS = ("purnama", "tilem", "nyepi")


def test_saka_year_at_epoch_equals_saka_epoch_year():
    """the epoch date itself must map to SAKA_EPOCH_YEAR.

    prior bug: `_saka_year_for_date` returned 0 at 1979-03-29 and 48
    for 2026, contradicting SAKA_EPOCH_YEAR = 1901.
    """
    sd = saka_for_gregorian(SAKA_EPOCH_GREGORIAN)
    assert sd.saka_year == SAKA_EPOCH_YEAR, (
        f"epoch {SAKA_EPOCH_GREGORIAN.isoformat()} must yield "
        f"saka_year == SAKA_EPOCH_YEAR ({SAKA_EPOCH_YEAR}); "
        f"got {sd.saka_year}"
    )


def test_saka_year_advances_one_per_gregorian_year():
    """spot check: 2026 must NOT be saka year 48 (the prior bug).

    with SAKA_EPOCH_YEAR=1901 anchored at 1979, 2026-1979+1901 = 1948.
    """
    sd = saka_for_gregorian(_dt.date(2026, 1, 1))
    assert sd.saka_year != 48, (
        f"engine regressed to the old `gregorian_year - 1979` bug; "
        f"2026 -> {sd.saka_year}, expected 1948 (1947 for the epoch-year offset)"
    )
    # 2026 is 47 years after the 1979 epoch anchor; epoch year 1901 + 47 = 1948.
    assert sd.saka_year == 1948, (
        f"2026-01-01 should be saka_year 1948 (epoch 1979 + 47 years); "
        f"got {sd.saka_year}"
    )


def test_compose_day_omits_removed_saka_fields():
    """the four removed fields must not appear in `compose_day(...).saka`."""
    day = compose_day(_dt.date(1981, 8, 23))  # a date inside the supported range
    saka_keys = set(day.saka.keys())
    leaked = set(REMOVED_SAKA_FIELDS) & saka_keys
    assert not leaked, (
        f"removed saka fields re-appeared in compose_day output: "
        f"{sorted(leaked)}; full keys: {sorted(saka_keys)}"
    )


def test_compose_day_omits_removed_saka_fields_for_a_span_of_dates():
    """the four removed fields must not appear for any supported date."""
    start = _dt.date(1979, 3, 29)  # SAKA_EPOCH_GREGORIAN
    end = _dt.date(2027, 1, 1)
    d = start
    leaked_dates: list[tuple[str, str]] = []
    while d <= end:
        day = compose_day(d)
        for field in REMOVED_SAKA_FIELDS:
            if field in day.saka:
                leaked_dates.append((d.isoformat(), field))
        d += _dt.timedelta(days=1)
    assert not leaked_dates, (
        f"removed saka fields leaked in compose_day output: "
        f"{leaked_dates[:5]} (and {max(0, len(leaked_dates) - 5)} more)"
    )


@pytest.mark.parametrize("forbidden_id", REMOVED_RAHINAN_IDS)
def test_no_removed_rahinan_id_over_multi_year_scan(forbidden_id):
    """the engine must never emit purnama/tilem/nyepi over a 1979-2099 scan.

    these ids previously relied on `is_purnama`, `is_tilem`, and the
    unreachable nyepi predicate. they are removed because the
    underlying computations were not implemented. if anyone re-adds
    them without first implementing a real lunisolar source, this
    test catches it.
    """
    start = _dt.date(1979, 1, 1)
    end = _dt.date(2099, 12, 31)
    d = start
    first_hit: str | None = None
    hit_count = 0
    while d <= end:
        day = compose_day(d)
        for r in day.rahinan:
            if r["id"] == forbidden_id:
                hit_count += 1
                if first_hit is None:
                    first_hit = d.isoformat()
        d += _dt.timedelta(days=1)
    assert hit_count == 0, (
        f"rahinan id {forbidden_id!r} should never be emitted by the "
        f"engine (it depends on removed saka fields); first occurrence "
        f"{first_hit}, total {hit_count} occurrences in 1979-2099"
    )
