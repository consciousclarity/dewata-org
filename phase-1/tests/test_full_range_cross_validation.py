"""Integrity and exact-count checks for the 1900-2099 evidence run."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path


PHASE_ROOT = Path(__file__).resolve().parents[1]
RESULTS = PHASE_ROOT / "evidence/cross-validation/1900-2099"
TOOLS = PHASE_ROOT / "tools/full_range_cross_validation"
FIELDS = ("pawukon_position", "wuku", "pancawara", "saptawara", "triwara", "sadwara")


def _summary() -> dict:
    return json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_full_range_and_constant_offsets_are_exact():
    summary = _summary()
    assert summary["range"] == {
        "start": "1900-01-01",
        "end": "2099-12-31",
        "inclusive_days": 73049,
    }
    assert summary["constant_offsets"] == {
        "pawukon_reference_minus_dewata_days_mod_210": 84,
        "wuku_reference_minus_dewata_mod_30": 12,
        "pancawara_dewata_minus_reference_days_mod_5": 1,
    }


def test_raw_dewata_reference_counts_are_exact():
    summary = _summary()
    for pair in ("dewata_vs_peradnya", "dewata_vs_rust"):
        raw = summary["counts"][pair]["raw"]
        for field in ("pawukon_position", "wuku", "pancawara"):
            assert raw[field] == {"matches": 0, "disagreements": 73049}
        for field in ("saptawara", "triwara", "sadwara"):
            assert raw[field] == {"matches": 73049, "disagreements": 0}


def test_phase_normalized_counts_are_exact():
    summary = _summary()
    for pair in ("dewata_vs_peradnya", "dewata_vs_rust"):
        normalized = summary["counts"][pair]["phase_normalized"]
        for field in FIELDS:
            assert normalized[field] == {"matches": 73049, "disagreements": 0}


def test_peradnya_and_rust_raw_counts_are_exact():
    raw = _summary()["counts"]["peradnya_vs_rust"]["raw"]
    for field in FIELDS:
        assert raw[field] == {"matches": 73049, "disagreements": 0}


def test_machine_readable_artifact_hashes():
    recorded = {}
    for line in (RESULTS / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        recorded[name] = digest
    paths = {
        "raw-outputs.jsonl.gz": RESULTS / "raw-outputs.jsonl.gz",
        "phase-normalized-comparisons.jsonl.gz": RESULTS / "phase-normalized-comparisons.jsonl.gz",
        "summary.json": RESULTS / "summary.json",
        "provenance.json": TOOLS / "provenance.json",
    }
    assert recorded.keys() == paths.keys()
    for name, path in paths.items():
        assert _sha256(path) == recorded[name]
    provenance = json.loads((TOOLS / "provenance.json").read_text(encoding="utf-8"))
    rust_lock = provenance["rust"]["reproduction_dependency_lock"]
    assert rust_lock["path"] == "phase-1/tools/full_range_cross_validation/rust-Cargo.lock"
    assert _sha256(TOOLS / "rust-Cargo.lock") == rust_lock["sha256"]


def test_raw_and_normalized_artifacts_have_exact_date_bounds():
    for name in ("raw-outputs.jsonl.gz", "phase-normalized-comparisons.jsonl.gz"):
        with gzip.open(RESULTS / name, "rt", encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle]
        assert len(rows) == 73049
        assert rows[0]["date"] == "1900-01-01"
        assert rows[-1]["date"] == "2099-12-31"


def test_authority_packet_is_explicitly_unapproved_and_unsent():
    packet = (PHASE_ROOT / "docs/audit/AUTHORITY_VALIDATION_PACKET_wuku_epoch_2026-09-16.md").read_text()
    assert "prepared only; not sent; no endorsement claimed" in packet
    assert "does not establish cultural authority" in packet
    assert "No response should be interpreted as authorization to change the engine" in packet
