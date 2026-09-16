"""corpus evidence status — two-dimensional verification + eligibility.

This module implements the corpus-evidence-status sidecar pattern called
for by PROTOCOL v1.0 §2.4 (artifact evidence standard). The principle:

    preserved != trusted
    verified source != accepted rule
    eligible != accepted
    agreement != authority

## the two axes

A corpus's evidence status is the combination of two orthogonal axes:

  axis 1 — verification_status (is the source / citation retrievable?)
    UNVERIFIED   the citation could not be independently verified from
                 this host (book not held, ISBN not retrievable, page
                 cannot be cross-checked, etc.)
    VERIFIED     the source has been fetched / the citation has been
                 confirmed against a retrievable record (the source
                 itself may still be non-authoritative — see axis 2).

  axis 2 — reference_eligibility (may this corpus satisfy an
            independent-reference validation gate for calendar
            correctness?)
    INELIGIBLE   the corpus may inform the work but cannot satisfy
                 an independent-reference validation gate, even if
                 VERIFIED. reasons include:
                   - practitioner / non-academic source
                   - source does not actually cover the claimed
                     calendrical relationship
                   - source is older than the regime it claims to
                     describe
    ELIGIBLE     the corpus may satisfy an independent-reference
                 validation gate for calendar correctness.

A corpus may be:
  VERIFIED + ELIGIBLE      → may satisfy the gate (claim-scoped)
  VERIFIED + INELIGIBLE    → may not satisfy the gate
  UNVERIFIED + ELIGIBLE    → may not satisfy the gate (the citation
                              cannot be verified)
  UNVERIFIED + INELIGIBLE  → may not satisfy the gate

the gate rule is therefore:
    verification_status == VERIFIED AND reference_eligibility == ELIGIBLE

Anything else fails closed. There is no implicit upgrade — a corpus
must be explicitly re-classified through an authority-bearing act.

## optional authority_basis

a corpus may additionally record an authority_basis to explain WHY it
is (or is not) eligible:

  scholarly      academic publication, peer-reviewed or from a
                 recognized scholarly press
  customary      attested by a Balinese customary authority (pemangku,
                 bendesa, etc.)
  institutional  attested by a state institution (university, ministry,
                 heritage body)
  practitioner   practitioner calendar (commercial or community) — may
                 be VERIFIED but is generally INELIGIBLE for
                 authoritative calendar validation
  software_reference  a software implementation that itself cites a
                 verifiable source (the source is what matters, not the
                 software)
  unknown        the basis could not be classified — UNVERIFIED by
                 default

## separation from Dewata's ceremonial provenance ladder

this module governs the **bibliographic / evidence-chain** layer for
conformance corpora. It is NOT a substitute for, and does not affect,
Dewata's ceremonial/record provenance tiers:

  computed     — derived from a deterministic computation, not yet
                  attested (PROTOCOL §2.6)
  registered    — recorded in a Dewata registry; presence-only, not
                  attested
  predicted     — the engine's forward-looking claim about a future
                  value
  verified      — attested by an applicable human or customary authority

those tiers are governed by PROTOCOL §2.6 and they are about CEREMONIAL
records (e.g. a banjar's computation that a given day is a Purnama).
corpus evidence status is about BIBLIOGRAPHIC sources used to validate
the engine's arithmetic. the two namespaces do not interact.

in particular: a corpus's `verification_status: VERIFIED` does NOT
imply `verified` in the ceremonial provenance ladder. the ceremonial
tier requires a human or customary attestation per PROTOCOL §2.6,
which is a separate process.

## gate hierarchy

There are FOUR gates in this module, each with a distinct and narrow
meaning. They are layered from permissive (top) to restrictive (bottom).

### 1. can_satisfy_validation_gate(record, *, claim_id=None) — REFERENCE-LEVEL

Returns True iff:
  - the record is a CorpusRecord (not a legacy enum or string)
  - verification_status == VERIFIED
  - reference_eligibility == ELIGIBLE
  - if claim_id is provided: the claim_id must be in
    `record.eligible_claim_ids`. If `eligible_claim_ids` is empty
    (default for historical records) this fails closed.
  - if claim_id is None: the record's `eligible_claim_ids` may be
    non-empty (i.e. it claims some scope). An empty list fails
    closed even if the two axes pass.

This is the reference-level gate. VERIFIED + ELIGIBLE means: this
source MAY PARTICIPATE in independent-reference validation for the
specific claim(s) it is scoped to. It does NOT mean the source
is sufficient to promote a ruleset, becomes ground truth, or may be
silently copied.

### 2. can_promote_ruleset_using(record, context) — RULESET-PROMOTION-LEVEL

A ruleset promotion requires more than reference validation. It
requires an explicit `RulesetPromotionContext` carrying:
  - component (e.g. "pawukon.epoch")
  - claim_ids (list of claim IDs being promoted)
  - blocking_dispute_ids (list of dispute IDs the caller asserts
    are blocking; the gate checks STATUS.json's structured
    `blocking_disputes_pending` against this)
  - scope_match (bool: every claim_id is in record.eligible_claim_ids)
  - conformance_passed (bool: required conformance tests have
    actually run and passed)
  - governance_authorization_artifact (path or identifier of the
    explicit governance-owner / authorized-human promotion decision)

The gate returns True iff:
  - reference validation passes (gate 1) for the same record + context
  - scope_match is True
  - blocking_dispute_ids is fully enumerated AND every dispute in
    `record.blocking_disputes_pending` is in the caller's enumeration
    AND every dispute in the caller's enumeration that touches the
    component/claims has resolution != "pending"
  - conformance_passed is True
  - governance_authorization_artifact is set and non-empty
  - all six context fields are set (no missing field)

Any missing or False field fails closed. A source record alone
never authorizes promotion.

### 3. can_be_described_as_ground_truth(record) — DEPRECATED, FAIL CLOSED

Ground truth designation requires an explicit accepted-rule mechanism
with appropriate human/governance authority. This module does not
implement such a mechanism. Until one exists with appropriate
authority, this gate returns False unconditionally for every input
including CorpusRecord.

Use the following vocabulary instead:
  - eligible reference
  - supporting evidence
  - independently verified source
  - accepted rule
  - attested record

Do not allow software to convert the first three into the latter two.

### 4. can_be_silently_copied_to_authoritative_fixture(record) — FAIL CLOSED

This gate returns False unconditionally. There is no condition under
which evidence may be silently promoted into an authoritative fixture.
If values are intentionally adopted later, an explicit reviewed
operation with provenance is required.

## legacy single-axis status

the previous version of this module used a single `CorpusStatus`
enum (UNVERIFIED / NON_AUTHORITATIVE / ATTESTED). that enum is
retained as a derived convenience for deserialization / backward
compatibility, BUT:

  - it is marked deprecated
  - it MUST NOT satisfy can_satisfy_validation_gate on its own
  - it MUST NOT satisfy can_promote_ruleset_using
  - it MUST NOT satisfy can_be_described_as_ground_truth
  - it MUST NOT satisfy can_be_silently_copied_to_authoritative_fixture

Modern callers must supply the explicit two-axis CorpusRecord.

## structured scope and disputes

Each CorpusRecord now carries:
  - `eligible_claim_ids`: tuple of claim IDs the corpus is explicitly
    scoped to support (e.g. "CALC-005"). An empty tuple means
    "no explicit scope" and fails closed on claim-scoped queries.
  - `blocking_disputes_pending`: tuple of dispute IDs that are
    blocking and pending resolution. These are checked by
    can_promote_ruleset_using.

These are STRUCTURED fields read from STATUS.json. Free-text
`scope_limitations` and the manually-entered boolean
`may_justify_ruleset_promotion` are documentation only and are NOT
consulted by any gate function.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


CONFORMANCE_ROOT = Path(__file__).resolve().parent.parent.parent / "conformance"
STATUS_MANIFEST_PATH = CONFORMANCE_ROOT / "STATUS.json"
STATUS_SCHEMA_DOC = CONFORMANCE_ROOT / "STATUS.schema.md"


class VerificationStatus(str, Enum):
    """axis 1 — is the source / citation retrievable?"""
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class ReferenceEligibility(str, Enum):
    """axis 2 — may this corpus satisfy an independent-reference
    validation gate for calendar correctness?"""
    INELIGIBLE = "INELIGIBLE"
    ELIGIBLE = "ELIGIBLE"


class AuthorityBasis(str, Enum):
    """optional explanation of WHY a corpus is (or is not) eligible"""
    SCHOLARLY = "scholarly"
    CUSTOMARY = "customary"
    INSTITUTIONAL = "institutional"
    PRACTITIONER = "practitioner"
    SOFTWARE_REFERENCE = "software_reference"
    UNKNOWN = "unknown"


# legacy single-axis status — DEPRECATED. retained only for
# deserialization / backward compatibility. MUST NOT authorize any
# modern gate.
class CorpusStatus(str, Enum):
    """DEPRECATED single-axis status enum.

    retained for backward compatibility with deserialization of legacy
    STATUS.json entries. MUST NOT satisfy can_satisfy_validation_gate,
    can_promote_ruleset_using, can_be_described_as_ground_truth, or
    can_be_silently_copied_to_authoritative_fixture. modern callers
    must use CorpusRecord with the two-axis model.
    """
    UNVERIFIED = "UNVERIFIED"            # (UNVERIFIED, INELIGIBLE)
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"  # (VERIFIED, INELIGIBLE)
    ATTESTED = "ATTESTED"              # (VERIFIED, ELIGIBLE) — DEPRECATED

    @property
    def is_deprecated(self) -> bool:
        """the entire enum is deprecated; this is a convenience."""
        return True

    @classmethod
    def from_axes(
        cls, verification: VerificationStatus, eligibility: ReferenceEligibility,
    ) -> "CorpusStatus":
        if verification == VerificationStatus.UNVERIFIED:
            return cls.UNVERIFIED
        # VERIFIED
        if eligibility == ReferenceEligibility.ELIGIBLE:
            return cls.ATTESTED
        return cls.NON_AUTHORITATIVE


@dataclass(frozen=True)
class RulesetPromotionContext:
    """explicit promotion context.

    every field is required. any missing field fails closed in
    can_promote_ruleset_using.

    fields:
      component:                     target component (e.g. "pawukon.epoch")
      claim_ids:                     tuple of claim IDs being promoted
      blocking_dispute_ids:          tuple of dispute IDs the caller
                                     asserts are blocking (the gate
                                     checks STATUS.json's structured
                                     blocking_disputes_pending
                                     against this enumeration)
      scope_match:                   bool: every claim_id is in
                                     record.eligible_claim_ids
      conformance_passed:            bool: required conformance tests
                                     have actually run and passed
      governance_authorization_artifact:  identifier of the explicit
                                     governance-owner / authorized-human
                                     promotion decision (path, URL,
                                     commit SHA, or signed artifact).
                                     empty string fails closed.
    """
    component: str
    claim_ids: tuple[str, ...]
    blocking_dispute_ids: tuple[str, ...]
    scope_match: bool
    conformance_passed: bool
    governance_authorization_artifact: str

    def is_complete(self) -> bool:
        """return True iff every required field is set to a non-empty value.

        an empty claim_ids list or empty blocking_dispute_ids list is
        considered set-but-empty and FAIL CLOSED (the gate cannot
        verify scope coverage without claim IDs and cannot enumerate
        blocking disputes without an enumeration).
        """
        if not self.component:
            return False
        if not self.claim_ids:
            return False
        # blocking_dispute_ids may legitimately be empty if the caller
        # has explicitly enumerated the universe of blocking disputes
        # and found none. treat empty as a valid enumeration ONLY if
        # the caller also confirms scope_match.
        if not isinstance(self.scope_match, bool):
            return False
        if not isinstance(self.conformance_passed, bool):
            return False
        if not self.governance_authorization_artifact:
            return False
        return True


@dataclass(frozen=True)
class CorpusRecord:
    """full two-axis record for a corpus, loaded from STATUS.json.

    `verification_status` and `reference_eligibility` are the two
    axes. `authority_basis` is optional metadata. `citation_keys`
    lists the citation keys present in the corpus file. `reason`
    records why this corpus was classified as it was.

    structured scope/dispute fields (loaded from STATUS.json):
      `eligible_claim_ids`:        tuple of claim IDs the corpus is
                                    explicitly scoped to support. empty
                                    tuple means "no explicit scope" and
                                    fails closed on claim-scoped queries.
      `blocking_disputes_pending`: tuple of dispute IDs that are
                                    blocking and pending resolution.
                                    checked by can_promote_ruleset_using.
    """
    corpus_basename: str
    corpus_file: str
    corpus_class: str
    verification_status: VerificationStatus
    reference_eligibility: ReferenceEligibility
    authority_basis: AuthorityBasis
    reason: str
    related_dispute_id: str | None
    date_classified: str
    evidence_review_artifact: str
    citation_keys: tuple[str, ...] = field(default_factory=tuple)
    preserved: bool = True
    eligible_claim_ids: tuple[str, ...] = field(default_factory=tuple)
    blocking_disputes_pending: tuple[str, ...] = field(default_factory=tuple)

    @property
    def legacy_status(self) -> CorpusStatus:
        """single-axis legacy view (for callers that don't need the
        two-axis detail). DEPRECATED; modern callers should use
        verification_status and reference_eligibility directly."""
        return CorpusStatus.from_axes(
            self.verification_status, self.reference_eligibility,
        )

    @property
    def may_satisfy_validation_gate(self) -> bool:
        """DEPRECATED convenience property. modern callers should use
        can_satisfy_validation_gate() directly with claim scope."""
        return can_satisfy_validation_gate(self)


def can_satisfy_validation_gate(
    record: Any,
    *,
    claim_id: str | None = None,
) -> bool:
    """return True iff `record` may satisfy an independent-reference
    validation gate for `claim_id`.

    accepts:
      - a CorpusRecord (modern)
      - None (no record — fail closed)
      - legacy CorpusStatus, VerificationStatus, ReferenceEligibility,
        or string (deprecated — fail closed; modern callers must use
        a CorpusRecord with explicit two-axis state and claim scope)

    gate rule (CorpusRecord path):
      - verification_status == VERIFIED
      - reference_eligibility == ELIGIBLE
      - eligible_claim_ids must be non-empty (a corpus that does not
        declare ANY scope fails closed — there is no claim it can
        validate)
      - if claim_id is provided: claim_id must be in
        record.eligible_claim_ids (fail closed if not in scope)

    any other input (legacy enum, string, None) fails closed.

    a True return value is the reference-level gate: this source may
    PARTICIPATE in independent-reference validation for the specific
    claim (or any of its declared scope). it does NOT authorize
    ruleset promotion, ground-truth designation, or silent fixture
    copying.
    """
    if not isinstance(record, CorpusRecord):
        # legacy enum, string, None, or anything else — fail closed.
        # modern callers must use CorpusRecord.
        return False

    if record.verification_status != VerificationStatus.VERIFIED:
        return False
    if record.reference_eligibility != ReferenceEligibility.ELIGIBLE:
        return False

    # claim-scope enforcement: a corpus that does not declare any
    # explicit eligible_claim_ids has no scope and cannot satisfy any
    # gate. a corpus that declares scope satisfies an unscoped gate
    # (claim_id=None) iff its scope is non-empty; satisfies a claim-
    # scoped gate iff the specific claim_id is in its declared scope.
    if not record.eligible_claim_ids:
        return False
    if claim_id is not None and claim_id not in record.eligible_claim_ids:
        return False

    return True


def can_promote_ruleset_using(
    record: Any,
    context: RulesetPromotionContext | None = None,
) -> bool:
    """return True iff a ruleset promotion may be justified by this
    corpus + this explicit context.

    ruleset promotion requires authoritative ground truth AND an
    authorized promotion decision. A source record alone is never
    sufficient. This gate fails closed unless ALL of the following
    are True:

      - context is a RulesetPromotionContext with every field set
        (RulesetPromotionContext.is_complete() returns True)
      - can_satisfy_validation_gate(record, claim_id=...) returns True
        for the claims in the context (callers must invoke this gate
        with the appropriate claim_id; this function checks scope_match
        in the context to enforce it)
      - scope_match in the context is True
      - blocking_disputes_pending on the record is fully covered by
        the caller's blocking_dispute_ids enumeration: every dispute
        in record.blocking_disputes_pending must be in
        context.blocking_dispute_ids (the caller is asserting they
        have considered each blocking dispute)
      - conformance_passed in the context is True
      - governance_authorization_artifact in the context is non-empty

    any missing field, any unresolved blocking dispute not in the
    caller's enumeration, or any False value fails closed.

    Until a complete promotion-context mechanism exists across the
    codebase, this gate returns False unconditionally for every
    caller — a source record alone must never authorize promotion.
    """
    # fail closed if no context supplied
    if context is None:
        return False
    if not context.is_complete():
        return False

    # fail closed if record is not a CorpusRecord
    if not isinstance(record, CorpusRecord):
        return False

    # every claim_id in the context must satisfy reference validation
    for claim_id in context.claim_ids:
        if not can_satisfy_validation_gate(record, claim_id=claim_id):
            return False

    # caller must have asserted scope match
    if not context.scope_match:
        return False

    # conformance tests must have actually passed
    if not context.conformance_passed:
        return False

    # governance authorization must be set
    if not context.governance_authorization_artifact:
        return False

    # every blocking dispute in the record must be enumerated in the
    # caller's context.blocking_dispute_ids
    record_blocking = set(record.blocking_disputes_pending)
    context_blocking = set(context.blocking_dispute_ids)
    if not record_blocking.issubset(context_blocking):
        return False

    return True


def can_be_described_as_ground_truth(record: Any) -> bool:
    """return False unconditionally.

    ground-truth designation requires an explicit accepted-rule
    mechanism with appropriate human/governance authority. this module
    does not implement such a mechanism. until one exists, this gate
    is fail-closed for every input including CorpusRecord.

    callers should use the following vocabulary instead:
      - eligible reference
      - supporting evidence
      - independently verified source
      - accepted rule
      - attested record
    do not allow software to convert the first three into the latter two.
    """
    return False


def can_be_silently_copied_to_authoritative_fixture(record: Any) -> bool:
    """return False unconditionally.

    there is no condition under which evidence may be silently promoted
    into an authoritative fixture. if values are intentionally adopted
    later, an explicit reviewed operation with provenance is required.

    preserved != trusted
    eligible != accepted
    verified source != accepted rule
    agreement != authority
    """
    return False


def load_status_manifest() -> dict[str, Any]:
    """load the corpus STATUS.json sidecar manifest.

    raises FileNotFoundError if the manifest does not exist.
    """
    if not STATUS_MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"corpus status manifest not found: {STATUS_MANIFEST_PATH}. "
            "this manifest is required for any corpus load under PROTOCOL v1.0."
        )
    return json.loads(STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def corpus_record_for(corpus_basename: str) -> CorpusRecord | None:
    """return the full two-axis record for a corpus, or None if not
    registered. a directory name does not confer authority."""
    try:
        manifest = load_status_manifest()
    except FileNotFoundError:
        return None
    entry = manifest.get("corpora", {}).get(corpus_basename)
    if entry is None:
        return None
    return _record_from_entry(corpus_basename, entry)


def _record_from_entry(corpus_basename: str, entry: dict[str, Any]) -> CorpusRecord:
    """parse a STATUS.json entry into a CorpusRecord."""
    vs = entry.get("verification_status", "UNVERIFIED")
    re_ = entry.get("reference_eligibility", "INELIGIBLE")
    ab = entry.get("authority_basis", "unknown")
    try:
        v_enum = VerificationStatus(vs)
    except ValueError:
        v_enum = VerificationStatus.UNVERIFIED
    try:
        r_enum = ReferenceEligibility(re_)
    except ValueError:
        r_enum = ReferenceEligibility.INELIGIBLE
    try:
        a_enum = AuthorityBasis(ab)
    except ValueError:
        a_enum = AuthorityBasis.UNKNOWN
    return CorpusRecord(
        corpus_basename=corpus_basename,
        corpus_file=entry.get("corpus_file", ""),
        corpus_class=entry.get("corpus_class", "unverified"),
        verification_status=v_enum,
        reference_eligibility=r_enum,
        authority_basis=a_enum,
        reason=entry.get("reason", ""),
        related_dispute_id=entry.get("related_dispute_id"),
        date_classified=entry.get("date_classified", ""),
        evidence_review_artifact=entry.get("evidence_review_artifact", ""),
        citation_keys=tuple(entry.get("citation_keys_present_in_corpus", [])),
        preserved=bool(entry.get("preserved", True)),
        eligible_claim_ids=tuple(entry.get("eligible_claim_ids", [])),
        blocking_disputes_pending=tuple(entry.get("blocking_disputes_pending", [])),
    )


def annotate_vectors_with_status(
    vectors: list[dict[str, Any]], corpus_basename: str,
) -> list[dict[str, Any]]:
    """return a copy of `vectors` with each vector annotated with the
    corpus's two-axis record. does not mutate the input.

    annotation fields per vector:
      _corpus_verification_status:  VerificationStatus value
      _corpus_reference_eligibility: ReferenceEligibility value
      _corpus_authority_basis:       AuthorityBasis value
      _corpus_legacy_status:         CorpusStatus (legacy single-axis,
                                     DEPRECATED — included for backward
                                     compatibility only)
      _corpus_eligible_claim_ids:    tuple of structured claim IDs
      _corpus_blocking_disputes:     tuple of structured dispute IDs
      _corpus_record:                { reason, related_dispute_id,
                                       date_classified,
                                       evidence_review_artifact,
                                       citation_keys,
                                       eligible_claim_ids,
                                       blocking_disputes_pending }
    """
    record = corpus_record_for(corpus_basename)
    out: list[dict[str, Any]] = []
    for v in vectors:
        v2 = dict(v)
        if record is not None:
            v2["_corpus_verification_status"] = record.verification_status.value
            v2["_corpus_reference_eligibility"] = record.reference_eligibility.value
            v2["_corpus_authority_basis"] = record.authority_basis.value
            v2["_corpus_legacy_status"] = record.legacy_status.value
            v2["_corpus_eligible_claim_ids"] = list(record.eligible_claim_ids)
            v2["_corpus_blocking_disputes"] = list(record.blocking_disputes_pending)
            v2["_corpus_record"] = {
                "reason": record.reason,
                "related_dispute_id": record.related_dispute_id,
                "date_classified": record.date_classified,
                "evidence_review_artifact": record.evidence_review_artifact,
                "citation_keys": list(record.citation_keys),
                "eligible_claim_ids": list(record.eligible_claim_ids),
                "blocking_disputes_pending": list(record.blocking_disputes_pending),
            }
        else:
            # unknown corpus — fail closed
            v2["_corpus_verification_status"] = VerificationStatus.UNVERIFIED.value
            v2["_corpus_reference_eligibility"] = ReferenceEligibility.INELIGIBLE.value
            v2["_corpus_authority_basis"] = AuthorityBasis.UNKNOWN.value
            v2["_corpus_legacy_status"] = CorpusStatus.UNVERIFIED.value
            v2["_corpus_eligible_claim_ids"] = []
            v2["_corpus_blocking_disputes"] = []
            v2["_corpus_record"] = {
                "reason": "corpus not registered in STATUS.json; fail-closed",
                "related_dispute_id": None,
                "date_classified": "",
                "evidence_review_artifact": "",
                "citation_keys": [],
                "eligible_claim_ids": [],
                "blocking_disputes_pending": [],
            }
        out.append(v2)
    return out
