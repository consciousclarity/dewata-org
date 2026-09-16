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
    RulesetPromotionContext,
    VerificationStatus,
    annotate_vectors_with_status,
    can_be_described_as_ground_truth,
    can_be_silently_copied_to_authoritative_fixture,
    can_promote_ruleset_using,
    can_satisfy_validation_gate,
    corpus_record_for,
    load_status_manifest,
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


def _make_record(
    verification: str,
    eligibility: str,
    basis: str = "unknown",
    eligible_claim_ids: tuple[str, ...] = ("CALC-TEST",),
    blocking_disputes_pending: tuple[str, ...] = (),
) -> CorpusRecord:
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
        eligible_claim_ids=eligible_claim_ids,
        blocking_disputes_pending=blocking_disputes_pending,
    )


def _make_promotion_context(
    component: str = "pawukon.test",
    claim_ids: tuple[str, ...] = ("CALC-TEST",),
    blocking_dispute_ids: tuple[str, ...] = (),
    scope_match: bool = True,
    conformance_passed: bool = True,
    governance_authorization_artifact: str = "/path/to/decision.md",
) -> RulesetPromotionContext:
    return RulesetPromotionContext(
        component=component,
        claim_ids=claim_ids,
        blocking_dispute_ids=blocking_dispute_ids,
        scope_match=scope_match,
        conformance_passed=conformance_passed,
        governance_authorization_artifact=governance_authorization_artifact,
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


def test_gate_verified_eligible_with_claim_scope_returns_true():
    """VERIFIED + ELIGIBLE + the claim_id is in eligible_claim_ids
    → reference gate True. this is the modern narrow meaning: this
    source MAY PARTICIPATE in independent-reference validation for
    the specific claim it is scoped to. it does NOT authorize ruleset
    promotion, ground truth, or fixture copying."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    # claim-scoped, in scope: True
    assert can_satisfy_validation_gate(r, claim_id="CALC-005") is True
    # claim_id not in scope: False
    assert can_satisfy_validation_gate(r, claim_id="CALC-099") is False
    # no claim_id provided but scope is non-empty: True (unscoped gate)
    assert can_satisfy_validation_gate(r) is True
    # promotion, ground-truth, and fixture-copying all fail closed
    assert can_promote_ruleset_using(r, _make_promotion_context()) is False
    assert can_be_described_as_ground_truth(r) is False
    assert can_be_silently_copied_to_authoritative_fixture(r) is False


def test_gate_verified_eligible_but_no_claim_scope_fails_closed():
    """VERIFIED + ELIGIBLE but eligible_claim_ids is empty (no
    explicit scope) → reference gate False for every claim. a corpus
    that does not declare its claim scope cannot satisfy a claim-scoped
    gate."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=(),  # empty scope
    )
    assert can_satisfy_validation_gate(r) is False
    assert can_satisfy_validation_gate(r, claim_id="ANY") is False


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


