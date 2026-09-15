"""verify the 210-day cycle comparison counts between Dewata and first-party CALENDRICA.

this test loads the cycle-comparison CSVs from the evidence package and asserts
the exact match/disagreement counts recorded in dewata-vs-firstparty-calendrica-comparison.md.

the user explicitly required:
> Do not use wording such as "always" or "mostly" without exact counts.
> For every comparable field report exact counts: matches / 210, disagreements / 210.

this test makes those counts machine-checkable.
"""

from __future__ import annotations

from pathlib import Path

import pytest


EV_DIR = Path("/opt/dw-phase2/phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2")
FP_CSV = EV_DIR / "cycle-comparison/firstparty-cycle-210.csv"
DEW_CSV = EV_DIR / "cycle-comparison/dewata-cycle-210.csv"


def _read_pipe(path: Path):
    rows = []
    with open(path) as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n")
            if not line:
                continue
            if i == 0:  # header
                continue
            rows.append(line.split("|"))
    return rows


# fields and their column indices in each file
# CAL: 0=POS, 1=shifted, 2=luang, 3=dwi, 4=tri, 5=cat, 6=pan, 7=sad, 8=sap, 9=ast, 10=sng, 11=das
# DEW: 0=POS, 1=dewata_pos, 2=luang_proxy, 3=dwi_name, 4=tri, 5=cat, 6=pan, 7=sad, 8=sap, 9=ast, 10=sng, 11=das
FIELDS = [
    # (name, cal_col, dew_col, converter)
    ("Triwara",   4,  4,  int),
    ("Caturwara", 5,  5,  int),
    ("Pancawara", 6,  6,  int),
    ("Sadwara",   7,  7,  int),
    ("Saptawara", 8,  8,  int),
    ("Astawara",  9,  9,  int),
    ("Sangawara", 10, 10, int),
    ("Dasawara",  11, 11, int),
    ("Dwiwara",   3,  3,  "dwi"),  # special: Menga/Pepet conversion
]

# Exact counts from the recorded evidence package
EXPECTED_COUNTS = {
    "Triwara":   (210, 0),
    "Caturwara": (12,  198),
    "Pancawara": (210, 0),
    "Sadwara":   (210, 0),
    "Saptawara": (210, 0),
    "Astawara":  (12,  198),
    "Sangawara": (125, 85),
    "Dasawara":  (12,  198),
    "Dwiwara":   (126, 84),
}


def _normalize_dwi(cal_val):
    return "Menga" if int(cal_val) == 1 else "Pepet"


@pytest.fixture(scope="module")
def cycle_data():
    return _read_pipe(FP_CSV), _read_pipe(DEW_CSV)


def test_cycle_length_210(cycle_data):
    fp, dew = cycle_data
    assert len(fp) == 210
    assert len(dew) == 210


def test_cycle_position_match_count(cycle_data):
    fp, dew = cycle_data
    matches = sum(1 for c, d in zip(fp, dew) if int(c[1]) == int(d[1]))
    assert matches == 210, f"expected 210 cycle-position matches, got {matches}"


@pytest.mark.parametrize("field_name,expected_matches,expected_disagree", [
    (name, m, d) for name, (m, d) in EXPECTED_COUNTS.items()
])
def test_field_match_counts(cycle_data, field_name, expected_matches, expected_disagree):
    fp, dew = cycle_data
    field = next(f for f in FIELDS if f[0] == field_name)
    fname, cal_col, dew_col, conv = field

    matches = 0
    disagree = 0
    for c, d in zip(fp, dew):
        if conv == "dwi":
            cal_v = _normalize_dwi(c[cal_col])
            dew_v = d[dew_col]  # already "Menga"/"Pepet"
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


def test_modern_dates_comparison_recorded():
    """the modern-dates-comparison.md must exist and report counts."""
    path = EV_DIR / "cycle-comparison/modern-dates-comparison.md"
    assert path.exists()
    text = path.read_text()
    # should contain key counts (per the comparison)
    assert "cycle pos matches: 11/11" in text
    # should contain disagreement counts
    assert "Caturwara:" in text
    assert "0/11" in text  # caturwara disagree count for modern dates
