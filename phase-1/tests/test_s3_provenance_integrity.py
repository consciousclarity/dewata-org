"""provenance integrity tests for the edysantosa/sakacalendar (S3)
evidence source.

per user instruction 2026-09-16, these tests assert:

- S3 canonical commit SHA is present and immutable
- mutable master is not the sole canonical identity
- complete-source SHA-256 remains the recorded value
- excerpt identifies Edy Santosa Putra
- LGPL-2.1 license artifact exists
- license artifact is referenced from the evidence manifest

These are provenance tests only; they do not change any claim status.
"""

import hashlib
import json
import re
from pathlib import Path

import pytest


WARIGA = Path(
    "/opt/dw-phase2/phase-1/evidence/references/balinese-wariga-sources"
)
STATUS = Path("/opt/dw-phase2/phase-1/conformance/STATUS.json")

S3_PINNED_COMMIT = "21ff347c0431cb12e02296f76077aa40525da9e0"
S3_FULL_SOURCE_SHA256 = (
    "dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579"
)
S3_LGPL_SHA256 = (
    "9b872a8a070b8ad329c4bd380fb1bf0000f564c75023ec8e1e6803f15364b9e9"
)
S3_ORIGINAL_AUTHOR = "Edy Santosa Putra"


@pytest.fixture(scope="module")
def s3_excerpt_path() -> Path:
    return WARIGA / "edysantosa-sakacalendar" / "extracted-functions.txt"


@pytest.fixture(scope="module")
def s3_license_path() -> Path:
    return WARIGA / "edysantosa-sakacalendar" / "LICENSE.LGPL-2.1"


@pytest.fixture(scope="module")
def s3_status_entry() -> dict:
    s = json.loads(STATUS.read_text(encoding="utf-8"))
    return s["corpora"]["wariga_edysantosa_sakacalendar_java"]


# 1. S3 canonical commit SHA is present


def test_s3_canonical_commit_sha_present_in_excerpt(s3_excerpt_path):
    """the evidence excerpt must record the exact pinned upstream
    commit SHA as the canonical source identity."""
    text = s3_excerpt_path.read_text(encoding="utf-8")
    assert S3_PINNED_COMMIT in text, (
        f"excerpt must contain pinned commit {S3_PINNED_COMMIT!r}; "
        f"mutable master URLs are not the canonical evidence locator"
    )


def test_s3_canonical_commit_sha_present_in_status(s3_status_entry):
    """STATUS.json S3 entry must record the pinned commit SHA."""
    assert S3_PINNED_COMMIT in s3_status_entry["reason"], (
        f"STATUS.json S3 reason must contain pinned commit "
        f"{S3_PINNED_COMMIT!r}"
    )


def test_s3_canonical_commit_sha_in_source_access_notes():
    """source-access-notes.md S3 section must record the pinned
    commit SHA."""
    text = (WARIGA / "source-access-notes.md").read_text(encoding="utf-8")
    assert S3_PINNED_COMMIT in text, (
        f"source-access-notes.md must contain pinned commit "
        f"{S3_PINNED_COMMIT!r}"
    )


def test_s3_canonical_commit_sha_in_bibliographic_records():
    """bibliographic-records.md S3 section must record the pinned
    commit SHA."""
    text = (WARIGA / "bibliographic-records.md").read_text(encoding="utf-8")
    assert S3_PINNED_COMMIT in text, (
        f"bibliographic-records.md must contain pinned commit "
        f"{S3_PINNED_COMMIT!r}"
    )


def test_s3_canonical_commit_sha_in_manifest():
    """MANIFEST.md S3 row must reference the pinned commit."""
    text = (WARIGA / "MANIFEST.md").read_text(encoding="utf-8")
    assert S3_PINNED_COMMIT in text, (
        f"MANIFEST.md must reference pinned commit {S3_PINNED_COMMIT!r}"
    )


# 2. mutable master is not the sole canonical identity


def test_s3_master_url_not_solo_canonical_in_excerpt(s3_excerpt_path):
    """the excerpt must NOT use mutable master as the sole canonical
    identity. master URLs are allowed only as supplementary context."""
    text = s3_excerpt_path.read_text(encoding="utf-8")
    # the excerpt must explicitly mark master as non-canonical
    assert "mutable master" in text.lower() or \
           "pinned" in text.lower(), (
        f"excerpt must explicitly note mutable master is not canonical"
    )


def test_s3_master_url_not_solo_canonical_in_status(s3_status_entry):
    """STATUS.json S3 reason must explicitly mark master as mutable
    (not the canonical evidence locator)."""
    assert "mutable" in s3_status_entry["reason"].lower() or \
           "not mutable master" in s3_status_entry["reason"].lower() or \
           "pinned" in s3_status_entry["reason"].lower(), (
        f"STATUS.json must mark master as mutable"
    )


