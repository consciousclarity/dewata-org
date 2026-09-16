# STATUS.json schema — corpus evidence status registry

This document specifies the schema of `phase-1/conformance/STATUS.json`,
the sidecar manifest that records the **bibliographic / evidence-
chain status** of every conformance corpus file under
`phase-1/conformance/`.

schema version: **3.0**

v3.0 changes from v2.0:
- extended with structured claim-scope and blocking-dispute fields
- gate hierarchy re-architected into four distinct gates with
  different semantics (validation, promotion, ground truth, fixture
  copying)
- legacy `CorpusStatus` enum retained for deserialization only;
  never authorizes a modern gate
- v3.0-post-stabilization (2026-09-16): the reference gate is
  **claim-scoped** and requires an explicit `claim_id`; unscoped
  source-level boolean authority shortcuts are forbidden
- v3.0-post-stabilization (2026-09-16): `can_promote_ruleset_using`
  returns False unconditionally; the executable promotion-authority
  mechanism does not exist yet
- v3.0-post-stabilization (2026-09-16 documentation consistency pass):
  STATUS.schema.md fully rewritten for internal consistency; legacy
  four-gates-are-identical language and obsolete `may_satisfy_validation_gate`
  / `may_be_described_as_ground_truth` source-level boolean fields are
  removed; `/tmp/refs/` policy documented as transient retrieval space
  (not durable evidence storage); Kemendikbud licensing corrected
  (NOT open-content); edysantosa lineage terminology corrected
  (derivative, not independent)

## why a sidecar exists

per PROTOCOL v1.0 §2.4 and the v1.0 gap analysis Finding 5, a
conformance corpus's directory placement (`published/`, `ground-truth/`,
etc.) does NOT confer authority. Authority must be explicit,
per-corpus, and machine-readable so that the cross-validation and
conformance machinery can enforce gates deterministically.

the sidecar exists to:

1. Separate **preservation** (the corpus stays on disk for historical
   evidence) from **authority** (whether the corpus may satisfy a
   validation gate).
2. Make the authority status a first-class field that downstream
   code must consult, not a string check buried in a comment.
3. Distinguish two orthogonal failure modes: the citation cannot be
   retrieved (`UNVERIFIED`) versus the citation exists but the source
   is not authoritative (`INELIGIBLE`).
4. Provide an audit trail: every status entry records who classified
   it, when, on what evidence, and which dispute (if any) it is bound
   to.

## the two-axis model

A corpus's evidence status is the combination of two orthogonal
fields:

### axis 1 — `verification_status` (is the source / citation retrievable?)

| value | meaning |
|---|---|
| `UNVERIFIED` | the citation could not be independently verified from this host (book not held, ISBN not retrievable, page cannot be cross-checked, etc.) |
| `VERIFIED` | the source has been fetched / the citation has been confirmed against a retrievable record (the source itself may still be non-authoritative — see axis 2) |

### axis 2 — `reference_eligibility` (may this corpus support independent-reference validation for calendar correctness?)

| value | meaning |
|---|---|
| `INELIGIBLE` | the corpus may inform the work but cannot satisfy an independent-reference validation gate, even if VERIFIED. reasons include practitioner/non-academic source, source does not actually cover the claimed calendrical relationship, source is older than the regime it claims to describe |
| `ELIGIBLE` | the corpus MAY PARTICIPATE in independent-reference validation for claims within its structured `eligible_claim_ids` scope. An ELIGIBLE flag does NOT automatically grant eligibility for every claim in that corpus — see gate hierarchy below. |

The two axes are **necessary source-level prerequisites** for the
reference gate. They are not sufficient on their own — see gate
hierarchy §1 below.

## optional authority_basis

a corpus may additionally record an authority_basis to explain WHY
it is (or is not) eligible:

