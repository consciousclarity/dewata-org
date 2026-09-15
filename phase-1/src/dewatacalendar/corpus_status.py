"""corpus evidence status — two-dimensional verification + eligibility.

This module implements the corpus-evidence-status sidecar pattern called
for by PROTOCOL v1.0 §2.4 (artifact evidence standard). The principle:

    preserved != trusted

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
  VERIFIED + ELIGIBLE      → may satisfy the gate
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

## gate predicate

`can_satisfy_validation_gate(record) -> bool` returns True iff
`record.verification_status == "VERIFIED"` AND
`record.reference_eligibility == "ELIGIBLE"`. All other
combinations return False.

the predicate is the single point at which corpus authority is
enforced. any code path that:
  - claims a corpus as authoritative,
  - cites a corpus to justify a ruleset promotion,
  - presents a corpus value as ground truth,
  - silently copies values from a corpus into a new authoritative
    fixture,

must pass through this predicate. If the corpus is not
VERIFIED + ELIGIBLE, the claim must be downgraded to "historical"
or "diagnostic" and the corpus's status must be reported to the
caller.

## legacy single-axis status

the previous version of this module used a single `CorpusStatus`
enum (UNVERIFIED / NON_AUTHORITATIVE / ATTESTED). that enum is
retained as a derived convenience for callers that don't need the
two-axis detail:

  UNVERIFIED         (UNVERIFIED, INELIGIBLE)
  NON_AUTHORITATIVE  (VERIFIED, INELIGIBLE)
  ATTESTED           (VERIFIED, ELIGIBLE)

callers that want the full detail should use CorpusRecord and the
two-axis gate predicate directly.
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


# legacy single-axis status — derived from the two-axis combination
class CorpusStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"            # (UNVERIFIED, INELIGIBLE)
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"  # (VERIFIED, INELIGIBLE)
    ATTESTED = "ATTESTED"              # (VERIFIED, ELIGIBLE)

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
class CorpusRecord:
    """full two-axis record for a corpus, loaded from STATUS.json.

    `verification_status` and `reference_eligibility` are the two
    axes. `authority_basis` is optional metadata. `citation_keys`
    lists the citation keys present in the corpus file. `reason`
    records why this corpus was classified as it was.
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

    @property
    def legacy_status(self) -> CorpusStatus:
        """single-axis legacy view (for callers that don't need the
        two-axis detail)."""
        return CorpusStatus.from_axes(
            self.verification_status, self.reference_eligibility,
        )

    @property
    def may_satisfy_validation_gate(self) -> bool:
        return can_satisfy_validation_gate(self)


def can_satisfy_validation_gate(record: CorpusRecord | VerificationStatus | ReferenceEligibility | str | None) -> bool:
    """return True iff the input may satisfy an independent-reference
    validation gate for calendar correctness.

    accepts:
      - a CorpusRecord
      - None (no record — fail closed)
      - a single-axis CorpusStatus (legacy)
      - a VerificationStatus (treats as the verification axis only;
        cannot satisfy on its own — fails closed)
      - a ReferenceEligibility (treats as the eligibility axis only;
        cannot satisfy on its own — fails closed)
      - a string (treated as legacy CorpusStatus)

    gate rule: verification_status == VERIFIED AND
               reference_eligibility == ELIGIBLE

    any unrecognized value fails closed.
    """
    if isinstance(record, CorpusRecord):
        return (
            record.verification_status == VerificationStatus.VERIFIED
            and record.reference_eligibility == ReferenceEligibility.ELIGIBLE
        )
    if isinstance(record, CorpusStatus):
        return record == CorpusStatus.ATTESTED
    if isinstance(record, VerificationStatus):
        # verification axis alone is not enough
        return False
    if isinstance(record, ReferenceEligibility):
        # eligibility axis alone is not enough
        return False
    if isinstance(record, str):
        try:
            return CorpusStatus(record) == CorpusStatus.ATTESTED
        except ValueError:
            return False
    return False


def can_promote_ruleset_using(record: CorpusRecord | CorpusStatus | str) -> bool:
    """return True iff a ruleset promotion may be justified by this
    corpus. ruleset_promotion requires authoritative ground truth;
    only VERIFIED + ELIGIBLE corpora satisfy this.
    """
    return can_satisfy_validation_gate(record)


def can_be_described_as_ground_truth(record: CorpusRecord | CorpusStatus | str) -> bool:
    """return True iff the corpus may be described as ground truth in
    any artifact (release notes, public docs, dispute records).
    """
    return can_satisfy_validation_gate(record)


def can_be_silently_copied_to_authoritative_fixture(record: CorpusRecord | CorpusStatus | str) -> bool:
    """return True iff values from this corpus may be copied into a new
    authoritative fixture without explicit human review.
    """
    return can_satisfy_validation_gate(record)


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
    registered. a directory name does not confer authority.
    """
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
      _corpus_legacy_status:         CorpusStatus (legacy single-axis)
      _corpus_record:                { reason, related_dispute_id,
                                       date_classified,
                                       evidence_review_artifact,
                                       citation_keys }
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
            v2["_corpus_record"] = {
                "reason": record.reason,
                "related_dispute_id": record.related_dispute_id,
                "date_classified": record.date_classified,
                "evidence_review_artifact": record.evidence_review_artifact,
                "citation_keys": list(record.citation_keys),
            }
        else:
            # unknown corpus — fail closed
            v2["_corpus_verification_status"] = VerificationStatus.UNVERIFIED.value
            v2["_corpus_reference_eligibility"] = ReferenceEligibility.INELIGIBLE.value
            v2["_corpus_authority_basis"] = AuthorityBasis.UNKNOWN.value
            v2["_corpus_legacy_status"] = CorpusStatus.UNVERIFIED.value
            v2["_corpus_record"] = {
                "reason": "corpus not registered in STATUS.json; fail-closed",
                "related_dispute_id": None,
                "date_classified": "",
                "evidence_review_artifact": "",
                "citation_keys": [],
            }
        out.append(v2)
    return out
