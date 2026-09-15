"""verify BASAbali evidence qualification notes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


EV_DIR = Path("/opt/dw-phase2/phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2")
ADAPTER_JSON = EV_DIR / "cycle-comparison/adapter-audit.json"
QUALIFICATION = EV_DIR / "cycle-comparison/basabubali-evidence-qualification.md"


def test_qualification_file_exists():
    assert QUALIFICATION.exists()


def test_qualification_warns_about_standalone_formula():
    text = QUALIFICATION.read_text()
    assert "A formula excerpt without its surrounding convention" in text
    assert "insufficient to establish a competing semantic ruleset" in text


def test_qualification_not_first_party_or_primary_academic():
    text = QUALIFICATION.read_text()
    assert "NOT a traditional Lontar or scholarly Wariga text" in text


def test_basabubali_pancawara_remainder_mapping():
    data = json.loads(ADAPTER_JSON.read_text())
    bas = data["basabubali_org"]["mappings"]["Pancawara"]["remainder_to_name"]
    assert bas == {"1": "Umanis", "2": "Pahing", "3": "Pon", "4": "Wage", "5": "Kliwon"}


def test_basabubali_caturwara_simple_modular():
    data = json.loads(ADAPTER_JSON.read_text())
    cat = data["basabubali_org"]["mappings"]["Caturwara"]
    assert "/" in cat["formula"] or "mod" in cat["formula"].lower()


def test_basabubali_sangawara_simple_modular():
    data = json.loads(ADAPTER_JSON.read_text())
    sng = data["basabubali_org"]["mappings"]["Sangawara"]
    assert "/" in sng["formula"] or "*" in sng["formula"]


def test_basabubali_dasawara_urip_based():
    data = json.loads(ADAPTER_JSON.read_text())
    das = data["basabubali_org"]["mappings"]["Dasawara"]
    assert "urip" in das["formula"].lower()


def test_basabubali_qualifies_as_community_reference():
    data = json.loads(ADAPTER_JSON.read_text())
    bas = data["basabubali_org"]
    assert "community" in bas["type"].lower()
    assert "first-party" not in bas["type"].lower()


def test_basabubali_supports_pancawara_convention_b():
    """BASAbali independently confirms mapping B (1=Umanis) which matches CAL and cultural reference."""
    data = json.loads(ADAPTER_JSON.read_text())
    bas_panc = data["basabubali_org"]["mappings"]["Pancawara"]["remainder_to_name"]
    cal_panc = data["calendrica"]["mappings"]["Pancawara"]["name_by_index"]
    # Both have 1=Umanis
    assert bas_panc["1"] == "Umanis"
    assert cal_panc["1"] == "Umanis"


def test_basabubali_does_not_support_special_case():
    """BASAbali Caturwara and Sangawara use simple modular arithmetic, not the special-case structure."""
    data = json.loads(ADAPTER_JSON.read_text())
    assert data["basabubali_org"]["supports_special_case_structure"] is False
