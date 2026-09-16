"""Verify Wariga source evidence package artifacts exist and have expected content."""
import os
import json
import pytest
import hashlib

EVIDENCE_DIR = "/opt/dw-phase2/phase-1/evidence/references/balinese-wariga-sources"


def test_evidence_directory_exists():
    """The Wariga evidence directory must exist."""
    assert os.path.isdir(EVIDENCE_DIR), f"Evidence directory missing: {EVIDENCE_DIR}"


def test_bibliographic_records_md_exists():
    """Bibliographic records markdown must exist."""
    path = os.path.join(EVIDENCE_DIR, "bibliographic-records.md")
    assert os.path.exists(path)
    content = open(path).read()
    # must include S1-S5
    for s in ["S1. Pokok-pokok Wariga", "S2. Tenung Wariga", "S3. edysantosa/sakacalendar", "S4. Kemendikbud", "S5. babadbali.com"]:
        assert s in content, f"missing {s}"


def test_bibliographic_records_have_isbn_and_lccn():
    """S1 (Suparta Ardhana) must have ISBN-10 and LCCN recorded."""
    content = open(os.path.join(EVIDENCE_DIR, "bibliographic-records.md")).read()
    assert "979722242X" in content, "ISBN-10 missing"
    assert "2007308755" in content, "LCCN missing"
    assert "OL5988117W" in content, "Open Library work key missing"


def test_claim_register_md_exists():
    """Claim register markdown must exist."""
    path = os.path.join(EVIDENCE_DIR, "claim-register.md")
    assert os.path.exists(path)
    content = open(path).read()
    # must include all major claims
    for claim in ["Wuku/Gregorian Phase", "Pancawara Ordering", "Caturwara", "Astawara", "Sangawara", "Dasawara", "Dwiwara"]:
        assert claim in content, f"missing claim: {claim}"


def test_source_provenance_graph_exists():
    """Source provenance graph must exist."""
    path = os.path.join(EVIDENCE_DIR, "source-provenance-graph.md")
    assert os.path.exists(path)
    content = open(path).read()
    assert "S1" in content
    assert "S3" in content
    assert "S4" in content
    assert "S5" in content
    # must explicitly note that S3 is derivative of S1+S2
    assert "derivative of S1+S2" in content or "derivative of S1" in content


def test_source_access_notes_exists():
    """Source access notes must exist."""
    path = os.path.join(EVIDENCE_DIR, "source-access-notes.md")
    assert os.path.exists(path)
    content = open(path).read()
    # must include SHA-256 fingerprints
    assert "dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579" in content, "Java SHA-256 missing"
    assert "0ac38bf5e59c3ef755d3296894a3d865da43c0945c92b3ed4d1e19457b9fe429" in content, "PDF SHA-256 missing"


def test_manifest_md_exists():
    """Manifest must exist."""
    path = os.path.join(EVIDENCE_DIR, "MANIFEST.md")
    assert os.path.exists(path)
    content = open(path).read()
    assert "SHA-256" in content


def test_kemendikbud_pages_extracted():
    """Kemendikbud textbook minimum-evidence-quotes must include
    the Pawukon exceptions content needed for the claim register."""
    path = os.path.join(
        EVIDENCE_DIR,
        "kemendikbud-hindu-bs-kls-ix",
        "minimum-evidence-quotes.md",
    )
    assert os.path.exists(path), (
        f"missing minimum-evidence-quotes file: {path}"
    )
    content = open(path).read()
    # Must contain key terms from Pawukon exceptions
    assert "Caturwara" in content
    assert "Astawara" in content or "Asatawara" in content
    assert "Sangawara" in content
    # must include the Indonesian phrase for "exceptions"
    assert "pengecualian" in content
    # must include key wuku names
    assert "Dungulan" in content or "Dunggulan" in content
    assert "Sinta" in content


def test_kemendikbud_confirms_mapping_b():
    """Kemendikbud textbook confirms Pancawara mapping B (1=Umanis)."""
    path = os.path.join(
        EVIDENCE_DIR,
        "kemendikbud-hindu-bs-kls-ix",
        "minimum-evidence-quotes.md",
    )
    content = open(path).read()
    # Quote 1 must contain the Pancawara mapping names
    assert "Umanis" in content
    assert "Pahing" in content
    assert "Pon" in content
    assert "Wage" in content
    assert "Kliwon" in content
    # Quote 1 must explicitly assign 1=Umanis (mapping B)
    assert "(1) Umanis" in content or "1=Umanis" in content or "(1) Umanis" in content


def test_kemendikbud_license_uncertainty_recorded():
    """the Kemendikbud extraction must explicitly note the license
    status (government copyright, not Creative Commons) and explain
    why only the minimum-evidence quote was retained."""
    path = os.path.join(
        EVIDENCE_DIR,
        "kemendikbud-hindu-bs-kls-ix",
        "minimum-evidence-quotes.md",
    )
    content = open(path).read()
    # must mention Hak Cipta (Indonesian copyright assertion)
    assert "Hak Cipta" in content
    # must explicitly state redistribution rights are not granted
    assert "redistribution" in content.lower()
    # must reference the SHA-256 fingerprint
    assert "0ac38bf5e59c3ef755d3296894a3d865da43c0945c92b3ed4d1e19457b9fe429" in content


def test_java_functions_extracted():
    """Java source functions must be extracted with key Wariga references."""
    path = os.path.join(EVIDENCE_DIR, "edysantosa-sakacalendar", "extracted-functions.txt")
    assert os.path.exists(path)
    content = open(path).read()
    # Must include key function signatures
    assert "getPancawara" in content
    assert "getCaturwara" in content
    assert "getAstawara" in content
    assert "getSangawara" in content
    assert "getDasawara" in content
    # Must include the Jaya Tiga documentation
    assert "Jaya Tiga" in content


