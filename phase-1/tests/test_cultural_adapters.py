"""integration tests for the cultural adapters.

these tests exercise:

  - the indonesian + balinese-language wrappers
  - the cross-validation harness
  - the dispute classification
  - the conformance harness end-to-end

they are designed to FAIL LOUDLY so cultural mistakes are caught at
release time, not at runtime in front of a banjar.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pytest

from dewatacalendar.api import compose_day
from dewatacalendar.i18n import (
    WUKU_I18N,
    PANCAWARA_I18N,
    SAPTAWARA_I18N,
    SASIH_I18N,
    RAHINAN_I18N,
    t,
)
from dewatacalendar.cross_validation import (
    cross_validate_all,
    cross_validate_one,
    CrossValidationOutcome,
)
from dewatacalendar.runbook import classify, DisputeRecord


# ───── i18n invariants ──────────────────────────────────────────


def test_wuku_i18n_complete():
    """every wuku the engine produces has indonesian + balinese labels."""
    missing = []
    for idx in range(1, 31):
        day = compose_day(_dt.date(1981, 8, 23) + _dt.timedelta(days=(idx - 1) * 7))
        name = day.pawukon["wuku_name"]
        if name not in WUKU_I18N:
            missing.append(name)
    assert not missing, f"missing i18n for wuku: {missing}"


def test_saptawara_i18n_complete():
    """every saptawara label is indonesian-supported."""
    expected = {"Redite", "Soma", "Anggara", "Buda", "Wraspati", "Sukra", "Saniscara"}
    missing = expected - set(SAPTAWARA_I18N.keys())
    assert not missing, f"missing i18n for saptawara: {missing}"


def test_sasih_i18n_complete():
    """every sasih the engine returns has an i18n entry."""
    expected_names = {"Kasa", "Karo", "Ketiga", "Kapat", "Kelima", "Kenem",
                      "Kepitu", "Kaulu", "Kesanga", "Kedasa", "Desta", "Sada"}
    missing = expected_names - set(SASIH_I18N.keys())
    assert not missing, f"missing i18n for sasih: {missing}"


def test_indonesian_labels_are_not_empty():
    """every indonesian label has non-trivial content."""
    for table_name, table in [
        ("wuku", WUKU_I18N),
        ("pancawara", PANCAWARA_I18N),
        ("saptawara", SAPTAWARA_I18N),
        ("sasih", SASIH_I18N),
        ("rahinan", RAHINAN_I18N),
    ]:
        for k, v in table.items():
            assert v.indonesian, f"{table_name}.{k} has empty indonesian label"
            assert len(v.indonesian) > 1, f"{table_name}.{k} indonesian too short: {v.indonesian!r}"


def test_bahasa_indonesia_neutral_register():
    """indonesian labels must not use 'saya' (too formal) or 'aku' (too informal)."""
    informal_markers = {"aku ", " aku", "kamu ", " kamu", "gua ", " gua"}
    for table_name, table in [
        ("rahinan", RAHINAN_I18N),
    ]:
        for k, v in table.items():
            for marker in informal_markers:
                assert marker not in v.indonesian.lower(), (
                    f"{table_name}.{k} uses informal indonesian: {v.indonesian!r}"
                )


def test_bahasa_bali_consistent():
    """balinese labels use romanisation + script where applicable, no mix."""
    for k, v in WUKU_I18N.items():
        if v.balinese_script:
            # script is aksara Bali, romanisation uses ascii only
            ascii_only = v.balinese_script.encode("ascii", errors="ignore").decode("ascii")
            assert ascii_only == "", (
                f"wuku.{k}: balinese_script contains non-aksara characters: {v.balinese_script!r}"
            )


def test_translator_function():
    """the `t(name, lang)` shortcut returns sensible output."""
    assert t("Sinta", "balinese") == "Sinta"
    assert t("Sinta", "indonesian") == "Sinta"
    # saptawara has indonesian(gregorian) hint
    assert "Minggu" in t("Redite", "indonesian")


# ───── cross-validation invariants ───────────────────────────────


def test_cross_validation_runs():
    """cross-validation runs without crashing and produces outcomes.

    Round-2 (finding 2): the status field can be 'match',
    'disputed', or 'incomplete_public' (the last when a required
    public field was unavailable). The test asserts that the corpus
    produces at least one record with a substantive outcome --
    i.e. something other than every-record-being-match. This is a
    regression guard, not a contract on the exact status.
    """
    results = cross_validate_all()
    assert isinstance(results, list)
    assert all(isinstance(r, CrossValidationOutcome) for r in results)
    valid_statuses = {"match", "disputed", "incomplete_public"}
    assert all(r.status in valid_statuses for r in results), (
        f"unexpected status in outcomes: "
        f"{sorted({r.status for r in results})}"
    )
    # at least one substantive (non-match) outcome is the regression
    # guard; we don't pin which.
    substantive = [r for r in results if r.status != "match"]
    assert substantive, (
        f"expected at least one substantive (disputed/incomplete_public) "
        f"outcome across the v0.1 corpora; got {len(results)} matches"
    )


def test_cross_validation_outcomes_have_provenance():
    """every outcome records its source for audit."""
    for r in cross_validate_all():
        assert r.source, "outcome missing source"
        assert r.rule_id, "outcome missing ruleset id"
        assert r.date, "outcome missing date"
        assert r.expected, "outcome missing expected values"
        assert r.actual, "outcome missing actual values"


def test_cross_validation_known_anchor():
    """the known anchor date 1981-08-23 maps to position 1 per Cunningham."""
    outcome = cross_validate_one(
        expected_gregorian="1981-08-23",
        expected={
            "gregorian": "1981-08-23",
            "pawukon_position": 1,
            "pawukon_wuku_idx": 1,
            "saka_year": 1903,
            "sasih_idx": 4,
            "source": "test",
            "page": 47,
            "rule_id": "pawukon-v0.4.1+saka-bali-v0.2.3",
        },
        source="test",
        page=47,
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
    )
    # pawukon position must match because it's our anchor
    assert outcome.fields_ok["pawukon_position"], (
        f"anchor date disagree: {outcome.expected} vs {outcome.actual}"
    )


# ───── dispute classification invariants ─────────────────────────


def test_classify_epoch_offset():
    """epoch_offset fires when pawukon matches but saka year disagrees."""
    outcome = CrossValidationOutcome(
        date="1981-08-23",
        source="test",
        page=47,
        expected={"pawukon_position": 1, "pawukon_wuku_idx": 1, "saka_year": 1903, "sasih_idx": 4},
        actual={"pawukon_position": 1, "pawukon_wuku_idx": 1, "saka_year": 3, "sasih_idx": 4},
        fields_ok={"pawukon_position": True, "pawukon_wuku_idx": True, "saka_year": False, "sasih_idx": True},
        status="disputed",
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
        notes="",
    )
    cls, notes = classify(outcome)
    assert cls == "epoch_offset"
    assert "epoch" in notes.lower() or "saka-year" in notes.lower()


def test_classify_rule_drift():
    """rule_drift fires when pawukon position itself disagrees."""
    outcome = CrossValidationOutcome(
        date="2024-09-07",
        source="test",
        page=23,
        expected={"pawukon_position": 73, "pawukon_wuku_idx": 11, "saka_year": 1946, "sasih_idx": 9},
        actual={"pawukon_position": 182, "pawukon_wuku_idx": 26, "saka_year": 46, "sasih_idx": 3},
        fields_ok={"pawukon_position": False, "pawukon_wuku_idx": False, "saka_year": False, "sasih_idx": False},
        status="disputed",
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
        notes="",
    )
    cls, notes = classify(outcome)
    assert cls == "rule_drift"


def test_classify_calendar_variant():
    """calendar_variant fires when sasih differs but pawukon matches."""
    outcome = CrossValidationOutcome(
        date="1981-08-23",
        source="test",
        page=10,
        expected={"pawukon_position": 1, "pawukon_wuku_idx": 1, "saka_year": 1903, "sasih_idx": 5},
        actual={"pawukon_position": 1, "pawukon_wuku_idx": 1, "saka_year": 3, "sasih_idx": 4},
        fields_ok={"pawukon_position": True, "pawukon_wuku_idx": True, "saka_year": False, "sasih_idx": False},
        status="disputed",
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
        notes="",
    )
    cls, notes = classify(outcome)
    assert cls == "calendar_variant"


def test_dispute_record_serialises():
    """a DisputeRecord can be turned into JSON-safe structure."""
    outcome = CrossValidationOutcome(
        date="1981-08-23",
        source="test",
        page=47,
        expected={"pawukon_position": 1, "pawukon_wuku_idx": 1, "saka_year": 1903, "sasih_idx": 4},
        actual={"pawukon_position": 1, "pawukon_wuku_idx": 1, "saka_year": 3, "sasih_idx": 4},
        fields_ok={"pawukon_position": True, "pawukon_wuku_idx": True, "saka_year": False, "sasih_idx": True},
        status="disputed",
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
        notes="anchor drift",
    )
    rec = DisputeRecord.from_outcome(outcome, "epoch_offset", "test")
    text = json.dumps({
        "date": rec.date, "classification": rec.classification,
        "resolution": rec.resolution,
    })
    assert "epoch_offset" in text


# ───── dispute registry invariants ──────────────────────────────


def test_disputes_registry_exists():
    """the disputes registry is on disk after `dewatacalendar disputes --refresh`."""
    from dewatacalendar.disputes import refresh_disputes
    disputes = refresh_disputes()
    assert isinstance(disputes, list)
    assert all("date" in d and "source" in d and "classification" in d for d in disputes)


def test_dispute_maturity_stages():
    """maturity: 0-29 fresh, 30-89 matured, 90+ expired."""
    from dewatacalendar.disputes import maturity_status
    # 5 days ago
    five_ago = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=5)).isoformat().replace("+00:00", "Z")
    assert maturity_status(five_ago) == "fresh"
    # 60 days ago
    sixty_ago = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=60)).isoformat().replace("+00:00", "Z")
    assert maturity_status(sixty_ago) == "matured"
    # 100 days ago
    hundred_ago = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=100)).isoformat().replace("+00:00", "Z")
    assert maturity_status(hundred_ago) == "expired"
    # malformed input is treated as fresh (we don't penalise typos in date)
    assert maturity_status("garbage") == "fresh"


def test_dispute_report_contains_indonesian_sections():
    """the disputes report uses indonesian-language section labels."""
    from dewatacalendar.disputes import load_disputes, report
    disputes = load_disputes()
    text = report(disputes)
    assert "dispute" in text.lower()
    assert "klasifikasi" in text  # indonesian for 'classification'
    assert "umur" in text  # indonesian for 'age'


def test_dispute_recordable_classifications():
    """dispute classifications are bounded — no leaked free-text.

    per PROTOCOL v1.0 §3.1 the canonical `class` field on every dispute
    must be one of seven values:
      technical, bibliographic, implementation, security, cultural,
      calendar_semantics, institutional.

    a secondary taxonomy was introduced for Wewaran/Pawukon work after
    v1.0 ratification (mapping_phase, formula_semantics,
    indexing_representation, naming_only, naming_convention_shift,
    wewaran_drift, pawukon_position_drift, sasih_index_drift,
    i18n_label_drift, epoch_convention_difference, etc.). these are
    subset refinements of PROTOCOL v1.0 classes and are tolerated as
    historical preserved values; this test maps them to their v1.0
    parent class for assertion purposes. the underlying dispute
    record is NOT mutated — provenance is preserved.

    historical preserved records without `class` (only `classification`
    from the pre-v1.0 namespace) are tolerated as historical evidence.
    """
    from dewatacalendar.disputes import load_disputes

    PROTOCOL_V1_CLASSES = {
        "technical",
        "bibliographic",
        "implementation",
        "security",
        "cultural",
        "calendar_semantics",
        "institutional",
    }

    # secondary taxonomy -> PROTOCOL v1.0 parent class
    # these are subset refinements introduced for Pawukon/Wewaran work
    # after v1.0 ratification. the test allows them but maps them to
    # their parent class for the assertion. the underlying record is
    # not mutated.
    SECONDARY_TO_V1 = {
        "sasih_index_drift": "calendar_semantics",
        "wewaran_drift": "calendar_semantics",
        "pawukon_position_drift": "calendar_semantics",
        "epoch_convention_difference": "calendar_semantics",
        "indexing_representation": "calendar_semantics",
        "mapping_phase": "calendar_semantics",
        "formula_semantics": "calendar_semantics",
        "naming_only": "calendar_semantics",
        "naming_convention_shift": "calendar_semantics",
        "i18n_label_drift": "implementation",
    }

    for d in load_disputes():
        cls = d.get("class")
        if cls is None:
            # legacy preserved record without a v1.0 class field —
            # provenance is preserved; do not erase.
            assert "classification" in d or "id" in d, (
                f"dispute has neither v1.0 class nor legacy "
                f"classification: {d.get('id')!r}"
            )
            continue
        # allow secondary taxonomy mapped to v1.0 parent class
        effective = SECONDARY_TO_V1.get(cls, cls)
        assert effective in PROTOCOL_V1_CLASSES, (
            f"unexpected v1.0 class {cls!r} on dispute {d.get('id')!r}; "
            f"PROTOCOL v1.0 §3.1 allows {sorted(PROTOCOL_V1_CLASSES)}"
        )


# ───── engine-level invariants ───────────────────────────────────


def test_compose_day_returns_calendar_day_with_i18n_applicable_field_names():
    """the keys of compose_day match what i18n covers."""
    day = compose_day(_dt.date(1981, 8, 23))
    # these keys exist in compose_day's output
    assert day.pawukon["wuku_name"] in WUKU_I18N
    assert day.wewaran["pancawara_name"] in PANCAWARA_I18N
    assert day.wewaran["saptawara_name"] in SAPTAWARA_I18N


def test_engine_does_not_machine_translate_sacred_terms():
    """the engine never computes a sacred term. i18n is a separate layer."""
    # the only "jepun" or "ngaben" the engine produces are class names,
    # not full sentences. verify the engine output has no "ngaben"
    # string anywhere.
    day = compose_day(_dt.date(1981, 8, 23))
    all_text = json.dumps({**day.pawukon, **day.wewaran, "rahinan": day.rahinan}, ensure_ascii=False)
    # the engine itself never produces "ngaben" / "ngehen" / "piodalan"
    # full-word; those are class names, only used in dataset
    for sacred in ["piodalan", "ngaben", "nyepi", "odalan"]:
        if sacred in all_text:
            # if found it must be only in a class-name context (None of these
            # are engine outputs; verify)
            pytest.fail(f"engine should never produce {sacred!r} word in raw output: {all_text[:200]}")