| value | meaning |
|---|---|
| `scholarly` | academic publication, peer-reviewed or from a recognized scholarly press |
| `customary` | attested by a Balinese customary authority (pemangku, bendesa, etc.) |
| `institutional` | attested by a state institution (university, ministry, heritage body) |
| `practitioner` | practitioner calendar (commercial or community) — may be VERIFIED but is generally INELIGIBLE for authoritative calendar validation |
| `software_reference` | a software implementation that itself cites a verifiable source (the source is what matters, not the software) |
| `unknown` | the basis could not be classified — UNVERIFIED by default |

## separation from Dewata's ceremonial provenance ladder

this status governs the **bibliographic / evidence-chain** layer for
conformance corpora. It is NOT a substitute for, and does not affect,
Dewata's ceremonial/record provenance tiers:

| tier | meaning | governance |
|---|---|---|
| `computed` | derived from a deterministic computation, not yet attested | PROTOCOL §2.6 |
| `registered` | recorded in a Dewata registry; presence-only, not attested | PROTOCOL §2.6 |
| `predicted` | the engine's forward-looking claim about a future value | PROTOCOL §2.6 |
| `verified` | attested by an applicable human or customary authority | PROTOCOL §2.6 |

those tiers are about CEREMONIAL records (e.g. a banjar's computation
that a given day is a Purnama). corpus evidence status is about
BIBLIOGRAPHIC sources used to validate the engine's arithmetic.
the two namespaces do not interact.

in particular: a corpus's `verification_status: VERIFIED` does NOT
imply `verified` in the ceremonial provenance ladder. the ceremonial
tier requires a human or customary attestation per PROTOCOL §2.6,
which is a separate process.

## gate hierarchy (v3.0 — post-stabilization 2026-09-16)

There are FOUR layered gates in
`phase-1/src/dewatacalendar/corpus_status.py`. They are layered from
most permissive (top) to most restrictive (bottom), and they do NOT
have the same semantics. Each gate answers a different question.

### 1. `can_satisfy_validation_gate(record, *, claim_id)` — REFERENCE-LEVEL, CLAIM-SCOPED

Answers ONLY: "Can source S support claim C?"

Returns True iff every condition holds:
- `claim_id` is not None (the caller MUST supply an explicit claim)
- the record is a `CorpusRecord`
- `verification_status == "VERIFIED"`
- `reference_eligibility == "ELIGIBLE"`
- `eligible_claim_ids` is non-empty
- `claim_id` is present in `eligible_claim_ids`

A True result means the source MAY PARTICIPATE in independent-
reference validation for the specific claim. It does NOT mean:
- the source is sufficient to promote a ruleset
- the source becomes ground truth
- values from the source may be silently copied

Unscoped calls (no `claim_id`) fail closed. There is no source-level
boolean authority shortcut.

### 2. `can_promote_ruleset_using(record, context)` — RULESET-PROMOTION-LEVEL, ALWAYS FAIL-CLOSED

Returns False unconditionally.

Promotion is an authority-bearing action that requires independent
verification of dispute records, blocking-dispute resolution state,
resolver authority, resolution evidence artifacts, affected
claim/component scope, required conformance-run artifacts, explicit
governance authorization, and matching ruleset candidate.

The executable promotion-authority mechanism does not exist yet.
Until it does, this gate is fail-closed for every caller — including
callers that supply a complete `RulesetPromotionContext` with
arbitrary strings as `governance_authorization_artifact`.

`RulesetPromotionContext` is retained only as a future-schema
prototype. It is **NOT YET AUTHORIZATION-BEARING**.

### 3. `can_be_described_as_ground_truth(record)` — ALWAYS FAIL-CLOSED

Returns False unconditionally.

Ground-truth designation requires an explicit accepted-rule mechanism
with appropriate human/governance authority that this module does
not yet implement.

Use the following vocabulary instead:
- eligible reference
- supporting evidence
- independently verified source
- accepted rule
- attested record

Do not allow software to convert the first three into the latter two.

### 4. `can_be_silently_copied_to_authoritative_fixture(record)` — ALWAYS FAIL-CLOSED