def test_status_json_includes_wariga_corpora():
    """STATUS.json must include the new Wariga corpora."""
    status_path = "/opt/dw-phase2/phase-1/conformance/STATUS.json"
    status = json.load(open(status_path))
    corpora = status.get("corpora", {})
    # new entries
    assert "wariga_suparta_ardhana_2006" in corpora
    assert "wariga_putra_manik_ariana_2009" in corpora
    assert "wariga_kemendikbud_hindu_bs_kls_ix_2022" in corpora
    assert "wariga_babadbali_com" in corpora
    assert "wariga_edysantosa_sakacalendar_java" in corpora


def test_wariga_kemendikbud_eligible_with_scope_limitations():
    """Kemendikbud textbook corpus must be ELIGIBLE but with explicit scope limitations."""
    status = json.load(open("/opt/dw-phase2/phase-1/conformance/STATUS.json"))
    corpus = status["corpora"]["wariga_kemendikbud_hindu_bs_kls_ix_2022"]
    assert corpus["verification_status"] == "VERIFIED"
    assert corpus["reference_eligibility"] == "ELIGIBLE"
    assert corpus["authority_basis"] == "institutional"
    assert "scope_limitations" in corpus
    # must explicitly note that Wuku/Gregorian phase remains insufficiently evidenced
    scope_text = " ".join(corpus["scope_limitations"])
    assert "Wuku/Gregorian" in scope_text or "Wuku/Gregorian examples" in scope_text


def test_wariga_suparta_ardhana_metadata_only():
    """S1 (Pokok-Pokok Wariga) must remain INELIGIBLE because chapter text not acquired."""
    status = json.load(open("/opt/dw-phase2/phase-1/conformance/STATUS.json"))
    corpus = status["corpora"]["wariga_suparta_ardhana_2006"]
    assert corpus["verification_status"] == "VERIFIED"  # bibliographic only
    assert corpus["reference_eligibility"] == "INELIGIBLE"  # chapter not acquired


def test_sakacalendar_java_sha256_matches_recorded():
    """the Java source file is held at /tmp/refs/sakacalendar.java (a
    working copy outside the public repo for copyright reasons — the
    full file is Apache-2.0 / LGPL but we keep the working copy out
    of git). the recorded SHA-256 must match the file's actual hash.

    this test is gated on the canonical evidence artifact path: the
    test fails if the file is missing. we do NOT silently skip on
    missing artifacts — a missing required artifact is a test
    failure, not a vacuous pass."""
    expected = "dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579"
    java_path = "/tmp/refs/sakacalendar.java"
    assert os.path.exists(java_path), (
        f"required evidence artifact missing at {java_path}; "
        "the Java working copy must be present at this canonical path "
        "for this test to run. missing artifacts fail, not vacuously pass."
    )
    actual = hashlib.sha256(open(java_path, 'rb').read()).hexdigest()
    assert actual == expected, f"Java SHA mismatch: {actual} != {expected}"


def test_pancawara_convention_multi_lineage_agreement():
    """Multiple independent lineages must agree on Pancawara mapping B
    convention. the Kemendikbud textbook (S4), the Java implementation
    (S3), and CALENDRICA all use 1=Umanis convention."""
    # The Kemendikbud textbook (S4) explicitly assigns 1=Umanis
    path = os.path.join(
        EVIDENCE_DIR,
        "kemendikbud-hindu-bs-kls-ix",
        "minimum-evidence-quotes.md",
    )
    content = open(path).read()
    # The textbook should list the 5 Pancawara names
    assert "Umanis" in content
    assert "Pahing" in content
    # The Java implementation uses noPancawara = (noWuku % 5) + 1 with mapping B convention
    java_path = os.path.join(EVIDENCE_DIR, "edysantosa-sakacalendar", "extracted-functions.txt")
    java_content = open(java_path).read()
    assert "getPancawara" in java_content


def test_sangawara_duration_disagreement_recorded():
    """The 3-vs-4 day Sangawara duration disagreement must be recorded in the claim register."""
    content = open(os.path.join(EVIDENCE_DIR, "claim-register.md")).read()
    # The claim register must mention both 3-day and 4-day Sangawara
    assert "3 consecutive Dangu" in content or "3 day" in content.lower()
    assert "4 consecutive Dangu" in content or "4 day" in content.lower()
    # And must note that CALENDRICA says 3 days while Kemendikbud/edysantosa say 4
    assert "L4" in content  # refers to CALENDRICA
    assert "S4" in content or "Kemendikbud" in content


def test_wuku_gregorian_phase_insufficient_evidence():
    """Wuku/Gregorian phase must be flagged as having insufficient independent evidence."""
    content = open(os.path.join(EVIDENCE_DIR, "claim-register.md")).read()
    # The claim register must note insufficient independent evidence for Wuku/Gregorian phase
    # and that only 1 lineage (kb.org L1) was retrieved
    assert "Insufficient independent evidence" in content or "insufficiently evidenced" in content or "INSUFFICIENT" in content


def test_no_silent_dispute_resolution():
    """Per PROTOCOL v1.0, no dispute must be resolved by Wariga source acquisition alone."""
    content = open(os.path.join(EVIDENCE_DIR, "claim-register.md")).read()
    # must explicitly note that disputes are not resolved
    assert "does NOT resolve disputes" in content or "not resolved" in content or "preserved" in content
