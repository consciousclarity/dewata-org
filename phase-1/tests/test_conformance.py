"""conformance harness for the dewata calendar engine.

`pytest -q tests/test_conformance.py` runs all conformance vectors and
the corpus-evidence-status gate tests.

## corpus enumeration

the harness explicitly enumerates corpus basenames in PUBLISHED_CORPORA.
it does NOT glob `*.json` under `conformance/` because that directory
also contains STATUS.json (the corpus-evidence-status registry),
which is metadata, not corpus vectors. STATUS.json must never be
loadable as a corpus — a directory name does not confer authority
(see phase-1/conformance/STATUS.schema.md).

## corpus evidence status (two-axis model)

per phase-1/conformance/STATUS.json schema v2, every corpus has two
orthogonal axes:
  verification_status:  UNVERIFIED | VERIFIED
  reference_eligibility: INELIGIBLE | ELIGIBLE

the gate rule is:
  can_satisfy_validation_gate(corpus) =
      verification_status == VERIFIED
   AND reference_eligibility == ELIGIBLE

the legacy single-axis `CorpusStatus` is retained as a derived view
for callers that don't need the two-axis detail.

the published corpora in their current state:
  cunningham_1994       UNVERIFIED + INELIGIBLE   (book not on host)
  igarashi_1999         UNVERIFIED + INELIGIBLE   (publisher unverified)
  kalenderbali_2026-09  VERIFIED   + INELIGIBLE   (page retrievable,
                                                    practitioner source)

none of these currently satisfies the gate.

## separation from ceremonial provenance

this test file governs the bibliographic / evidence-chain layer
for conformance corpora. it does NOT touch Dewata's ceremonial/
record provenance tiers (computed / registered / predicted / verified)
governed by PROTOCOL §2.6.

the pre-v1.0 assumption that any file under conformance/published/
is authoritative has been explicitly corrected here. STATUS.json
is the single source of truth for authority.

this file does NOT touch test_dispute_recordable_classifications or
any other test in tests/test_cultural_adapters.py — those belong to
the v1.0 dispute-schema migration (item 7 in the gap analysis
remediation order), not to the corpus-evidence-status quarantine.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

from dewatacalendar.api import compose_day
from dewatacalendar.conformance import load_corpus
from dewatacalendar.corpus_status import (
    AuthorityBasis,
    CorpusRecord,
    CorpusStatus,
    ReferenceEligibility,
    VerificationStatus,
    annotate_vectors_with_status,
    can_be_described_as_ground_truth,
    can_be_silently_copied_to_authoritative_fixture,
    can_promote_ruleset_using,
    can_satisfy_validation_gate,
    corpus_record_for,
)


CORPUS_ROOT = Path(__file__).resolve().parent.parent / "conformance"
PUBLISHED_DIR = CORPUS_ROOT / "published"
STATUS_FILE = CORPUS_ROOT / "STATUS.json"

# explicit enumeration — do not use glob. a directory name does not
# confer authority. STATUS.json is metadata and is excluded by name
# here, NOT by glob-exclusion logic.
PUBLISHED_CORPORA: tuple[str, ...] = (
    "cunningham_1994",
    "igarashi_1999",
    "kalenderbali_2026-09",
)

# expected two-axis classification per STATUS.json schema v2.
# any drift between this map and the actual STATUS.json fails the
# registry-drift tests below.
EXPECTED_VERIFICATION: dict[str, str] = {
    "cunningham_1994": VerificationStatus.UNVERIFIED.value,
    "igarashi_1999": VerificationStatus.UNVERIFIED.value,
    "kalenderbali_2026-09": VerificationStatus.VERIFIED.value,
}

EXPECTED_ELIGIBILITY: dict[str, str] = {
    "cunningham_1994": ReferenceEligibility.INELIGIBLE.value,
    "igarashi_1999": ReferenceEligibility.INELIGIBLE.value,
    "kalenderbali_2026-09": ReferenceEligibility.INELIGIBLE.value,
}

EXPECTED_AUTHORITY_BASIS: dict[str, str] = {
    "cunningham_1994": AuthorityBasis.UNKNOWN.value,
    "igarashi_1999": AuthorityBasis.UNKNOWN.value,
    "kalenderbali_2026-09": AuthorityBasis.PRACTITIONER.value,
}

EXPECTED_GATE_PASSES: dict[str, bool] = {
    # every published corpus currently fails the gate.
    "cunningham_1994": False,
    "igarashi_1999": False,
    "kalenderbali_2026-09": False,
}


# ──────────────────────────────────────────────────────────────────────
# Section 1 — registry integrity: STATUS.json is the single source of
# truth, and the canonical STATUS location is conformance/STATUS.json
# ──────────────────────────────────────────────────────────────────────


def test_status_file_exists_at_canonical_location():
    """STATUS.json lives at phase-1/conformance/STATUS.json. it does
    NOT live under published/. STATUS.json is metadata; published/
    contains historical corpus material."""
    assert STATUS_FILE.exists(), f"missing canonical registry: {STATUS_FILE}"
    assert not (PUBLISHED_DIR / "STATUS.json").exists(), (
        "STATUS.json must NOT live under published/ — authority comes "
        "from the canonical STATUS location, not from directory placement"
    )


def test_status_file_is_not_loadable_as_a_corpus():
    """STATUS.json must never be interpretable as a corpus. load_corpus
    refuses to load it (either because no file is found at the
    STATUS location, or because the file's structure does not match
    a corpus — both are refusals)."""
    with pytest.raises((FileNotFoundError, ValueError)):
        load_corpus("STATUS")


def test_registry_axis_values_match_expected_for_each_published_corpus():
    """for every corpus in PUBLISHED_CORPORA, the two-axis
    classification declared in STATUS.json matches the expected v1.0
    quarantine status."""
    for name in PUBLISHED_CORPORA:
        record = corpus_record_for(name)
        assert record is not None, f"corpus {name!r}: no record in STATUS.json"
        assert record.verification_status.value == EXPECTED_VERIFICATION[name], (
            f"corpus {name!r}: verification_status={record.verification_status.value!r}, "
            f"expected {EXPECTED_VERIFICATION[name]!r}"
        )
        assert record.reference_eligibility.value == EXPECTED_ELIGIBILITY[name], (
            f"corpus {name!r}: reference_eligibility={record.reference_eligibility.value!r}, "
            f"expected {EXPECTED_ELIGIBILITY[name]!r}"
        )
        assert record.authority_basis.value == EXPECTED_AUTHORITY_BASIS[name], (
            f"corpus {name!r}: authority_basis={record.authority_basis.value!r}, "
            f"expected {EXPECTED_AUTHORITY_BASIS[name]!r}"
        )


def test_unknown_corpus_fails_closed_to_unverified_ineligible_unknown():
    """corpora not registered in STATUS.json must default to the
    fail-closed axis combination: UNVERIFIED + INELIGIBLE + unknown.
    a directory name does not confer authority."""
    for name in ("totally_made_up_corpus", "another_unknown", ""):
        record = corpus_record_for(name)
        if record is None:
            # No record at all — the load function returns None for
            # unknown corpora. Verify the fallback annotation
            # matches the fail-closed axes by exercising the
            # annotation through load_corpus if possible, otherwise
            # verify the gate directly.
            from dewatacalendar.corpus_status import annotate_vectors_with_status as avs
            ann = avs([{"gregorian": "2026-09-01"}], name)
            for v in ann:
                assert v["_corpus_verification_status"] == VerificationStatus.UNVERIFIED.value
                assert v["_corpus_reference_eligibility"] == ReferenceEligibility.INELIGIBLE.value
                assert v["_corpus_authority_basis"] == AuthorityBasis.UNKNOWN.value
        else:
            assert record.verification_status == VerificationStatus.UNVERIFIED
            assert record.reference_eligibility == ReferenceEligibility.INELIGIBLE
            assert record.authority_basis == AuthorityBasis.UNKNOWN


# ──────────────────────────────────────────────────────────────────────
# Section 2 — gate predicate: two-axis rule with full matrix coverage
# ──────────────────────────────────────────────────────────────────────


def _make_record(verification: str, eligibility: str, basis: str = "unknown") -> CorpusRecord:
    return CorpusRecord(
        corpus_basename="<test>",
        corpus_file="<test>",
        corpus_class="<test>",
        verification_status=VerificationStatus(verification),
        reference_eligibility=ReferenceEligibility(eligibility),
        authority_basis=AuthorityBasis(basis),
        reason="<test>",
        related_dispute_id=None,
        date_classified="<test>",
        evidence_review_artifact="<test>",
        citation_keys=(),
    )


def test_gate_unverified_ineligible_returns_false():
    """UNVERIFIED + INELIGIBLE -> gate False. this is the
    Cunningham/Igarashi current state."""
    r = _make_record("UNVERIFIED", "INELIGIBLE")
    assert can_satisfy_validation_gate(r) is False
    assert can_promote_ruleset_using(r) is False
    assert can_be_described_as_ground_truth(r) is False
    assert can_be_silently_copied_to_authoritative_fixture(r) is False


def test_gate_verified_ineligible_returns_false():
    """VERIFIED + INELIGIBLE -> gate False. this is the kalenderbali
    current state. the page is retrievable but the source is a
    practitioner calendar, so it cannot satisfy an authoritative
    calendar validation gate."""
    r = _make_record("VERIFIED", "INELIGIBLE", "practitioner")
    assert can_satisfy_validation_gate(r) is False
    assert can_promote_ruleset_using(r) is False
    assert can_be_described_as_ground_truth(r) is False
    assert can_be_silently_copied_to_authoritative_fixture(r) is False


def test_gate_verified_eligible_returns_true():
    """VERIFIED + ELIGIBLE -> gate True. a properly acquired scholarly
    source (e.g. Dershowitz & Reingold Pawukon chapter, once archived
    per the remediation order) would have this axis combination."""
    r = _make_record("VERIFIED", "ELIGIBLE", "scholarly")
    assert can_satisfy_validation_gate(r) is True
    assert can_promote_ruleset_using(r) is True
    assert can_be_described_as_ground_truth(r) is True
    assert can_be_silently_copied_to_authoritative_fixture(r) is True


def test_gate_unverified_eligible_returns_false():
    """UNVERIFIED + ELIGIBLE -> gate False. the citation is presumed
    eligible but cannot be independently retrieved. this is the
    correct failure mode for a future source where the cited work
    is known to be on-topic and authoritative, but no copy is
    available on this host to confirm."""
    r = _make_record("UNVERIFIED", "ELIGIBLE")
    assert can_satisfy_validation_gate(r) is False
    assert can_promote_ruleset_using(r) is False
    assert can_be_described_as_ground_truth(r) is False
    assert can_be_silently_copied_to_authoritative_fixture(r) is False


def test_gate_unknown_corpus_returns_false():
    """unknown corpus -> gate False (fail-closed). an unknown corpus
    returns no CorpusRecord (corpus_record_for returns None), and
    can_satisfy_validation_gate(None) fails closed. this exercises
    the fail-closed behavior on unknown basenames."""
    for n in ("totally_unknown", "", "STATUS"):
        record = corpus_record_for(n)
        assert record is None, (
            f"unexpected: corpus {n!r} returned a record; "
            "unknown corpora should return None"
        )
        # None to the gate fails closed
        assert can_satisfy_validation_gate(record) is False


def test_gate_recognizes_legacy_single_axis_status():
    """the legacy single-axis CorpusStatus enum is still recognized by
    the gate predicate. ATTESTED -> True (passes); everything else
    -> False (fails closed)."""
    assert can_satisfy_validation_gate(CorpusStatus.ATTESTED) is True
    assert can_satisfy_validation_gate(CorpusStatus.NON_AUTHORITATIVE) is False
    assert can_satisfy_validation_gate(CorpusStatus.UNVERIFIED) is False
    # string forms also accepted
    assert can_satisfy_validation_gate("ATTESTED") is True
    assert can_satisfy_validation_gate("UNVERIFIED") is False
    assert can_satisfy_validation_gate("MAYBE_OK") is False
    assert can_satisfy_validation_gate("") is False
    assert can_satisfy_validation_gate("authoritative") is False


def test_single_axis_enum_alone_cannot_satisfy_gate():
    """passing a single axis enum alone cannot satisfy the gate —
    both axes must pass together. UNVERIFIED alone is not enough
    even with the right axis combination; VERIFIED alone is not
    enough; ELIGIBLE alone is not enough."""
    assert can_satisfy_validation_gate(VerificationStatus.VERIFIED) is False
    assert can_satisfy_validation_gate(VerificationStatus.UNVERIFIED) is False
    assert can_satisfy_validation_gate(ReferenceEligibility.ELIGIBLE) is False
    assert can_satisfy_validation_gate(ReferenceEligibility.INELIGIBLE) is False


def test_authority_basis_does_not_alone_satisfy_gate():
    """authority_basis is metadata; it does NOT itself determine
    whether the gate passes. a corpus with basis=scholarly but
    verification=UNVERIFIED still fails."""
    r = _make_record("UNVERIFIED", "INELIGIBLE", "scholarly")
    assert can_satisfy_validation_gate(r) is False
    r = _make_record("VERIFIED", "ELIGIBLE", "unknown")
    assert can_satisfy_validation_gate(r) is True  # basis does not gate


# ──────────────────────────────────────────────────────────────────────
# Section 3 — corpus loads + per-corpus two-axis annotation
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module", params=list(PUBLISHED_CORPORA))
def published_corpus_name(request) -> str:
    return request.param


def test_published_corpus_file_exists(published_corpus_name):
    """every corpus in PUBLISHED_CORPORA must have a JSON file under
    conformance/published/."""
    path = PUBLISHED_DIR / f"{published_corpus_name}.json"
    assert path.exists(), f"corpus file missing: {path}"


def test_published_corpus_loads_with_two_axis_annotation(published_corpus_name):
    """load_corpus returns the vectors and annotates each with the
    two-axis evidence status (verification_status +
    reference_eligibility + authority_basis). UNVERIFIED / INELIGIBLE
    corpora remain loadable; they are diagnostic only and may not
    satisfy a validation gate."""
    vectors = load_corpus(published_corpus_name)
    assert len(vectors) > 0, f"corpus {published_corpus_name} is empty"
    expected_v = EXPECTED_VERIFICATION[published_corpus_name]
    expected_r = EXPECTED_ELIGIBILITY[published_corpus_name]
    expected_a = EXPECTED_AUTHORITY_BASIS[published_corpus_name]
    for v in vectors:
        assert v.get("_corpus_verification_status") == expected_v, (
            f"vector in {published_corpus_name} annotated with "
            f"verification_status={v.get('_corpus_verification_status')!r}, "
            f"expected {expected_v!r}"
        )
        assert v.get("_corpus_reference_eligibility") == expected_r, (
            f"vector in {published_corpus_name} annotated with "
            f"reference_eligibility={v.get('_corpus_reference_eligibility')!r}, "
            f"expected {expected_r!r}"
        )
        assert v.get("_corpus_authority_basis") == expected_a, (
            f"vector in {published_corpus_name} annotated with "
            f"authority_basis={v.get('_corpus_authority_basis')!r}, "
            f"expected {expected_a!r}"
        )


def test_published_corpus_annotation_carries_review_record(published_corpus_name):
    """each annotated vector carries a `_corpus_record` with reason,
    related_dispute_id, date_classified, and evidence_review_artifact."""
    vectors = load_corpus(published_corpus_name)
    sample = vectors[0]
    rec = sample.get("_corpus_record", {})
    assert rec.get("reason"), f"{published_corpus_name}: missing reason"
    assert rec.get("date_classified"), f"{published_corpus_name}: missing date_classified"
    assert rec.get("evidence_review_artifact"), f"{published_corpus_name}: missing evidence_review_artifact"


def test_published_corpora_remain_diagnostically_loadable(published_corpus_name):
    """UNVERIFIED / NON_AUTHORITATIVE corpora may still be loaded for
    historical comparison and diagnostic output. this is what
    'preserved != silent' means."""
    vectors = load_corpus(published_corpus_name)
    assert len(vectors) > 0, (
        f"corpus {published_corpus_name} is not loadable; quarantine "
        "does not mean silence"
    )


# ──────────────────────────────────────────────────────────────────────
# Section 4 — gate behavior per corpus
# ──────────────────────────────────────────────────────────────────────


def test_each_published_corpus_cannot_satisfy_validation_gate(published_corpus_name):
    """every currently-published corpus has axes that fail the gate.
    this is the core enforcement: even if a future ruleset bump
    happens to match the corpus's vectors, the corpus's axes
    (verification, eligibility) block the promotion from being
    justified by that corpus alone."""
    record = corpus_record_for(published_corpus_name)
    assert record is not None
    assert can_satisfy_validation_gate(record) is False, (
        f"corpus {published_corpus_name} unexpectedly satisfies the gate"
    )


def test_each_published_corpus_cannot_justify_ruleset_promotion(published_corpus_name):
    record = corpus_record_for(published_corpus_name)
    assert record is not None
    assert can_promote_ruleset_using(record) is False


def test_each_published_corpus_cannot_be_described_as_ground_truth(published_corpus_name):
    record = corpus_record_for(published_corpus_name)
    assert record is not None
    assert can_be_described_as_ground_truth(record) is False


# ──────────────────────────────────────────────────────────────────────
# Section 5 — separation from ceremonial provenance tier
# ──────────────────────────────────────────────────────────────────────


def test_ceremonial_tier_unaffected_by_corpus_evidence_status():
    """per the protocol: corpus evidence status (verification_status,
    reference_eligibility, authority_basis) is the bibliographic /
    evidence-chain layer. it does NOT affect Dewata's ceremonial /
    record provenance tiers (computed / registered / predicted /
    verified) governed by PROTOCOL §2.6.

    this test asserts that the corpus status module does not export
    a 'verified' ceremonial tier, and that the names 'computed',
    'registered', 'predicted', 'verified' are not shadowed by the
    bibliographic layer."""
    from dewatacalendar import corpus_status

    # the corpus_status module's namespace uses 'verified' only as
    # part of VerificationStatus.VERIFIED. that is the bibliographic
    # axis, not the ceremonial tier.
    assert hasattr(corpus_status, "VerificationStatus")
    assert hasattr(corpus_status, "ReferenceEligibility")
    assert hasattr(corpus_status, "AuthorityBasis")
    assert VerificationStatus.VERIFIED.value == "VERIFIED"
    # ensure the ceremonial tier 'verified' is not shadowed as a
    # module-level symbol in corpus_status
    assert "computed" not in dir(corpus_status)
    assert "registered" not in dir(corpus_status)
    assert "predicted" not in dir(corpus_status)


# ──────────────────────────────────────────────────────────────────────
# Section 6 — engine invariants
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module", params=list(PUBLISHED_CORPORA))
def published_corpus_vector_dates(published_corpus_name) -> list[str]:
    vectors = load_corpus(published_corpus_name)
    return [v.get("gregorian") or v.get("input", {}).get("date") for v in vectors]


def test_engine_produces_internal_consistency_for_each_published_corpus_date(
    published_corpus_name, published_corpus_vector_dates
):
    """even though the published corpora are quarantined, the engine
    must still produce internally consistent output for the dates
    they cover. quarantine means 'not authoritative', not 'engine
    output is broken'."""
    for date_str in published_corpus_vector_dates:
        if not date_str:
            continue
        try:
            date = _dt.date.fromisoformat(date_str)
        except ValueError:
            continue
        result = compose_day(date)
        assert result.gregorian == date.isoformat()
        assert result.ruleset
        assert result.saka
        assert result.pawukon
        assert result.wewaran
        assert isinstance(result.rahinan, list)


