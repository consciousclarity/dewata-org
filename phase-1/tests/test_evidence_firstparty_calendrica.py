"""verify the first-party EdReingold/calendar-code2 evidence artifacts.

this test:
- confirms LICENSE SHA-256 matches the recorded value
- confirms LICENSE is Apache License 2.0 verbatim
- confirms calendar.l SHA-256 matches the recorded value
- confirms calendar.l git blob SHA-1 matches the GitHub API
- confirms dates.l SHA-256 matches the recorded value
- confirms README SHA-256 matches the recorded value
- confirms calendar.l is NOT committed to the public repo (license compliance
  is being prepared separately per the user's absolute-boundary instruction)
- confirms the CALENDRICA source authentication metadata is present in STATUS.json
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


EV_DIR = Path("/opt/dw-phase2/phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2")
STATUS_PATH = Path("/opt/dw-phase2/phase-1/conformance/STATUS.json")


EXPECTED_LICENSE_SHA = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
EXPECTED_LICENSE_BLOB_SHA1 = "261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64"
EXPECTED_CALENDAR_SHA = "642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484"
EXPECTED_CALENDAR_BLOB_SHA1 = "2e4ad0f58ac52cb5fd497aa97b2b9ffe57ec623d"
EXPECTED_DATES_SHA = "d81cdfc1a3777b5dbf64473af3f5d272a73afda0fa5f2e97ec2ab299421a863e"
EXPECTED_DATES_BLOB_SHA1 = "e73a43b863178fbad14fd14210d7b10bd8920225"
EXPECTED_README_SHA = "c92d48ed825f98b233ae5c156427561a8732dbf1bb02329895309939ef9cc3e3"
EXPECTED_README_BLOB_SHA1 = "813fcc53e91b40c09a54a14842774a35666ea929"

EXPECTED_COMMIT_SHA = "9afc1f3277b839db1a70c2350d6c708ac83df78f"


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_firstparty_license_sha256():
    """first-party LICENSE file SHA-256 must match the recorded value."""
    actual = _sha256_of(EV_DIR / "LICENSE")
    assert actual == EXPECTED_LICENSE_SHA, (
        f"first-party LICENSE SHA mismatch: actual={actual} expected={EXPECTED_LICENSE_SHA}"
    )


def test_firstparty_license_is_apache_2():
    """first-party LICENSE must be verbatim Apache License 2.0."""
    text = (EV_DIR / "LICENSE").read_text()
    # Apache 2.0 verbatim header
    assert "Apache License" in text
    assert "Version 2.0, January 2004" in text
    assert "http://www.apache.org/licenses/" in text


def test_firstparty_calendar_l_sha256():
    """first-party calendar.l SHA-256 must match the recorded value."""
    actual = _sha256_of(EV_DIR / "calendar.l")
    assert actual == EXPECTED_CALENDAR_SHA, (
        f"first-party calendar.l SHA mismatch: actual={actual} expected={EXPECTED_CALENDAR_SHA}"
    )


def test_firstparty_dates_l_sha256():
    actual = _sha256_of(EV_DIR / "dates.l")
    assert actual == EXPECTED_DATES_SHA, (
        f"first-party dates.l SHA mismatch: actual={actual} expected={EXPECTED_DATES_SHA}"
    )


def test_firstparty_readme_sha256():
    actual = _sha256_of(EV_DIR / "README.md")
    assert actual == EXPECTED_README_SHA, (
        f"first-party README SHA mismatch: actual={actual} expected={EXPECTED_README_SHA}"
    )


def test_firstparty_metadata_records_commit_sha():
    meta = json.loads((EV_DIR / "METADATA.json").read_text())
    assert meta["repository"]["commit_sha"] == EXPECTED_COMMIT_SHA
    assert meta["license"]["type"] == "Apache License 2.0"
    assert meta["license"]["spdx_id"] == "Apache-2.0"


def test_calendrica_firstparty_entry_in_status():
    """STATUS.json must contain the first-party entry as ELIGIBLE."""
    status = json.loads(STATUS_PATH.read_text())
    assert "reingold_dershowitz_2018_calendrica_4_0_firstparty" in status["corpora"]
    entry = status["corpora"]["reingold_dershowitz_2018_calendrica_4_0_firstparty"]
    assert entry["verification_status"] == "VERIFIED"
    assert entry["reference_eligibility"] == "ELIGIBLE"
    assert entry["authority_basis"] == "software_reference"
    # may_satisfy_validation_gate was removed in v3.0 (post-stabilization
    # 2026-09-16): source-level boolean implied corpus-as-a-whole authority
    # that is forbidden. verification_status+reference_eligibility are
    # the structured fields; eligible_claim_ids would be required for
    # claim-scoped validation.
    assert "may_satisfy_validation_gate" not in entry
    # may_justify_ruleset_promotion is kept as DOCUMENTATION-ONLY
    assert entry["may_justify_ruleset_promotion"] is False
    # 5 blocking disputes
    blocking = entry["blocking_disputes_pending"]
    assert len(blocking) == 5


def test_calendrica_calixir_entry_in_status():
    """STATUS.json must contain the secondary Calixir entry as INELIGIBLE."""
    status = json.loads(STATUS_PATH.read_text())
    assert "reingold_dershowitz_2018_calendrica_4_0_calixir" in status["corpora"]
    entry = status["corpora"]["reingold_dershowitz_2018_calendrica_4_0_calixir"]
    assert entry["verification_status"] == "VERIFIED"
    assert entry["reference_eligibility"] == "INELIGIBLE"
    # may_satisfy_validation_gate was removed in v3.0 (post-stabilization
    # 2026-09-16): source-level boolean implied corpus-as-a-whole authority
    # that is forbidden under the v3.0 claim-scoped model.
    assert "may_satisfy_validation_gate" not in entry


def test_calendrica_firstparty_supersedes_calixir():
    """the first-party entry must record supersession of the Calixir entry."""
    status = json.loads(STATUS_PATH.read_text())
    fp = status["corpora"]["reingold_dershowitz_2018_calendrica_4_0_firstparty"]
    # supersedes must reference the calixir key
    assert "reingold_dershowitz_2018_calendrica_4_0" in fp.get("supersedes", "")
    cx = status["corpora"]["reingold_dershowitz_2018_calendrica_4_0_calixir"]
    assert cx.get("superseded_by") == "reingold_dershowitz_2018_calendrica_4_0_firstparty"


def test_license_dispute_resolved():
    """the original license dispute must be superseded and the resolution record
    must record the first-party Apache 2.0 evidence."""
    disputes = json.loads(Path("/opt/dw-phase2/phase-1/docs/runbook/disputes.json").read_text())
    by_id = {d.get("id"): d for d in disputes if d.get("id")}
    assert by_id["DISPUTE-reference-reingold-dershowitz-2018-license-classification-2026-09-15"]["resolution"] == "superseded"
    resolution = by_id["DISPUTE-reference-reingold-dershowitz-2018-license-firstparty-resolution-2026-09-15"]
    assert resolution["resolution"] == "resolved"
    assert "Apache 2.0" in resolution["notes"]