# 3. complete-source SHA-256 remains the recorded value


def test_s3_complete_source_sha256_recorded(s3_excerpt_path, s3_status_entry):
    """the full-source SHA-256 (the recorded value, verified against
    the pinned commit on 2026-09-16) must appear in the excerpt and
    in STATUS.json."""
    assert S3_FULL_SOURCE_SHA256 in s3_excerpt_path.read_text(encoding="utf-8"), (
        f"excerpt must record complete-source SHA-256 "
        f"{S3_FULL_SOURCE_SHA256!r}"
    )
    assert S3_FULL_SOURCE_SHA256 in s3_status_entry["reason"], (
        f"STATUS.json must record complete-source SHA-256 "
        f"{S3_FULL_SOURCE_SHA256!r}"
    )


def test_s3_complete_source_sha256_in_source_access_notes():
    """source-access-notes.md must record the complete-source SHA-256."""
    text = (WARIGA / "source-access-notes.md").read_text(encoding="utf-8")
    assert S3_FULL_SOURCE_SHA256 in text, (
        f"source-access-notes.md must record complete-source SHA-256"
    )


def test_s3_complete_source_sha256_in_bibliographic_records():
    """bibliographic-records.md must record the complete-source
    SHA-256."""
    text = (WARIGA / "bibliographic-records.md").read_text(encoding="utf-8")
    assert S3_FULL_SOURCE_SHA256 in text


def test_s3_complete_source_sha256_in_manifest():
    """MANIFEST.md must record the complete-source SHA-256."""
    text = (WARIGA / "MANIFEST.md").read_text(encoding="utf-8")
    assert S3_FULL_SOURCE_SHA256 in text


# 4. excerpt identifies Edy Santosa Putra


def test_s3_excerpt_identifies_original_author(s3_excerpt_path):
    """the excerpt must clearly identify Edy Santosa Putra as the
    original author."""
    text = s3_excerpt_path.read_text(encoding="utf-8")
    assert S3_ORIGINAL_AUTHOR in text, (
        f"excerpt must identify original author "
        f"{S3_ORIGINAL_AUTHOR!r}"
    )


def test_s3_bibliographic_records_identify_original_author():
    """bibliographic-records.md S3 section must identify Edy Santosa
    Putra as the original author."""
    text = (WARIGA / "bibliographic-records.md").read_text(encoding="utf-8")
    assert S3_ORIGINAL_AUTHOR in text


def test_s3_source_access_notes_identify_original_author():
    """source-access-notes.md S3 section must identify Edy Santosa
    Putra as the original author."""
    text = (WARIGA / "source-access-notes.md").read_text(encoding="utf-8")
    assert S3_ORIGINAL_AUTHOR in text


# 5. LGPL-2.1 license artifact exists


def test_s3_lgpl_license_artifact_exists(s3_license_path):
    """the upstream LGPL-2.1 LICENSE text must be retained as a
    sibling file in the evidence package."""
    assert s3_license_path.exists(), (
        f"missing LGPL-2.1 license artifact: {s3_license_path}"
    )
    text = s3_license_path.read_text(encoding="utf-8")
    # the upstream LGPL-2.1 LICENSE text starts with "GNU LESSER
    # GENERAL PUBLIC LICENSE" and mentions "Version 2.1"
    assert "GNU LESSER GENERAL PUBLIC LICENSE" in text, (
        "license artifact must contain LGPL header"
    )
    assert "Version 2.1" in text, (
        "license artifact must be LGPL version 2.1"
    )


def test_s3_lgpl_license_sha256_recorded(s3_license_path):
    """the LGPL-2.1 license artifact SHA-256 must match the value
    recorded in the evidence package."""
    actual = hashlib.sha256(
        s3_license_path.read_bytes()
    ).hexdigest()
    assert actual == S3_LGPL_SHA256, (
        f"LGPL-2.1 license SHA-256 mismatch: expected {S3_LGPL_SHA256!r}, "
        f"got {actual!r}"
    )


def test_s3_lgpl_sha256_in_excerpt(s3_excerpt_path):
    """the excerpt must record the LGPL-2.1 license SHA-256."""
    text = s3_excerpt_path.read_text(encoding="utf-8")
    assert S3_LGPL_SHA256 in text, (
        f"excerpt must record LGPL-2.1 license SHA-256 "
        f"{S3_LGPL_SHA256!r}"
    )


# 6. license artifact is referenced from the evidence manifest


def test_s3_license_referenced_in_manifest():
    """MANIFEST.md must reference the LGPL-2.1 license artifact."""
    text = (WARIGA / "MANIFEST.md").read_text(encoding="utf-8")
    assert "LICENSE.LGPL-2.1" in text, (
        "MANIFEST.md must reference the LGPL-2.1 license artifact"
    )


