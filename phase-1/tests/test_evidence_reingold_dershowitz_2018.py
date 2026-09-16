"""verify the reingold-dershowitz-2018-pawukon evidence package.

this is a documentary integrity check — it does NOT verify any
calendrical claim. the chapter body is not archived here.

this test recomputes sha256 over every artifact listed in the
package MANIFEST.md and compares against the recorded hashes. a
mismatch indicates the package has been altered since the manifest
was committed.

the canonical evidence artifacts live in the public repository under
phase-1/evidence/references/reingold-dershowitz-2018-pawukon/. this
test does NOT depend on /tmp working copies — it operates on the
in-tree artifacts, so a missing or altered artifact fails the test
rather than silently passing.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest


EVDIR = (
    Path(__file__).resolve().parent.parent
    / "evidence" / "references" / "reingold-dershowitz-2018-pawukon"
)
MANIFEST = EVDIR / "MANIFEST.md"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _parse_recorded_hashes(manifest_text: str) -> dict[str, str]:
    """parse '`name` | `sha256`' rows from the MANIFEST table.

    returns a dict mapping artifact filename to recorded sha256.
    """
    out: dict[str, str] = {}
    for line in manifest_text.splitlines():
        m = re.search(r"`([^`]+)`.*?`([0-9a-f]{64})`", line)
        if m and len(m.group(1)) < 80:
            out[m.group(1)] = m.group(2)
    return out


@pytest.fixture(scope="module")
def recorded_hashes() -> dict[str, str]:
    """parse MANIFEST.md once per module."""
    assert MANIFEST.exists(), f"manifest not found: {MANIFEST}"
    hashes = _parse_recorded_hashes(MANIFEST.read_text(encoding="utf-8"))
    assert hashes, "no hashes parsed from manifest"
    return hashes


def test_evidence_manifest_exists_and_parses(recorded_hashes):
    """MANIFEST.md must exist and contain parseable SHA-256 entries."""
    assert MANIFEST.exists(), f"missing manifest: {MANIFEST}"
    assert recorded_hashes, "manifest contains no SHA-256 entries"


def test_every_recorded_artifact_exists(recorded_hashes):
    """every artifact listed in MANIFEST.md must be present in the
    evidence directory. a missing artifact fails the test (we do not
    silently skip on missing required artifacts)."""
    missing: list[str] = []
    for name in recorded_hashes:
        path = EVDIR / name
        if not path.exists():
            missing.append(name)
    assert not missing, (
        f"missing artifacts under {EVDIR}: {missing}"
    )


def test_every_recorded_artifact_sha256_matches(recorded_hashes):
    """every artifact's SHA-256 must equal the recorded value in
    MANIFEST.md. a mismatch indicates the artifact has been altered
    since the manifest was committed."""
    mismatches: list[tuple[str, str, str]] = []
    for name, expected in recorded_hashes.items():
        path = EVDIR / name
        if not path.exists():
            continue  # covered by test_every_recorded_artifact_exists
        actual = _sha256(path)
        if actual != expected:
            mismatches.append((name, expected, actual))
    assert not mismatches, (
        f"SHA-256 mismatches: {mismatches}"
    )


def test_evidence_directory_is_a_directory():
    """the canonical evidence directory must exist and be a directory."""
    assert EVDIR.is_dir(), f"evidence directory missing: {EVDIR}"


def test_first_party_calendrica_source_files_have_recorded_hashes(recorded_hashes):
    """the first-party CALENDRICA evidence directory must include
    files whose SHA-256 is recorded in the manifest. these are the
    files that anchor the entire CALENDRICA-based comparison
    argument."""
    firstparty_files = [
        "firstparty-EdReingold-calendar-code2/LICENSE",
        "firstparty-EdReingold-calendar-code2/calendar.l",
        "firstparty-EdReingold-calendar-code2/dates.l",
    ]
    for name in firstparty_files:
        assert name in recorded_hashes, (
            f"first-party CALENDRICA file {name!r} has no recorded "
            f"SHA-256 in MANIFEST.md"
        )


def test_secondary_calendrica_calixir_source_has_recorded_hash(recorded_hashes):
    """the secondary (Calixir) copy of CALENDRICA must have a recorded
    SHA-256. the actual Calixir .cl file is NOT in the public repo
    (per the older restrictive header), but its SHA-256 IS recorded
    in calendrica-source/METADATA.json (the canonical evidence
    artifact). The MANIFEST.md parses only filenames with backtick
    hashes; the metadata file uses JSON. We verify the metadata file
    contains the recorded SHA-256."""
    metadata_path = EVDIR / "calendrica-source" / "METADATA.json"
    assert metadata_path.exists(), (
        f"missing CALENDRICA metadata file: {metadata_path}"
    )
    import json
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    # the metadata file must record the source SHA-256 under source.sha256
    expected = "5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb"
    actual = metadata.get("source", {}).get("sha256")
    assert actual == expected, (
        f"CALENDRICA Calixir source SHA-256 mismatch in METADATA.json: "
        f"got {actual!r}"
    )


def test_calendrica_sample_data_has_recorded_hash(recorded_hashes):
    """CALENDRICA's dates4.csv sample data file must have a recorded
    SHA-256. this file is referenced by evidence tests for
    cross-validation."""
    assert "calendrica-source/dates4.csv" in recorded_hashes, (
        "CALENDRICA dates4.csv has no recorded SHA-256 in MANIFEST.md"
    )


def test_no_recorded_hash_for_nonexistent_artifact(recorded_hashes):
    """no MANIFEST.md entry should point to an artifact that does not
    exist. this catches stale MANIFEST entries."""
    stale: list[str] = []
    for name in recorded_hashes:
        path = EVDIR / name
        if not path.exists():
            stale.append(name)
    # already covered by test_every_recorded_artifact_exists, but
    # this is a separate assertion so a failure surfaces a more
    # specific message.
    assert not stale, f"MANIFEST references nonexistent artifacts: {stale}"