Returns False unconditionally. There is no condition under which
evidence may be silently promoted into an authoritative fixture.

## structured scope and dispute fields (schema v3.0)

v3.0 adds two STRUCTURED fields per entry that the gate machinery
reads directly. Free-text `scope_limitations` and the manually-entered
boolean `may_justify_ruleset_promotion` are documentation only and are
NOT consulted by any gate function.

### `eligible_claim_ids` (structured claim scope)

A tuple of claim IDs the corpus is explicitly scoped to support
(e.g. `["CALC-005"]`). An empty tuple means "no explicit scope"
and fails closed on claim-scoped queries.

For every claim in `RulesetPromotionContext.claim_ids`, the corpus
record's `eligible_claim_ids` must contain the same claim ID. This is
enforced by `can_satisfy_validation_gate(record, claim_id=...)`.

### `blocking_disputes_pending` (structured dispute enumeration)

A tuple of dispute IDs that are blocking and pending resolution.
Read by `can_promote_ruleset_using(record, context)` to verify that
the caller's `context.blocking_dispute_ids` enumerates every
blocking dispute. Un-enumerated blocking disputes fail closed.

Per v3.0-post-stabilization (2026-09-16), `can_promote_ruleset_using`
returns False unconditionally regardless of this field. The field
is preserved as structured data for a future executable mechanism.

### `scope_limitations` (free text, DOCUMENTATION ONLY)

A list of free-text strings documenting any claim/region/period
limitations on the corpus's applicability. NOT consulted by any gate
function. Use `eligible_claim_ids` (structured) for any claim-scope
enforcement.

### `may_justify_ruleset_promotion` (boolean, DOCUMENTATION ONLY — DEPRECATED for executable use)

A boolean that was historically used to indicate whether the corpus
might justify a ruleset promotion. Per v3.0-post-stabilization
(2026-09-16) this field is DOCUMENTATION-ONLY and is NOT consulted
by `can_promote_ruleset_using`. Future promotion decisions must
derive from structured artifacts (resolution records, conformance-
run artifacts, governance-authorization artifacts), not from this
boolean. **No duplicated policy boolean should drift away from the
structured model.**

## per-corpus example (v3.0)

```json
{
  "corpora": {
    "example_corpus": {
      "corpus_file": "path/to/evidence/file.json",
      "corpus_class": "primary_evidence",
      "verification_status": "VERIFIED",
      "reference_eligibility": "ELIGIBLE",
      "authority_basis": "scholarly",
      "reason": "...",
      "related_dispute_id": "DISPUTE-...",
      "date_classified": "YYYY-MM-DD",
      "evidence_review_artifact": "path/to/review.md",
      "citation_keys_present_in_corpus": ["..."],
      "preserved": true,
      "eligible_claim_ids": ["CALC-001", "CALC-002"],
      "blocking_disputes_pending": ["DISPUTE-A"],
      "scope_limitations": [
        "free-text limitation, NOT consulted by any gate function"
      ],
      "may_justify_ruleset_promotion": false
    }
  }
}
```

Fields removed in v3.0 (because they implied source-level boolean
authority that is forbidden under the claim-scoped model):
- ~~`may_satisfy_validation_gate`~~ — REMOVED. A source-level boolean
  that claimed "this corpus passes the validation gate" is
  contradicted by the post-stabilization claim-scoped gate.
- ~~`may_be_described_as_ground_truth`~~ — REMOVED. Same reasoning.

Use `verification_status`, `reference_eligibility`, and
`eligible_claim_ids` (the structured fields) instead.

## top-level policy

