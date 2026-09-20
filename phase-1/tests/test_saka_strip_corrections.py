"""Regression tests added by the corrections follow-up to PR #15.

The merged strip PR (2a302db, head 253dd8a) fixed the saka_year bug
and removed the lunar fields, but the Codex independent review
returned request-changes (F1-F5). These tests pin the corrected
contract on top of main:

  - F1: public `saka_year` is None; the raw January-rollover value is
    exposed as `saka_year_diagnostic_january_rollover` and matches
    the helper output for the same date.
  - F2: every `compose_day` response carries `candidate_id` matching
    `rulesets.CANDIDATE_ID` alongside the frozen `ruleset` string.
  - F3: capability metadata in `RULESET_METADATA` matches the
    runtime-of-record: `named_days == len(IMPLEMENTED_RAHINAN_IDS)`,
    `purnama_counted=False`, `tilem_counted=False`,
    `nyepi_counted=False`, the unimplemented ids are listed.
  - F4: nampih metadata field is renamed to `nampih_rule_observed`
    with explicit uncited note; index-13 named `Nampih Sada`.
  - F5: the wiki generator's `RHINAN_IDS` does NOT include
    purnama/tilem/nyepi; the named-day entries no longer claim the
    engine emits those.

These tests do NOT delete or rewrite the merged `test_saka_strip.py`
regressions; they augment them.
"""

from __future__ import annotations

import datetime as _dt

import pytest

from dewatacalendar.api import compose_day
from dewatacalendar.rulesets import (
    CANDIDATE_ID,
    IMPLEMENTED_RAHINAN_IDS,
    RULESET_METADATA,
    RULESET_VERSION,
    UNIMPLEMENTED_RAHINAN_IDS,
)
from dewatacalendar.saka import (
    SAKA_EPOCH_GREGORIAN,
    SAKA_EPOCH_YEAR,
    _saka_year_for_date,
    saka_for_gregorian,
)


# --- F1: public year unavailability + diagnostic value ---


def test_f1_public_saka_year_is_none():
    """F1: the public `saka_year` field must be None for every supported date.

    The formula advances on January 1, not on a customary-attested
    boundary, so the public surface is unavailable until sign-off.
    """
    for d in (
        _dt.date(1979, 3, 29),
        _dt.date(1981, 4, 1),
        _dt.date(2024, 6, 1),
        _dt.date(2026, 1, 1),
        _dt.date(2026, 3, 18),
        _dt.date(2026, 3, 19),
        _dt.date(2026, 9, 20),
        _dt.date(2099, 12, 31),
    ):
        sd = saka_for_gregorian(d)
        assert sd.saka_year is None, (
            f"F1 violated: {d.isoformat()} public saka_year must be None, "
            f"got {sd.saka_year!r}"
        )


def test_f1_diagnostic_value_matches_helper():
    """F1: `saka_year_diagnostic_january_rollover` must equal the helper.

    The diagnostic field preserves the raw formula output for the
    harness and dispute packet. It must equal `_saka_year_for_date`
    for the same date.
    """
    for d in (
        SAKA_EPOCH_GREGORIAN,
        _dt.date(2026, 1, 1),
        _dt.date(2026, 9, 20),
    ):
        sd = saka_for_gregorian(d)
        expected = _saka_year_for_date(d)
        assert sd.saka_year_diagnostic_january_rollover == expected, (
            f"F1 violated: diagnostic for {d.isoformat()} should equal "
            f"_saka_year_for_date output {expected}; "
            f"got {sd.saka_year_diagnostic_january_rollover}"
        )
    # And the anchor: at epoch the diagnostic must be SAKA_EPOCH_YEAR.
    sd_epoch = saka_for_gregorian(SAKA_EPOCH_GREGORIAN)
    assert sd_epoch.saka_year_diagnostic_january_rollover == SAKA_EPOCH_YEAR


def test_f1_boundary_regression():
    """F1: 2026-03-18 and 2026-03-19 must both return None public saka_year.

    Codex noted that the prior PR test only smoke-tested September
    dates and hid the January-rollover boundary defect. The
    March-18/19 pair spans the customary Nyepi date (2026-03-19).
    """
    d_18 = compose_day(_dt.date(2026, 3, 18))
    d_19 = compose_day(_dt.date(2026, 3, 19))
    assert d_18.saka["saka_year"] is None
    assert d_19.saka["saka_year"] is None
    assert (
        d_18.saka["saka_year_diagnostic_january_rollover"]
        == d_19.saka["saka_year_diagnostic_january_rollover"]
    )


# --- F2: candidate identity separated from frozen ruleset ---


