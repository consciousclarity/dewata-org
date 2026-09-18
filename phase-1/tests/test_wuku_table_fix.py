"""wuku-table-fix tests — pinned to babadbali.com/pewarigaan/wuku.htm via METADATA.json.

Per governance decision 2026-09-19, babadbali.com is the governing source
for wuku spelling. The page itself is NOT vendored in the repository (see
the METADATA.json redistribution_decision for the rationale and the
Kemendikbud precedent at STATUS.json:178). What IS vendored is the 30
Nama Bali link-text strings, recorded verbatim in
phase-1/evidence/references/babadbali-com-wuku/METADATA.json under
sample_data.nama_bali_link_text_extracted.

This test asserts the engine's WUKU_NAMES_BALINESE equals those 30 strings
in position order. No HTML parsing, no file outside the repository.

The page-level SHA-256 and byte count are recorded in METADATA.json for
future re-fetch verification but are NOT asserted here — the test is
about the engine matching the canonical spelling, not about the engine
re-reading the source page. A future re-fetch that produces the same 30
strings (even with a different SHA-256) would still satisfy this test.

Saraswati triggers at pawukon.wuku_idx == 30 (Watugunung) + Saniscara per
canonical babadbali ordering. Galungan triggers at wuku_idx == 11
(Dungulan) + Buda + Keliwon.

Tests in this file are fail-closed: METADATA.json is part of the
repository, so its absence is a real failure of the test setup, not a
reason to pass quietly. Same fail-closed principle as test_wariga_evidence.py.
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dewatacalendar.pawukon import (  # noqa: E402
    WUKU_NAMES_BALINESE,
)
from dewatacalendar.api import compose_day  # noqa: E402


BABADBALI_METADATA = ROOT / "evidence" / "references" / "babadbali-com-wuku" / "METADATA.json"


def _load_babadbali_nama_bali() -> list[str]:
    """Read METADATA.json and return the 30 Nama Bali link-text strings in
    document order. The strings are vendored in METADATA.json; the source
    HTML is not.
    """
    assert BABADBALI_METADATA.exists(), (
        f"babadbali METADATA.json missing at {BABADBALI_METADATA}. "
        "The 30 Nama Bali strings are the minimum evidence the engine fix "
        "relies on; this file must be committed to the repository."
    )
    metadata = json.loads(BABADBALI_METADATA.read_text())
    assert "source" in metadata, (
        f"METADATA.json at {BABADBALI_METADATA} is missing the 'source' key."
    )
    assert "redistribution_status" in metadata["source"], (
        f"METADATA.json at {BABADBALI_METADATA} is missing "
        f"'source.redistribution_status'."
    )
    assert metadata["source"]["redistribution_status"] == "NOT_VENDORED", (
        f"METADATA.json at {BABADBALI_METADATA} has redistribution_status "
        f"= {metadata['source']['redistribution_status']!r}, expected "
        f"'NOT_VENDORED'. The page itself must not be vendored in this "
        f"repository; only the extracted strings may be."
    )
    babadbali = metadata["sample_data"]["nama_bali_link_text_extracted"]
    assert len(babadbali) == 30, (
        f"METADATA.json sample_data.nama_bali_link_text_extracted has "
        f"{len(babadbali)} entries, expected 30."
    )
    return babadbali


def test_engine_wuku_names_match_babadbali() -> None:
    """WUKU_NAMES_BALINESE must equal the babadbali Nama Bali link-text column
    recorded in METADATA.json, in position order."""
    babadbali = _load_babadbali_nama_bali()
    assert len(WUKU_NAMES_BALINESE) == 30, (
        f"engine WUKU_NAMES_BALINESE has {len(WUKU_NAMES_BALINESE)} names, expected 30"
    )
    mismatches = [
        (i + 1, b, e)
        for i, (b, e) in enumerate(zip(babadbali, WUKU_NAMES_BALINESE))
        if b != e
    ]
    assert not mismatches, (
        "engine does not match babadbali canonical ordering at these positions:\n  "
        + "\n  ".join(f"pos {i}: babadbali={b!r}  engine={e!r}" for i, b, e in mismatches)
    )


def test_saraswati_fires_at_cycle_position_210() -> None:
    """Saraswati triggers at the LAST day of the cycle (position 210), which is
    Wuku Watugunung day 7 (wuku_idx == 30) + Saniscara. epoch + 210 days = position 1
    of next cycle; epoch + 209 days = position 210 of the FIRST cycle.
    """
    epoch = _dt.date(1981, 8, 23)
    saraswati_dates: list[tuple[str, int, int, str]] = []
    for offset in range(0, 365 * 30):
        d = epoch + _dt.timedelta(days=offset)
        cd = compose_day(d)
        if any(r["id"] == "saraswati" for r in cd.rahinan):
            saraswati_dates.append(
                (d.isoformat(), cd.pawukon["position_in_cycle"], cd.pawukon["wuku_idx"],
                 cd.wewaran["saptawara_name"])
            )
            if len(saraswati_dates) >= 5:
                break
    assert saraswati_dates, "saraswati never fires in 30 years after epoch — predicate is broken"
    for dstr, pos, widx, sapt in saraswati_dates:
        assert pos == 210, f"{dstr}: position {pos}, expected 210"
        assert widx == 30, f"{dstr}: wuku_idx {widx}, expected 30"
        assert sapt == "Saniscara", f"{dstr}: saptawara {sapt!r}, expected 'Saniscara'"


def test_galungan_fires_at_buda_keliwon_in_dungulan() -> None:
    """Galungan triggers at Wuku Dungulan (wuku_idx 11) + Buda + Keliwon."""
    epoch = _dt.date(1981, 8, 23)
    galungan_dates: list[tuple[str, int, str, str]] = []
    for offset in range(0, 365 * 30):
        d = epoch + _dt.timedelta(days=offset)
        cd = compose_day(d)
        if any(r["id"] == "galungan" for r in cd.rahinan):
            galungan_dates.append(
                (d.isoformat(), cd.pawukon["wuku_idx"], cd.wewaran["saptawara_name"],
                 cd.wewaran["pancawara_name"])
            )
            if len(galungan_dates) >= 5:
                break
    assert galungan_dates, "galungan never fires in 30 years after epoch — predicate is broken"
    for dstr, widx, sapt, panc in galungan_dates:
        assert widx == 11, f"{dstr}: wuku_idx {widx}, expected 11 (Dungulan)"
        assert sapt == "Buda", f"{dstr}: saptawara {sapt!r}, expected 'Buda'"
        assert panc == "Keliwon", f"{dstr}: pancawara {panc!r}, expected 'Keliwon'"