```
verification_status: a necessary source-level prerequisite. the
  source has been fetched / the citation has been confirmed against
  a retrievable record.

reference_eligibility: a necessary source-level prerequisite. this
  corpus MAY PARTICIPATE in independent-reference validation for
  claims within its structured eligible_claim_ids scope.

actual validation gate (can_satisfy_validation_gate(record, claim_id)):
  returns True iff the source is CorpusRecord, the caller supplies
  an explicit claim_id, the axes are VERIFIED + ELIGIBLE, and
  eligible_claim_ids is non-empty AND claim_id is present in
  eligible_claim_ids. unscoped calls fail closed.

ruleset promotion (can_promote_ruleset_using): DISABLED / FAIL-CLOSED
  today. no caller input can authorize a promotion.

ground-truth designation (can_be_described_as_ground_truth):
  ALWAYS FAIL-CLOSED.

silent authoritative fixture copying
  (can_be_silently_copied_to_authoritative_fixture):
  ALWAYS FAIL-CLOSED.
```

## legacy CorpusStatus (v2.0 deprecated)

the legacy single-axis `CorpusStatus` enum
(`UNVERIFIED`, `NON_AUTHORITATIVE`, `ATTESTED`) is retained for
backward-compatible deserialization only. It is DEPRECATED.

| variant | meaning | modern usage |
|---|---|---|
| `UNVERIFIED` | derived from `(UNVERIFIED, INELIGIBLE)` axes | deserialization only |
| `NON_AUTHORITATIVE` | derived from `(VERIFIED, INELIGIBLE)` axes | deserialization only |
| `ATTESTED` | derived from `(VERIFIED, ELIGIBLE)` axes | deserialization only |

ATTESTED must NEVER satisfy a modern evidence gate:
- it MUST NOT satisfy `can_satisfy_validation_gate` on its own
- it MUST NOT satisfy `can_promote_ruleset_using`
- it MUST NOT satisfy `can_be_described_as_ground_truth`
- it MUST NOT satisfy `can_be_silently_copied_to_authoritative_fixture`

Modern callers must supply the explicit two-axis `CorpusRecord` with
its `eligible_claim_ids` field and an explicit `claim_id` argument.
The legacy enum is convenient only when deserializing older
artifacts; it is **not** an authorization shortcut.

## top-level example (v3.0)

```json
{
  "schema_version": "3.0",
  "last_modified": "YYYY-MM-DDTHH:MM:SSZ",
  "axes": { ... },
  "policy": "...",
  "gate_predicates": {
    "can_satisfy_validation_gate": "...",
    "can_promote_ruleset_using": "...",
    "can_be_described_as_ground_truth": "...",
    "can_be_silently_copied_to_authoritative_fixture": "..."
  },
  "removed_source_level_booleans_2026-09-16": "...",
  "separation_from_ceremonial_tiers": "...",
  "corpora": { ... }
}
```

## how this sidecar changes over time

- A corpus's `(verification_status, reference_eligibility)` may move
  in either axis as evidence is acquired or new evidence undermines
  the source.
- A corpus's status may move from UNVERIFIED → VERIFIED (citation
  found); from INELIGIBLE → ELIGIBLE (citation authority
  established); or in the opposite direction (citation refuted,
  authority withdrawn).
- `eligible_claim_ids` and `blocking_disputes_pending` are STRUCTURED
  fields that the gate machinery reads. They should be added/updated
  through append-only changes, with each change recorded in
  `disputes.json` per PROTOCOL v1.0 §3.2.
- Status transitions are append-only in the audit log (any status
  change should be recorded in `disputes.json` with a new dispute ID
  or as a resolution of an existing dispute).
- the `STATUS.json` file itself may be edited; the sidecar is a
  registry, not an event log. the event log is `disputes.json`.

## relationship to PROTOCOL v1.0

this sidecar is the implementation of the gap analysis Finding 5
remediation (corpus authority quarantine). It is part of the v1.0
PROTOCOL's evidence model (§2.4 artifact evidence standard, §2.7
canonical evidence root, §3 dispute classes including
`bibliographic`).

The v3.0-post-stabilization changes are part of the corrective
evidence-gate + test-integrity pass and the stabilization pass
executed in commits `037e0be` and `53ec52b` on the
`warden/phase2-foundation-20260914` history branch (and preserved in
the clean `integration/governance-evidence-20260916` integration
branch).
