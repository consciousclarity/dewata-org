"""verify the adapter audit and corrected 7-date comparison."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


PHASE_ROOT = Path(__file__).resolve().parents[1]
EV_DIR = PHASE_ROOT / "evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2"
ADAPTER_JSON = EV_DIR / "cycle-comparison/adapter-audit.json"
CORRECTED_7 = EV_DIR / "cycle-comparison/corrected-seven-date-comparison.csv"
CORRECTED_210 = EV_DIR / "cycle-comparison/corrected-210day-counts.csv"
DISPUTES = PHASE_ROOT / "docs/runbook/disputes.json"


def _str_keys(d):
    return {str(k): v for k, v in d.items()}


def test_calendrica_pancawara_is_mapping_b():
    data = json.loads(ADAPTER_JSON.read_text())
    panc = _str_keys(data["calendrica"]["mappings"]["Pancawara"]["name_by_index"])
    assert panc == {"1": "Umanis", "2": "Paing", "3": "Pon", "4": "Wage", "5": "Kliwon"}


def test_dewata_pancawara_is_mapping_a():
    data = json.loads(ADAPTER_JSON.read_text())
    panc = _str_keys(data["dewata"]["mappings"]["Pancawara"]["name_by_index"])
    assert panc == {"1": "Paing", "2": "Pon", "3": "Wage", "4": "Keliwon", "5": "Umanis"}


def test_cal_and_cultural_match_on_pancawara():
    data = json.loads(ADAPTER_JSON.read_text())
    cal = list(data["calendrica"]["mappings"]["Pancawara"]["name_by_index"].values())
    cultural = data["cultural_reference"]["mappings"]["Pancawara"]["name_order"]
    assert cal == cultural


def test_basabubali_pancawara_matches_mapping_b():
    data = json.loads(ADAPTER_JSON.read_text())
    bas = data["basabubali_org"]["mappings"]["Pancawara"]["remainder_to_name"]
    assert bas == {"1": "Umanis", "2": "Pahing", "3": "Pon", "4": "Wage", "5": "Kliwon"}


def test_corrected_7_date_cal_match_at_least_5():
    with open(CORRECTED_7) as f:
        reader = csv.DictReader(f, delimiter="|")
        rows = list(reader)
    assert len(rows) == 7
    cal_ok = sum(1 for r in rows if r["cal_all_match"] == "OK")
    cal_mix = sum(1 for r in rows if r["cal_all_match"] == "MIX")
    assert cal_ok + cal_mix == 7
    assert cal_ok >= 5


def test_corrected_7_date_dew_pancawara_always_wrong():
    with open(CORRECTED_7) as f:
        reader = csv.DictReader(f, delimiter="|")
        rows = list(reader)
    no_count = sum(1 for r in rows if r["dew_panc_match"] == "NO")
    assert no_count == 7


def test_corrected_210day_pancawara_numeric_match_210():
    with open(CORRECTED_210) as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            if row["comparison"] == "RAW_GREGORIAN_MAPPING" and row["field"] == "Pancawara":
                assert int(row["numeric_ok"]) == 210
                assert int(row["numeric_no"]) == 0
                assert int(row["semantic_ok"]) == 0
                assert int(row["semantic_no"]) == 210


def test_corrected_210day_saptawara_full_match():
    with open(CORRECTED_210) as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            if row["comparison"] == "RAW_GREGORIAN_MAPPING" and row["field"] == "Saptawara":
                assert int(row["numeric_ok"]) == 210
                assert int(row["semantic_ok"]) == 210
                assert int(row["numeric_no"]) == 0
                assert int(row["semantic_no"]) == 0


def test_corrected_210day_dasawara_numeric_match_semantic_mismatch():
    with open(CORRECTED_210) as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            if row["comparison"] == "RAW_GREGORIAN_MAPPING" and row["field"] == "Dasawara":
                assert int(row["numeric_ok"]) == 12
                assert int(row["semantic_ok"]) == 0
                assert int(row["semantic_no"]) == 210


def test_new_pancawara_dispute_filed():
    disputes = json.loads(DISPUTES.read_text())
    by_id = {d.get("id"): d for d in disputes if d.get("id")}
    assert "DISPUTE-pancawara-convention-shift-dewata-vs-cultural-2026-09-15" in by_id
    new = by_id["DISPUTE-pancawara-convention-shift-dewata-vs-cultural-2026-09-15"]
    # Corrected from naming_only to indexing_representation per user instruction (2026-09-15):
    # "That is more accurately: indexing_representation, rather than naming_only,
    # unless Dewata's numeric value is completely internal and never represents
    # a calendrical position externally."
    assert new["class"] == "indexing_representation", (
        f"Pancawara dispute should be classified indexing_representation, got {new['class']!r}"
    )
    assert new["blocking"] is False


def test_epoch_dispute_narrative_correction_recorded():
    disputes = json.loads(DISPUTES.read_text())
    by_id = {d.get("id"): d for d in disputes if d.get("id")}
    epoch = by_id["DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15"]
    assert "narrative_correction_2026-09-15" in epoch
    assert "Pancawara" in epoch["narrative_correction_2026-09-15"]["corrected_finding"] and "mapping B" in epoch["narrative_correction_2026-09-15"]["corrected_finding"]


def test_total_dispute_count():
    disputes = json.loads(DISPUTES.read_text())
    assert len(disputes) == 27


def test_cultural_convention_matches_basabubali_cal():
    """All three independent lineages (kb.org, BASAbali, CALENDRICA) agree on Pancawara mapping B."""
    data = json.loads(ADAPTER_JSON.read_text())
    assert data["cultural_reference"]["convention_matches_calendrica"] is True
    bas_panc = data["basabubali_org"]["mappings"]["Pancawara"]["remainder_to_name"]
    assert bas_panc == {"1": "Umanis", "2": "Pahing", "3": "Pon", "4": "Wage", "5": "Kliwon"}
    assert data["dewata"]["mappings"]["Pancawara"]["name_by_index"]["5"] == "Umanis"  # DEW is shifted


def test_basabubali_supports_simple_modular_not_special_case():
    """BASAbali Caturwara and Sangawara formulas are simple modular, no special case."""
    data = json.loads(ADAPTER_JSON.read_text())
    assert data["basabubali_org"]["supports_special_case_structure"] is False
    assert data["basabubali_org"]["structural_approach"].startswith("simple modular")