def test_f2_candidate_id_exposed_in_calendar_day():
    """F2: compose_day must carry the CANDIDATE_ID alongside the ruleset."""
    day = compose_day(_dt.date(2026, 9, 20))
    assert day.candidate_id == CANDIDATE_ID, (
        f"CalendarDay.candidate_id must equal rulesets.CANDIDATE_ID "
        f"({CANDIDATE_ID!r}); got {day.candidate_id!r}"
    )
    assert day.ruleset == RULESET_VERSION


def test_f2_candidate_id_differs_from_ruleset():
    """F2: the candidate_id must not silently equal the ruleset string.

    If they ever converged, the F2 separation would be lost.
    """
    assert CANDIDATE_ID != RULESET_VERSION, (
        "F2 violated: CANDIDATE_ID and RULESET_VERSION must be distinct "
        "identifiers. observable output diverges under CANDIDATE_ID but "
        "RULESET_VERSION is frozen; conflating them is the very bug F2 fixes."
    )


def test_f2_unimplemented_observances_field_present():
    """F5 (rolled into F2 acceptance): unimplemented_observances must
    always carry the three ids that depend on removed lunar fields.
    """
    day = compose_day(_dt.date(2026, 9, 20))
    assert day.unimplemented_observances == UNIMPLEMENTED_RAHINAN_IDS
    assert set(day.unimplemented_observances) == {"purnama", "tilem", "nyepi"}


def test_f2_note_explains_empty_rahinan():
    """F5: when rahinan is empty, the note must explain why."""
    day = compose_day(_dt.date(2026, 9, 20))
    assert day.rahinan == []
    assert day.note is not None
    assert "purnama" in day.note
    assert "tilem" in day.note
    assert "nyepi" in day.note


# --- F3: capability metadata matches runtime-of-record ---


def test_f3_capability_metadata_matches_runtime_of_record():
    """F3: RULESET_METADATA must reflect what the engine actually emits.

    The 210-day scan verifies the runtime count. The metadata count
    must equal it.
    """
    reachable: set[str] = set()
    start = _dt.date(2026, 1, 1)
    end = start + _dt.timedelta(days=209)  # 210-day span
    d = start
    while d <= end:
        day = compose_day(d)
        for r in day.rahinan:
            reachable.add(r["id"])
        d += _dt.timedelta(days=1)

    # Runtime reachable must equal IMPLEMENTED_RAHINAN_IDS exactly.
    assert reachable == set(IMPLEMENTED_RAHINAN_IDS), (
        f"runtime reachable ids {reachable} != "
        f"IMPLEMENTED_RAHINAN_IDS {set(IMPLEMENTED_RAHINAN_IDS)}"
    )

    # Metadata must reflect that.
    rahinan_meta = RULESET_METADATA["rahinan"]
    assert rahinan_meta["named_days"] == len(IMPLEMENTED_RAHINAN_IDS)
    assert rahinan_meta["purnama_counted"] is False
    assert rahinan_meta["tilem_counted"] is False
    assert rahinan_meta["nyepi_counted"] is False
    assert set(rahinan_meta["implemented_rahinan_ids"]) == set(IMPLEMENTED_RAHINAN_IDS)
    assert set(rahinan_meta["unimplemented_rahinan_ids"]) == set(UNIMPLEMENTED_RAHINAN_IDS)


def test_f3_public_saka_year_returned_false_in_metadata():
    """F1+F3: the metadata must declare that the public year is unavailable."""
    saka_meta = RULESET_METADATA["saka"]
    assert saka_meta["public_saka_year_returned"] is False
    assert saka_meta["saka_year_diagnostic_field"] == "saka_year_diagnostic_january_rollover"


# --- F4: nampih rule described as observed behaviour ---


def test_f4_nampih_rule_observed_with_sada_name():
    """F4: nampih metadata field is named `nampih_rule_observed` and
    names index 13 'Nampih Sada'. The prior `nampih_rule_actual`
    field must be gone.
    """
    saka_meta = RULESET_METADATA["saka"]
    assert "nampih_rule_actual" not in saka_meta, (
        "F4 violated: `nampih_rule_actual` field was removed because it "
        "falsely endorsed the loop's mod-3 rule as the cultural convention."
    )
    assert "nampih_rule_observed" in saka_meta
    assert "Nampih Sada" in saka_meta["nampih_rule_observed"]
    assert "uncited" in saka_meta["nampih_rule_observed"]
    assert saka_meta["nampih_observed_sasih_index"] == 13
    assert saka_meta["nampih_observed_sasih_name"] == "Nampih Sada"
    # The declared rule (Tilem Kapitu predicate) is still tracked.
    assert saka_meta["nampih_rule_declared"] == (
        "prevent Tilem Kapitu from falling in gregorian December"
    )
    assert saka_meta["nampih_declared_rule_implemented"] is False