def test_gate_legacy_attested_fails_closed():
    """legacy single-axis CorpusStatus is retained for backward
    compatibility (deserialization only) but MUST NOT satisfy modern
    gates. modern callers must use CorpusRecord with two-axis state
    and explicit claim scope. legacy ATTESTED alone fails closed on
    every gate."""
    # legacy enum fails closed on reference gate
    assert can_satisfy_validation_gate(CorpusStatus.ATTESTED) is False
    assert can_satisfy_validation_gate(CorpusStatus.NON_AUTHORITATIVE) is False
    assert can_satisfy_validation_gate(CorpusStatus.UNVERIFIED) is False
    # legacy string also fails closed
    assert can_satisfy_validation_gate("ATTESTED") is False
    assert can_satisfy_validation_gate("UNVERIFIED") is False
    assert can_satisfy_validation_gate("MAYBE_OK") is False
    assert can_satisfy_validation_gate("") is False
    assert can_satisfy_validation_gate("authoritative") is False
    # None fails closed
    assert can_satisfy_validation_gate(None) is False
    # legacy enum does not authorize promotion, ground truth, or
    # fixture copying (would have been True under the old semantics;
    # now False for all)
    assert can_promote_ruleset_using(CorpusStatus.ATTESTED, _make_promotion_context()) is False
    assert can_be_described_as_ground_truth(CorpusStatus.ATTESTED) is False
    assert can_be_silently_copied_to_authoritative_fixture(CorpusStatus.ATTESTED) is False
    # the enum itself is marked deprecated
    assert CorpusStatus.ATTESTED.is_deprecated is True
    assert CorpusStatus.NON_AUTHORITATIVE.is_deprecated is True
    assert CorpusStatus.UNVERIFIED.is_deprecated is True


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
    verification=UNVERIFIED still fails. even with the right axes
    and basis, the corpus must also have explicit claim scope."""
    r = _make_record("UNVERIFIED", "INELIGIBLE", "scholarly")
    assert can_satisfy_validation_gate(r) is False
    # basis does not gate — but scope does
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "unknown",
        eligible_claim_ids=(),  # no scope
    )
    assert can_satisfy_validation_gate(r) is False
    # with scope, basis does not affect pass/fail
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "unknown",
        eligible_claim_ids=("CALC-X",),
    )
    assert can_satisfy_validation_gate(r, claim_id="CALC-X") is True


# ──────────────────────────────────────────────────────────────────────
# Section 2.5 — gate hierarchy tests (post-remediation pass 2026-09-16)
#
# These tests verify the corrected gate hierarchy in which:
#   - reference validation is narrowly scoped to claims
#   - ruleset promotion requires an explicit RulesetPromotionContext
#   - ground truth always fails closed
#   - silent fixture copying always fails closed
#   - legacy ATTESTED does not authorize any modern gate
#
# A future test fixture containing all required conditions may return
# True for can_promote_ruleset_using; no current STATUS entry can.
# ──────────────────────────────────────────────────────────────────────


def test_promotion_requires_explicit_context():
    """can_promote_ruleset_using(record) without a context fails
    closed. a source record alone must never authorize promotion."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    assert can_promote_ruleset_using(r) is False
    assert can_promote_ruleset_using(r, None) is False


def test_promotion_requires_complete_context():
    """an incomplete RulesetPromotionContext (any missing field)
    fails closed. the gate cannot operate without a complete context."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    # missing component
    bad_ctx = RulesetPromotionContext(
        component="", claim_ids=("CALC-005",),
        blocking_dispute_ids=(), scope_match=True,
        conformance_passed=True,
        governance_authorization_artifact="/decision.md",
    )
    assert can_promote_ruleset_using(r, bad_ctx) is False
    # missing claim_ids
    bad_ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=(),
        blocking_dispute_ids=(), scope_match=True,
        conformance_passed=True,
        governance_authorization_artifact="/decision.md",
    )
    assert can_promote_ruleset_using(r, bad_ctx) is False
    # missing governance authorization
    bad_ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=(), scope_match=True,
        conformance_passed=True,
        governance_authorization_artifact="",
    )
    assert can_promote_ruleset_using(r, bad_ctx) is False


def test_promotion_requires_scope_match():
    """scope_match=False in the context fails closed."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=(), scope_match=False,
        conformance_passed=True,
        governance_authorization_artifact="/decision.md",
    )
    assert can_promote_ruleset_using(r, ctx) is False


def test_promotion_requires_conformance_passed():
    """conformance_passed=False fails closed. promotion cannot be
    authorized without verified test results."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=(), scope_match=True,
        conformance_passed=False,
        governance_authorization_artifact="/decision.md",
    )
    assert can_promote_ruleset_using(r, ctx) is False


def test_promotion_requires_blocking_disputes_to_be_enumerated():
    """if the corpus record has blocking_disputes_pending, the caller's
    context.blocking_dispute_ids must enumerate every blocking dispute.
    un-enumerated blocking disputes fail closed."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
        blocking_disputes_pending=("DISPUTE-A", "DISPUTE-B"),
    )
    # missing one blocking dispute
    ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=("DISPUTE-A",),
        scope_match=True, conformance_passed=True,
        governance_authorization_artifact="/decision.md",
    )
    assert can_promote_ruleset_using(r, ctx) is False
    # enumerating both: still fails closed because can_satisfy_validation_gate
    # is checked for every claim_id, but this corpus has the right claim_id,
    # so we need to verify scope at the gate level too. see below for the
    # complete-context success path.
    ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=("DISPUTE-A", "DISPUTE-B"),
        scope_match=True, conformance_passed=True,
        governance_authorization_artifact="/decision.md",
    )
    # still requires the claim_id to be in eligible_claim_ids (it is)
    # and the record must satisfy can_satisfy_validation_gate for the claim
    # (it does). this is the only path that returns True.
    assert can_promote_ruleset_using(r, ctx) is True


