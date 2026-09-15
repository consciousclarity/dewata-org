"""verify STATUS.json entries for the D&R Pawukon evidence package.

this test asserts:
- reingold_dershowitz_2018_pawukon_chapter: VERIFIED + INELIGIBLE
- reingold_dershowitz_2018_calendrica_4_0: VERIFIED + ELIGIBLE (claim-scoped)
- the second entry has the right axis values but unresolved disputes block ruleset promotion
- the prose chapter entry cannot satisfy a validation gate for any algorithmic claim
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

STATUS_PATH = Path("/opt/dw-phase2/phase-1/conformance/STATUS.json")


def _load_status() -> dict:
    with open(STATUS_PATH) as f:
        return json.load(f)


def test_prose_chapter_entry_exists():
    status = _load_status()
    assert "reingold_dershowitz_2018_pawukon_chapter" in status["corpora"]


def test_calendrica_entry_exists():
    status = _load_status()
    assert "reingold_dershowitz_2018_calendrica_4_0" in status["corpora"]


def test_prose_chapter_axes():
    status = _load_status()
    entry = status["corpora"]["reingold_dershowitz_2018_pawukon_chapter"]
    assert entry["verification_status"] == "VERIFIED"
    assert entry["reference_eligibility"] == "INELIGIBLE"
    assert entry["authority_basis"] == "scholarly"


def test_calendrica_axes():
    status = _load_status()
    entry = status["corpora"]["reingold_dershowitz_2018_calendrica_4_0"]
    assert entry["verification_status"] == "VERIFIED"
    assert entry["reference_eligibility"] == "ELIGIBLE"
    assert entry["authority_basis"] == "software_reference"


def test_prose_chapter_gate_closed():
    """prose chapter has VERIFIED + INELIGIBLE → gate MUST be False."""
    import sys
    sys.path.insert(0, "/opt/dw-phase2/phase-1/src")
    from dewatacalendar.corpus_status import corpus_record_for, can_satisfy_validation_gate
    rec = corpus_record_for("reingold_dershowitz_2018_pawukon_chapter")
    assert can_satisfy_validation_gate(rec) is False


def test_calendrica_gate_open():
    """CALENDRICA has VERIFIED + ELIGIBLE → gate returns True at the corpus level."""
    import sys
    sys.path.insert(0, "/opt/dw-phase2/phase-1/src")
    from dewatacalendar.corpus_status import corpus_record_for, can_satisfy_validation_gate
    rec = corpus_record_for("reingold_dershowitz_2018_calendrica_4_0")
    assert can_satisfy_validation_gate(rec) is True


def test_calendrica_blocks_ruleset_promotion():
    """Even though the corpus-level gate is True, unresolved blocking disputes
    must prevent any ruleset promotion using this corpus."""
    status = _load_status()
    entry = status["corpora"]["reingold_dershowitz_2018_calendrica_4_0"]
    assert entry["may_justify_ruleset_promotion"] is False
    blocking = entry.get("blocking_disputes_pending", [])
    assert len(blocking) >= 1, "expected at least one blocking dispute"
    # confirm the disputes are the right ones
    assert "DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15" in blocking


def test_calendrica_license_dispute_filed():
    """the Apache-vs-custom-license dispute must exist."""
    status_path = Path("/opt/dw-phase2/phase-1/docs/runbook/disputes.json")
    with open(status_path) as f:
        disputes = json.load(f)
    ids = [d.get("id") for d in disputes if d.get("id")]
    assert "DISPUTE-reference-reingold-dershowitz-2018-license-classification-2026-09-15" in ids


def test_epoch_anchor_dispute_filed():
    """epoch-anchor dispute between CALENDRICA and Dewata must exist."""
    status_path = Path("/opt/dw-phase2/phase-1/docs/runbook/disputes.json")
    with open(status_path) as f:
        disputes = json.load(f)
    ids = [d.get("id") for d in disputes if d.get("id")]
    assert "DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15" in ids


def test_special_case_disputes_filed():
    """special-case disputes (asatawara, sangawara, urip_5) must exist."""
    status_path = Path("/opt/dw-phase2/phase-1/docs/runbook/disputes.json")
    with open(status_path) as f:
        disputes = json.load(f)
    ids = [d.get("id") for d in disputes if d.get("id")]
    for expected in [
        "DISPUTE-wewaran-asatawara-special-case-formula-2026-09-15",
        "DISPUTE-wewaran-sangawara-special-case-formula-2026-09-15",
        "DISPUTE-wewaran-dasawara-urip-5-table-2026-09-15",
        "DISPUTE-wewaran-dwiwara-parity-basis-2026-09-15",
    ]:
        assert expected in ids, f"missing dispute: {expected}"
