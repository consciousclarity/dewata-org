"""corpus authority status — quarantine mechanism for unverified corpora.

This module implements the authority-status sidecar pattern called
for by the gap analysis under PROTOCOL v1.0 §2.4 (artifact evidence
standard). The principle is:

    preserved != trusted

A corpus under conformance/published/ may be:
  - historically cited (e.g. Cunningham 1994, Igarashi 1999) but
    not independently retrievable from this host;
  - sourced from a page on the open web (e.g. kalenderbali.org) but
    not from a peer-reviewed publication;
  - transcribed from a printed source (future case) but not yet
    cross-validated by a named authority.

Such corpora may STILL be loaded for historical comparison and may
STILL produce diagnostic output. They may NOT satisfy an independent-
reference validation gate. They may NOT justify a ruleset promotion.
They may NOT be described as published/verified ground truth. Their
values must not be silently copied into new authoritative fixtures.

A directory name must not confer authority.

## sidecar manifest format

`phase-1/conformance/STATUS.json` (sibling of `published/`) records the
authority status of each corpus file. The format is:

    {
      "schema_version": "1.0",
      "last_modified": "<ISO8601>",
      "corpora": {
        "<corpus_basename>": {
          "corpus_file": "<rel path>",
          "corpus_class": "published | unverified | ground-truth",
          "status": "UNVERIFIED | NON_AUTHORITATIVE | ATTESTED",
          "reason": "<free text, brief>",
          "related_dispute_id": "<DISPUTE-* id, if any>",
          "date_classified": "<ISO8601>",
          "evidence_review_artifact": "<rel path to the artifact that caused classification>",
          "citation_keys_present_in_corpus": ["<AuthorYearShortTitle>", ...]
        },
        ...
      }
    }

`status` values and their semantics:

  UNVERIFIED         — the source citation in the corpus could not be
                       independently verified; the corpus is preserved
                       for provenance but not loadable as authority.
  NON_AUTHORITATIVE  — the source is verified (e.g. an open-web page
                       that returns 200 with verifiable content) but
                       the source itself is not authoritative (e.g. a
                       practitioner calendar, a Wikipedia article).
  ATTESTED           — the source is verified AND authoritative; the
                       corpus may satisfy validation gates. No
                       corpus currently has this status.

## gate function

`can_satisfy_validation_gate(status) -> bool` returns True ONLY for
status == "ATTESTED". All other statuses return False.

The validation-gate predicate is the single point at which a corpus's
authority status is enforced. Any code path that:
  - claims a corpus as authoritative,
  - cites a corpus to justify a ruleset promotion,
  - presents a corpus value as ground truth,

must pass through this predicate. If the corpus is not ATTESTED, the
claim must be downgraded to "historical" or "diagnostic" and the
corpus's status must be reported to the caller.

This module is the mechanism — not a documentation claim. The Python
functions here are what `cross_validation`, `conformance`, `cli`, and
any future `ruleset_promotion` machinery must call.

the policy precedence for this mechanism is documented in PROTOCOL
v1.0 §9.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any


CONFORMANCE_ROOT = Path(__file__).resolve().parent.parent.parent / "conformance"
STATUS_MANIFEST_PATH = CONFORMANCE_ROOT / "STATUS.json"
STATUS_SCHEMA_DOC = CONFORMANCE_ROOT / "STATUS.schema.md"


class CorpusStatus(str, Enum):
    """authority status of a conformance corpus file.

    string values match the schema in STATUS.json. do NOT add new
    statuses without updating PROTOCOL §2.4 and the gap analysis.
    """

    UNVERIFIED = "UNVERIFIED"
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"
    ATTESTED = "ATTESTED"


class CorpusClass(str, Enum):
    """class of a conformance corpus — independent of its status.

    a corpus's class describes what kind of artifact it is; its
    status describes whether it currently satisfies an authority
    gate. the two are tracked separately so a corpus can move
    between statuses without losing its class.
    """

    PUBLISHED = "published"          # published academic / reference work
    UNVERIFIED = "unverified"        # cited but not retrievable from this host
    GROUND_TRUTH = "ground-truth"    # transcribed printed-calendar ground truth


# values that satisfy an independent-reference validation gate.
# only ATTESTED corpora pass the gate. any other status fails closed.
_GATE_PASSING_STATUSES: frozenset[CorpusStatus] = frozenset({CorpusStatus.ATTESTED})


def can_satisfy_validation_gate(status: CorpusStatus | str) -> bool:
    """return True iff `status` is in the set of statuses that satisfy
    an independent-reference validation gate.

    per the gap analysis (Finding 5) and PROTOCOL §2.4, only ATTESTED
    corpora pass. the function fails closed for any unrecognized
    status — unrecognized statuses are treated as not-authoritative.
    """
    if isinstance(status, str):
        try:
            status = CorpusStatus(status)
        except ValueError:
            return False
    return status in _GATE_PASSING_STATUSES


def can_promote_ruleset_using(corpus_status: CorpusStatus | str) -> bool:
    """return True iff a ruleset promotion may be justified by a
    corpus with this status.

    ruleset promotion requires authoritative ground truth. only
    ATTESTED corpora may justify promotion. UNVERIFIED and
    NON_AUTHORITATIVE corpora may inform the work but may not
    justify the promotion itself.
    """
    return can_satisfy_validation_gate(corpus_status)


def can_be_described_as_ground_truth(corpus_status: CorpusStatus | str) -> bool:
    """return True iff the corpus may be described as ground truth in
    any artifact (release notes, public docs, dispute records).

    ATTESTED corpora may be described as ground truth. UNVERIFIED and
    NON_AUTHORITATIVE corpora must be described as "historical",
    "diagnostic", or "unverified" instead.
    """
    return can_satisfy_validation_gate(corpus_status)


def can_be_silently_copied_to_authoritative_fixture(corpus_status: CorpusStatus | str) -> bool:
    """return True iff values from this corpus may be copied into a new
    authoritative fixture without explicit human review.

    per the gap analysis: "their values must not be silently copied
    into new authoritative fixtures." only ATTESTED corpora satisfy
    this. any other corpus requires per-value human review before
    promotion to authoritative fixture.
    """
    return can_satisfy_validation_gate(corpus_status)


def load_status_manifest() -> dict[str, Any]:
    """load the corpus STATUS.json sidecar manifest.

    raises FileNotFoundError if the manifest does not exist. callers
    that need to handle a missing manifest (e.g. legacy code paths
    before this module existed) should check for the file first.
    """
    if not STATUS_MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"corpus status manifest not found: {STATUS_MANIFEST_PATH}. "
            "this manifest is required for any corpus load under PROTOCOL v1.0."
        )
    return json.loads(STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def corpus_status_for(corpus_basename: str) -> CorpusStatus:
    """return the authority status of a corpus by its basename
    (e.g. 'cunningham_1994').

    if the manifest is present and the basename is registered, the
    declared status is returned. if the basename is not registered,
    the function fails closed and returns UNVERIFIED — a directory
    name does not confer authority.
    """
    try:
        manifest = load_status_manifest()
    except FileNotFoundError:
        return CorpusStatus.UNVERIFIED
    corpora = manifest.get("corpora", {})
    entry = corpora.get(corpus_basename)
    if not entry:
        return CorpusStatus.UNVERIFIED
    status_str = entry.get("status")
    if not status_str:
        return CorpusStatus.UNVERIFIED
    try:
        return CorpusStatus(status_str)
    except ValueError:
        return CorpusStatus.UNVERIFIED


def corpus_record_for(corpus_basename: str) -> dict[str, Any] | None:
    """return the full status record for a corpus, or None if not
    registered. callers may use this to surface reason, related
    dispute, citation keys, etc.
    """
    try:
        manifest = load_status_manifest()
    except FileNotFoundError:
        return None
    return manifest.get("corpora", {}).get(corpus_basename)


def annotate_vectors_with_status(
    vectors: list[dict[str, Any]], corpus_basename: str,
) -> list[dict[str, Any]]:
    """return a copy of `vectors` with each vector annotated with the
    corpus's authority status. does not mutate the input.

    the annotation is added as the `_corpus_status` field per vector.
    downstream consumers should read this field rather than asking
    the gate directly so that per-vector classification is preserved.
    """
    status = corpus_status_for(corpus_basename)
    record = corpus_record_for(corpus_basename)
    out: list[dict[str, Any]] = []
    for v in vectors:
        v2 = dict(v)
        v2["_corpus_status"] = status.value
        if record is not None:
            v2["_corpus_record"] = {
                "reason": record.get("reason"),
                "related_dispute_id": record.get("related_dispute_id"),
                "date_classified": record.get("date_classified"),
                "evidence_review_artifact": record.get("evidence_review_artifact"),
            }
        out.append(v2)
    return out