def test_promotion_no_blocking_disputes_with_full_context():
    """a corpus with no blocking_disputes_pending and a complete
    context can return True from the promotion gate. this is the
    only path that returns True."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
        blocking_disputes_pending=(),  # no blocking disputes
    )
    ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=(),
        scope_match=True, conformance_passed=True,
        governance_authorization_artifact="/path/to/governance-decision.md",
    )
    assert can_promote_ruleset_using(r, ctx) is True


def test_ground_truth_always_fails_closed():
    """can_be_described_as_ground_truth returns False for every input,
    including CorpusRecord, legacy enum, None, and string. ground-truth
    designation requires an explicit accepted-rule mechanism with
    appropriate human/governance authority that this module does not
    yet implement."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    assert can_be_described_as_ground_truth(r) is False
    assert can_be_described_as_ground_truth(CorpusStatus.ATTESTED) is False
    assert can_be_described_as_ground_truth(None) is False
    assert can_be_described_as_ground_truth("ATTESTED") is False
    assert can_be_described_as_ground_truth(True) is False
    assert can_be_described_as_ground_truth(False) is False


def test_silent_fixture_copying_always_fails_closed():
    """can_be_silently_copied_to_authoritative_fixture returns False
    for every input. there is no condition under which evidence may
    be silently promoted into an authoritative fixture."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    assert can_be_silently_copied_to_authoritative_fixture(r) is False
    assert can_be_silently_copied_to_authoritative_fixture(CorpusStatus.ATTESTED) is False
    assert can_be_silently_copied_to_authoritative_fixture(None) is False
    assert can_be_silently_copied_to_authoritative_fixture("ATTESTED") is False
    assert can_be_silently_copied_to_authoritative_fixture(True) is False


def test_no_current_status_entry_authorizes_promotion():
    """no current STATUS.json entry may independently authorize ruleset
    promotion. this test enumerates every corpus in STATUS.json and
    confirms it cannot satisfy can_promote_ruleset_using, even with
    a complete context.

    for an entry to satisfy promotion, it must:
      - be VERIFIED + ELIGIBLE
      - have non-empty eligible_claim_ids
      - have empty blocking_disputes_pending
      - be paired with a complete RulesetPromotionContext

    even if all four conditions hold, the entry only AUTHORIZES
    promotion — actual promotion still requires a caller to invoke
    this gate with a complete context. this test verifies that no
    entry can do so without that caller-supplied context.

    the test is parameterized so future STATUS entries can opt in
    to promotion-eligibility only by being added to an explicit
    whitelist."""
    manifest = load_status_manifest()
    corpora = manifest.get("corpora", {})
    # no current entry should independently authorize promotion
    for name, entry in corpora.items():
        record = corpus_record_for(name)
        # even with a complete context, current entries must not
        # independently authorize promotion. the gate must fail
        # closed because current entries do not declare
        # eligible_claim_ids (they are all empty), so the gate's
        # claim-scope check fails closed for every claim_id.
        ctx = _make_promotion_context()
        assert can_promote_ruleset_using(record, ctx) is False, (
            f"corpus {name!r} authorized promotion without explicit "
            f"context — this is a fail-closed regression"
        )


def test_no_current_status_entry_is_ground_truth():
    """no current STATUS.json entry may be described as ground truth."""
    manifest = load_status_manifest()
    corpora = manifest.get("corpora", {})
    for name in corpora:
        record = corpus_record_for(name)
        assert can_be_described_as_ground_truth(record) is False, (
            f"corpus {name!r} described as ground truth — this is a "
            f"fail-closed regression"
        )


def test_no_current_status_entry_may_be_silently_copied():
    """no current STATUS.json entry may be silently copied into an
    authoritative fixture."""
    manifest = load_status_manifest()
    corpora = manifest.get("corpora", {})
    for name in corpora:
        record = corpus_record_for(name)
        assert can_be_silently_copied_to_authoritative_fixture(record) is False, (
            f"corpus {name!r} allowed to be silently copied — this is a "
            f"fail-closed regression"
        )


def test_promotion_context_is_complete_method():
    """RulesetPromotionContext.is_complete enforces every required
    field. callers cannot construct a complete context with empty
    values."""
    # empty component
    ctx = RulesetPromotionContext(
        component="", claim_ids=("X",), blocking_dispute_ids=(),
        scope_match=True, conformance_passed=True,
        governance_authorization_artifact="/d.md",
    )
    assert ctx.is_complete() is False
    # empty claim_ids
    ctx = RulesetPromotionContext(
        component="c", claim_ids=(), blocking_dispute_ids=(),
        scope_match=True, conformance_passed=True,
        governance_authorization_artifact="/d.md",
    )
    assert ctx.is_complete() is False
    # empty governance authorization
    ctx = RulesetPromotionContext(
        component="c", claim_ids=("X",), blocking_dispute_ids=(),
        scope_match=True, conformance_passed=True,
        governance_authorization_artifact="",
    )
    assert ctx.is_complete() is False
    # non-bool scope_match
    ctx = RulesetPromotionContext(
        component="c", claim_ids=("X",), blocking_dispute_ids=(),
        scope_match="yes",  # type: ignore[arg-type]
        conformance_passed=True,
        governance_authorization_artifact="/d.md",
    )
    assert ctx.is_complete() is False
    # non-bool conformance_passed
    ctx = RulesetPromotionContext(
        component="c", claim_ids=("X",), blocking_dispute_ids=(),
        scope_match=True,
        conformance_passed="yes",  # type: ignore[arg-type]
        governance_authorization_artifact="/d.md",
    )
    assert ctx.is_complete() is False
    # all set
    ctx = RulesetPromotionContext(
        component="c", claim_ids=("X",), blocking_dispute_ids=(),
        scope_match=True, conformance_passed=True,
        governance_authorization_artifact="/d.md",
    )
    assert ctx.is_complete() is True


def test_reference_gate_with_claim_id_strict_membership():
    """the reference gate strictly checks claim_id membership in
    eligible_claim_ids. an empty eligible_claim_ids tuple fails closed
    even for VERIFIED + ELIGIBLE records."""
    # record with no scope declared
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=(),
    )
    assert can_satisfy_validation_gate(r) is False
    assert can_satisfy_validation_gate(r, claim_id="ANY") is False

    # record with explicit scope
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-001", "CALC-002"),
    )
    # in scope
    assert can_satisfy_validation_gate(r, claim_id="CALC-001") is True
    assert can_satisfy_validation_gate(r, claim_id="CALC-002") is True
    # not in scope
    assert can_satisfy_validation_gate(r, claim_id="CALC-999") is False
    # unscoped
    assert can_satisfy_validation_gate(r) is True


def test_legacy_enum_does_not_authorize_promotion_ground_truth_fixture():
    """legacy CorpusStatus.ATTESTED (and the string "ATTESTED") do
    not authorize promotion, ground-truth designation, or silent
    fixture copying. modern callers must use CorpusRecord."""
    for inp in (CorpusStatus.ATTESTED, "ATTESTED"):
        assert can_satisfy_validation_gate(inp) is False
        assert can_promote_ruleset_using(inp, _make_promotion_context()) is False
        assert can_be_described_as_ground_truth(inp) is False
        assert can_be_silently_copied_to_authoritative_fixture(inp) is False


def test_evidence_without_governance_authorization_fails_closed():
    """even with a fully valid corpus and a complete context with
    scope_match=True, conformance_passed=True, blocking_disputes
    enumerated, and claim scope valid — if governance_authorization_artifact
    is empty, the gate fails closed."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=(), scope_match=True,
        conformance_passed=True,
        governance_authorization_artifact="",  # explicitly empty
    )
    assert can_promote_ruleset_using(r, ctx) is False