def test_s3_license_referenced_in_bibliographic_records():
    """bibliographic-records.md must reference the LGPL-2.1 license
    artifact."""
    text = (WARIGA / "bibliographic-records.md").read_text(encoding="utf-8")
    assert "LICENSE.LGPL-2.1" in text


def test_s3_license_referenced_in_source_access_notes():
    """source-access-notes.md must reference the LGPL-2.1 license
    artifact."""
    text = (WARIGA / "source-access-notes.md").read_text(encoding="utf-8")
    assert "LICENSE.LGPL-2.1" in text


# 7. status.json corpus_file is unchanged (still points to the excerpt)


def test_s3_corpus_file_unchanged(s3_status_entry):
    """the S3 corpus_file pointer must continue to point to the
    in-tree excerpt (not to the upstream source)."""
    assert s3_status_entry["corpus_file"] == (
        "phase-1/evidence/references/balinese-wariga-sources/"
        "edysantosa-sakacalendar/extracted-functions.txt"
    )


def test_s3_status_axes_unchanged(s3_status_entry):
    """the S3 entry's verification_status, reference_eligibility,
    and authority_basis must not have been altered."""
    assert s3_status_entry["verification_status"] == "VERIFIED"
    assert s3_status_entry["reference_eligibility"] == "ELIGIBLE"
    assert s3_status_entry["authority_basis"] == "software_reference"


def test_s3_eligible_claim_ids_still_empty(s3_status_entry):
    """no eligible_claim_ids must have been populated during this
    pass. zero sources may automatically become claim-validating."""
    assert s3_status_entry.get("eligible_claim_ids", []) == []


def test_s3_no_may_satisfy_validation_gate(s3_status_entry):
    """the source-level boolean may_satisfy_validation_gate must
    not have been added back to S3 (removed in commit a05a4d1)."""
    assert "may_satisfy_validation_gate" not in s3_status_entry


def test_s3_no_may_be_described_as_ground_truth(s3_status_entry):
    """the source-level boolean may_be_described_as_ground_truth must
    not have been added back to S3."""
    assert "may_be_described_as_ground_truth" not in s3_status_entry


def test_s3_may_justify_ruleset_promotion_remains_false(s3_status_entry):
    """the documentation-only may_justify_ruleset_promotion must
    remain false (not consulted by any gate function)."""
    assert s3_status_entry.get("may_justify_ruleset_promotion") is False


# 8. canonical upstream URL pinning


def test_s3_canonical_url_is_pinned(s3_status_entry):
    """the canonical upstream URL must reference the pinned commit,
    not mutable master."""
    assert S3_PINNED_COMMIT in s3_status_entry["reason"]
    # ensure the immutable URL pattern appears
    assert f"/tree/{S3_PINNED_COMMIT}" in s3_status_entry["reason"] or \
           f"@{S3_PINNED_COMMIT}" in s3_status_entry["reason"], (
        "STATUS.json must reference the pinned commit via immutable URL"
    )


def test_s3_manifest_canonical_url_is_pinned():
    """MANIFEST.md canonical URL for S3 must be the pinned-commit
    URL, not the mutable master raw URL."""
    text = (WARIGA / "MANIFEST.md").read_text(encoding="utf-8")
    assert f"/tree/{S3_PINNED_COMMIT}" in text or \
           f"@{S3_PINNED_COMMIT}" in text
    # confirm the old mutable-master raw URL is NOT the canonical entry
    assert "raw.githubusercontent.com/edysantosa/sakacalendar/master" not in text or \
           "mutable master" in text.lower(), (
        "MANIFEST.md should not have raw.githubusercontent.com/.../master "
        "as the sole canonical URL"
    )


# 9. neutral provenance rationale — no "fair-use" framing


def test_s3_excerpt_no_fair_use_framing(s3_excerpt_path):
    """the excerpt must not frame the LGPL-2.1 excerpt under a
    'fair-use' rationale. LGPL-2.1 governs the upstream; the
    excerpt is committed with upstream attribution and license
    retained."""
    text = s3_excerpt_path.read_text(encoding="utf-8")
    assert "fair-use" not in text.lower(), (
        f"excerpt must not use 'fair-use' framing; upstream license is LGPL-2.1"
    )


def test_s3_manifest_no_fair_use_framing():
    """MANIFEST.md must not frame the LGPL-2.1 excerpt under a
    'fair-use' rationale."""
    text = (WARIGA / "MANIFEST.md").read_text(encoding="utf-8")
    # search the S3 row only (not other sources)
    in_s3_row = False
    for line in text.split("\n"):
        if line.startswith("| S3"):
            in_s3_row = True
            if "fair-use" in line.lower() or "fair use" in line.lower():
                pytest.fail(
                    f"S3 row in MANIFEST.md still uses fair-use framing: {line!r}"
                )
        elif in_s3_row and line.startswith("|") and not line.startswith("| S3"):
            in_s3_row = False