def test_epoch_anchor():
    """the engine's epoch anchor: 1981-08-23 should map to Wuku Sinta, day 1.

    This is the single most critical test in the corpus: if this fails, the
    engine's pawukon positioning will be off by some number of days for
    every date, and no further vector will match.
    """
    date = _dt.date(1981, 8, 23)
    result = compose_day(date)
    assert result.pawukon["position_in_cycle"] == 1
    assert result.pawukon["wuku_idx"] == 1
    assert result.pawukon["wuku_name"] == "Sinta"
    assert result.pawukon["wuku_day"] == 1
    assert result.wewaran["pancawara_name"] == "Paing"
    assert result.wewaran["saptawara_name"] == "Redite"
    assert result.ruleset == "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"


def test_cycle_completes_at_210():
    """1981-08-23 + 210 days should map back to position 1."""
    start = _dt.date(1981, 8, 23)
    end = start + _dt.timedelta(days=210)
    result = compose_day(end)
    assert result.pawukon["position_in_cycle"] == 1, f"expected 1, got {result.pawukon}"
    assert result.pawukon["wuku_idx"] == 1


def test_ruleset_constant():
    """the ruleset version is stable."""
    from dewatacalendar.rulesets import RULESET_VERSION
    assert RULESET_VERSION
    assert RULESET_VERSION.startswith("pawukon-v")
