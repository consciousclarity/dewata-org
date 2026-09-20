"""verify the two-axis analysis counts and dispute reclassifications.

This test loads the two-axis analysis evidence artifacts and asserts:
- exact 210-day field match/disagreement counts (RAW and NORMALIZED)
- exact phase offset (constant +84)
- Wuku differs raw (constant 12 wuku = 84 days)
- independent references match DEW/CAL saptawara on all 7 dates
- independent references match CAL wuku on all 7 dates
- DEW wuku is exactly 84 days off from independent references
- all 6 pawukon/wewaran disputes have reclassification records
- the epoch dispute has the narrative_update record
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

EV_DIR = ROOT / "evidence" / "references" / "reingold-dershowitz-2018-pawukon" / "firstparty-EdReingold-calendar-code2"
RAW_CAL = EV_DIR / "cycle-comparison/raw-cal-210.csv"
RAW_DEW = EV_DIR / "cycle-comparison/raw-dewata-210.csv"
INDEP = EV_DIR / "cycle-comparison/independent-references.csv"
BASA = EV_DIR / "cycle-comparison/basaibubali-formulas.json"

DISPUTES = ROOT / "docs" / "runbook" / "disputes.json"


def _read_pipe(path: Path):
    """read a pipe-delimited CSV with optional `#`-prefixed comment lines.

    the column header is the first non-comment line; everything after that
    is a data row. blank lines are skipped. see phase-1/evidence/MANIFEST.md
    for the `# git_commit:` provenance header convention.
    """
    rows = []
    saw_header = False
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith("#"):
                continue
            if not saw_header:
                saw_header = True
                continue
            rows.append(line.split("|"))
    return rows


@pytest.fixture(scope="module")
def raw_cal():
    return _read_pipe(RAW_CAL)


@pytest.fixture(scope="module")
def raw_dew():
    return _read_pipe(RAW_DEW)


# ========================================================================
# RAW 210-day field counts
# ========================================================================

EXPECTED_RAW_COUNTS = {
    "cycle_position": (0, 210),
    "Pancawara":      (210, 0),
    "Saptawara":      (210, 0),
    "Triwara":        (210, 0),
    "Sadwara":        (210, 0),
    "Caturwara":      (12, 198),
    "Asatawara":      (12, 198),
    "Sangawara":      (125, 85),
    "Dasawara":       (12, 198),
    "Dwiwara":        (126, 84),
}


def _normalize_dwi(cal_val):
    return "Menga" if int(cal_val) == 1 else "Pepet"


def test_raw_cycle_length_210(raw_cal, raw_dew):
    assert len(raw_cal) == 210
    assert len(raw_dew) == 210


def test_raw_phase_offset_constant_84(raw_cal, raw_dew):
    """every row must show CAL_pos - DEW_pos = +84 (mod 210)."""
    for c, d in zip(raw_cal, raw_dew):
        cal_pos = int(c[3])
        dew_pos = int(d[2])
        assert (cal_pos - dew_pos) % 210 == 84, (
            f"idx={c[0]}: CAL_pos={cal_pos}, DEW_pos={dew_pos}, offset should be 84 mod 210"
        )


def test_raw_wuku_differs_consistently(raw_cal, raw_dew):
    """Wuku (derived from cycle position) must differ consistently by 12 wuku (84 days)
    between CAL and DEW for every row."""
    for c, d in zip(raw_cal, raw_dew):
        cal_pos = int(c[3])
        dew_pos = int(d[2])
        cal_wku = ((cal_pos - 1) // 7) + 1
        dew_wku = int(d[3])
        # 84-day offset = 12 wuku shift (84 / 7 = 12)
        assert (cal_wku - dew_wku) % 30 == 12, (
            f"idx={c[0]}: CAL wku={cal_wku}, DEW wku={dew_wku}, expected shift of 12 wuku"
        )


@pytest.mark.parametrize("field_name,expected", [
    (n, c) for n, c in EXPECTED_RAW_COUNTS.items()
])
def test_raw_field_counts(raw_cal, raw_dew, field_name, expected):
    expected_matches, expected_disagree = expected
    field_to_cols = {
        "cycle_position": (3, 2, "int"),
        "Pancawara":      (4, 5, "int"),
        "Saptawara":      (5, 6, "int"),
        "Triwara":        (6, 7, "int"),
        "Sadwara":        (7, 8, "int"),
        "Caturwara":      (8, 9, "int"),
        "Asatawara":      (9, 10, "int"),
        "Sangawara":      (10, 11, "int"),
        "Dasawara":       (11, 12, "int"),
        "Dwiwara":        (12, 13, "dwi"),
    }
    cal_col, dew_col, kind = field_to_cols[field_name]

    matches = 0
    disagree = 0
    for c, d in zip(raw_cal, raw_dew):
        if kind == "dwi":
            cal_v = _normalize_dwi(c[cal_col])
            dew_v = d[dew_col]
        else:
            cal_v = int(c[cal_col])
            dew_v = int(d[dew_col])
        if cal_v == dew_v:
            matches += 1
        else:
            disagree += 1

    assert (matches, disagree) == (expected_matches, expected_disagree), (
        f"{field_name}: expected ({expected_matches}, {expected_disagree}) got ({matches}, {disagree})"
    )


# ========================================================================
# NORMALIZED 210-day field counts (after -84 shift on CAL position)
# ========================================================================

EXPECTED_NORMALIZED_COUNTS = {
    "cycle_position": (210, 0),
    "Pancawara":      (210, 0),
    "Saptawara":      (210, 0),
    "Triwara":        (210, 0),
    "Sadwara":        (210, 0),
    "Caturwara":      (12, 198),
    "Asatawara":      (12, 198),
    "Sangawara":      (125, 85),
    "Dasawara":       (12, 198),
    "Dwiwara":        (126, 84),
}


def _shift_cal_pos(pos):
    p = int(pos) - 84
    if p <= 0:
        p += 210
    return p


@pytest.mark.parametrize("field_name,expected", [
    (n, c) for n, c in EXPECTED_NORMALIZED_COUNTS.items()
])
def test_normalized_field_counts(raw_cal, raw_dew, field_name, expected):
    expected_matches, expected_disagree = expected
    field_to_cols_normalized = {
        "cycle_position": ("shifted", 2, "int"),
        "Pancawara":      (4, 5, "int"),
        "Saptawara":      (5, 6, "int"),
        "Triwara":        (6, 7, "int"),
        "Sadwara":        (7, 8, "int"),
        "Caturwara":      (8, 9, "int"),
        "Asatawara":      (9, 10, "int"),
        "Sangawara":      (10, 11, "int"),
        "Dasawara":       (11, 12, "int"),
        "Dwiwara":        (12, 13, "dwi"),
    }
    cal_col, dew_col, kind = field_to_cols_normalized[field_name]

    matches = 0
    disagree = 0
    for c, d in zip(raw_cal, raw_dew):
        if cal_col == "shifted":
            cal_v = _shift_cal_pos(c[3])
            dew_v = int(d[dew_col])
        elif kind == "dwi":
            cal_v = _normalize_dwi(c[cal_col])
            dew_v = d[dew_col]
        else:
            cal_v = int(c[cal_col])
            dew_v = int(d[dew_col])
        if cal_v == dew_v:
            matches += 1
        else:
            disagree += 1

    assert (matches, disagree) == (expected_matches, expected_disagree), (
        f"{field_name} (normalized): expected ({expected_matches}, {expected_disagree}) got ({matches}, {disagree})"
    )


# ========================================================================
# Independent references
# ========================================================================

def test_independent_references_present():
    assert INDEP.exists()
    text = INDEP.read_text()
    # all 7 reference dates must be present
    for date_str in ["2026-09-01", "2026-09-05", "2026-09-09", "2026-09-15",
                     "2026-09-17", "2026-09-26", "2026-09-30"]:
        assert date_str in text


def test_independent_references_saptawara_match_both_engines():
    """all 7 independent references must match DEW and CAL on saptawara."""
    with open(INDEP) as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            assert row["DEW_match_sapt"] == "OK", (
                f"DEW sapt mismatch on {row['date']}: {row['DEW_sapt']} vs ref {row['reference_sapt']}"
            )
            assert row["CAL_match_sapt"] == "OK", (
                f"CAL sapt mismatch on {row['date']}: {row['CAL_sapt']} vs ref {row['reference_sapt']}"
            )


def test_independent_references_wuku_match_cal_only():
    """all 7 independent references must match CAL wuku exactly."""
    with open(INDEP) as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            assert row["CAL_match_wku"] == "OK", (
                f"CAL wku mismatch on {row['date']}: CAL={row['CAL_wku']} vs ref {row['reference_wuku']}"
            )
            # DEW wuku should be exactly 84 days = 12 wuku off
            assert row["DEW_match_wku"] == "NO", (
                f"DEW wku unexpectedly matched on {row['date']}: {row['DEW_wku']} vs ref {row['reference_wuku']}"
            )


def test_independent_references_pancawara_disagrees_with_both_engines():
    """all 7 independent references must show pancawara disagreement with both engines."""
    with open(INDEP) as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            assert row["DEW_match_panc"] == "NO", (
                f"DEW panc unexpectedly matched on {row['date']}"
            )
            assert row["CAL_match_panc"] == "NO", (
                f"CAL panc unexpectedly matched on {row['date']}"
            )


# ========================================================================
# BASAbali formulas
# ========================================================================

def test_basaibubali_formulas_recorded():
    assert BASA.exists()
    data = json.loads(BASA.read_text())
    assert data["source"] == "basaibubali.org"
    assert "Caturwara" in data["formulas"]
    assert "Sangawara" in data["formulas"]
    assert "Dasawara" in data["formulas"]
    assert "Dwiwara" in data["formulas"]


def test_basaibubali_caturwara_simple_modular():
    data = json.loads(BASA.read_text())
    caturwara = data["formulas"]["Caturwara"]
    assert "(uku" in caturwara["formula"] or "bilangan uku" in caturwara["formula"]
    assert caturwara["type"] == "simple_modular_arithmetic"


# ========================================================================
# Dispute reclassifications
# ========================================================================

@pytest.fixture(scope="module")
def disputes():
    return json.loads(DISPUTES.read_text())


def test_epoch_dispute_reclassified_to_mapping_phase(disputes):
    d = next(x for x in disputes if x.get("id") == "DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15")
    assert "reclassification" in d
    assert d["reclassification"]["new_class"] == "mapping_phase"
    assert d["reclassification"]["previous_class"] == "calendar_semantics"


def test_epoch_dispute_narrative_update_present(disputes):
    d = next(x for x in disputes if x.get("id") == "DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15")
    assert "narrative_update" in d
    assert "computational origin" in d["narrative_update"]["new_framing"]
    assert "historical/cultural epoch" in d["narrative_update"]["new_framing"]


@pytest.mark.parametrize("dispute_id,expected_class", [
    ("DISPUTE-wewaran-asatawara-special-case-formula-2026-09-15", "formula_semantics"),
    ("DISPUTE-wewaran-caturwara-transitive-dependency-on-asatawara-2026-09-15", "formula_semantics"),
    ("DISPUTE-wewaran-sangawara-special-case-formula-2026-09-15", "formula_semantics"),
    ("DISPUTE-wewaran-dasawara-urip-5-table-2026-09-15", "formula_semantics"),
    ("DISPUTE-wewaran-dwiwara-parity-basis-2026-09-15", "indexing_representation"),
])
def test_wewaran_disputes_reclassified(disputes, dispute_id, expected_class):
    d = next(x for x in disputes if x.get("id") == dispute_id)
    assert "reclassification" in d
    assert d["reclassification"]["new_class"] == expected_class