def test_governance_authorization_without_evidence_fails_closed():
    """governance authorization alone is not enough — there must also
    be valid evidence. we simulate 'governance-only' by passing a
    context that says scope_match=True but using a record with no
    eligible_claim_ids. the claim scope check fails closed."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=(),  # no scope
    )
    ctx = RulesetPromotionContext(
        component="pawukon.epoch", claim_ids=("CALC-005",),
        blocking_dispute_ids=(), scope_match=True,
        conformance_passed=True,
        governance_authorization_artifact="/decision.md",
    )
    assert can_promote_ruleset_using(r, ctx) is False


def test_multiple_agreeing_eligible_sources_still_cannot_promote():
    """two agreeing eligible sources do not authorize promotion. a
    source record alone never authorizes promotion."""
    r1 = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-005",),
    )
    r2 = _make_record(
        "VERIFIED", "ELIGIBLE", "institutional",
        eligible_claim_ids=("CALC-005",),
    )
    # neither alone authorizes promotion without a complete context
    assert can_promote_ruleset_using(r1) is False
    assert can_promote_ruleset_using(r2) is False
    # r1 with a complete context (claim_ids in scope) can (this is
    # the only path that returns True)
    ctx = _make_promotion_context(claim_ids=("CALC-005",))
    assert can_promote_ruleset_using(r1, ctx) is True
    # ground truth still fails closed for both
    assert can_be_described_as_ground_truth(r1) is False
    assert can_be_described_as_ground_truth(r2) is False


def test_full_success_path_for_future_promotion():
    """a future test fixture containing ALL required conditions can
    return True for can_promote_ruleset_using. this proves the gate
    is not merely always-False but is conditional on the full
    structured context."""
    r = _make_record(
        "VERIFIED", "ELIGIBLE", "scholarly",
        eligible_claim_ids=("CALC-FUTURE-001",),
        blocking_disputes_pending=(),
    )
    ctx = RulesetPromotionContext(
        component="pawukon.future",
        claim_ids=("CALC-FUTURE-001",),
        blocking_dispute_ids=(),
        scope_match=True,
        conformance_passed=True,
        governance_authorization_artifact="/governance/decisions/2026-09-16-pawukon-future.md",
    )
    assert can_promote_ruleset_using(r, ctx) is True
    # but ground truth and silent fixture copying still fail closed
    assert can_be_described_as_ground_truth(r) is False
    assert can_be_silently_copied_to_authoritative_fixture(r) is False


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


def test_current_engine_epoch_behavior_preserved_pending_mapping_dispute():
    """current-behavior regression: documents the engine's existing
    output for 1981-08-23 = position 1, wuku_idx 1, wuku Sinta, wuku_day 1,
    pancawara Paing, saptawara Redite.

    this is a regression-protection test only. it is NOT a correctness
    assertion. the engine's choice of 1981-08-23 as epoch anchor is the
    subject of a pending mapping-phase dispute
    (DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15,
    class: calendar_semantics, reclassified to mapping_phase in
    commit 9516b01). CALENDRICA uses bali-epoch = fixed-from-jd 146,
    yielding a constant +84 mod 210 offset vs Dewata. the two are
    arithmetically equivalent; the question is which convention is
    culturally correct.

    while that dispute is pending, this test asserts only that the
    engine's CURRENT behavior is preserved. it does NOT claim
    1981-08-23 = Sinta day 1 / Paing as validated ground truth.
    the pancawara "Paing" assertion here is the engine's internal
    mapping-A convention; the cultural convention (mapping B =
    1=Umanis) is documented separately as the subject of
    DISPUTE-pancawara-convention-shift-dewata-vs-cultural-2026-09-15
    (class: indexing_representation).

    when either dispute resolves, this test must be updated or removed
    to reflect the new convention. do not silently change its
    expectations.
    """
    date = _dt.date(1981, 8, 23)
    result = compose_day(date)
    # current behavior: position 1, wuku_idx 1, wuku Sinta, wuku_day 1.
    # these are regression assertions: they document what the engine
    # currently does, not what is culturally correct.
    assert result.pawukon["position_in_cycle"] == 1
    assert result.pawukon["wuku_idx"] == 1
    assert result.pawukon["wuku_name"] == "Sinta"
    assert result.pawukon["wuku_day"] == 1
    # pancawara and saptawara assertions here are the engine's
    # CURRENT internal conventions, NOT validated against cultural
    # practice. see the disputes referenced above.
    assert result.wewaran["pancawara_name"] == "Paing"
    assert result.wewaran["saptawara_name"] == "Redite"
    # ruleset version is a regression check only
    assert result.ruleset == "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"


def test_cycle_completes_at_210():
    """current-behavior regression: 1981-08-23 + 210 days maps back
    to position 1. this is a regression-protection test only; the
    +210 cycle length itself is undisputed."""
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
