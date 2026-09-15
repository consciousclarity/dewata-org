# STATUS.json schema — corpus evidence status registry

This document specifies the schema of `phase-1/conformance/STATUS.json`,
the sidecar manifest that records the **bibliographic / evidence-
chain status** of every conformance corpus file under
`phase-1/conformance/`.

schema version: **2.0** (introduced when the single-axis `CorpusStatus`
enum was split into two orthogonal axes per PROTOCOL v1.0 §2.4
evidence model).

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
| `VERIFIED`   | the source has been fetched / the citation has been confirmed against a retrievable record |

### axis 2 — `reference_eligibility` (may this corpus satisfy an independent-reference validation gate?)

| value | meaning |
|---|---|
| `INELIGIBLE` | the corpus may inform the work but cannot satisfy an independent-reference validation gate. reasons: practitioner / non-academic source, source does not actually cover the claimed calendrical relationship, source is older than the regime it claims to describe |
| `ELIGIBLE`   | the corpus may satisfy an independent-reference validation gate for calendar correctness |

### optional `authority_basis` (why a corpus is / is not eligible)

| value | meaning |
|---|---|
| `scholarly`         | academic publication, peer-reviewed or from a recognized scholarly press |
| `customary`         | attested by a Balinese customary authority (pemangku, bendesa, etc.) |
| `institutional`     | attested by a state institution (university, ministry, heritage body) |
| `practitioner`      | practitioner calendar (commercial or community) — may be VERIFIED but generally INELIGIBLE for authoritative calendar validation |
| `software_reference` | a software implementation that itself cites a verifiable source (the source is what matters, not the software) |
| `unknown`           | the basis could not be classified — UNVERIFIED by default |

### the gate rule

```
can_satisfy_validation_gate(corpus) =
    verification_status == "VERIFIED"
  AND reference_eligibility == "ELIGIBLE"
```

anything else fails closed. There is no implicit upgrade.

### matrix

| verification | eligibility | gate | semantic |
|---|---|---|---|
| VERIFIED | ELIGIBLE | **passes** | the corpus is a properly cited, authoritative, on-topic source |
| VERIFIED | INELIGIBLE | fails | the source is retrievable but not authoritative for calendar validation |
| UNVERIFIED | ELIGIBLE | fails | the citation cannot be independently retrieved |
| UNVERIFIED | INELIGIBLE | fails | both axes fail closed |

## legacy single-axis status

the previous version of the corpus status used a single `CorpusStatus`
enum (`UNVERIFIED` / `NON_AUTHORITATIVE` / `ATTESTED`). That enum is
retained as a derived convenience for callers that don't need the
two-axis detail:

| legacy | two-axis mapping |
|---|---|
| `UNVERIFIED` | `(UNVERIFIED, INELIGIBLE)` |
| `NON_AUTHORITATIVE` | `(VERIFIED, INELIGIBLE)` |
| `ATTESTED` | `(VERIFIED, ELIGIBLE)` |

callers that want the full detail should use the `CorpusRecord`
dataclass from `phase-1/src/dewatacalendar/corpus_status.py`.

## top-level shape

```
{
  "schema_version": "2.0",
  "last_modified": "<ISO8601>",
  "policy": "<free text>",
  "axes": {
    "verification_status": { "UNVERIFIED": "...", "VERIFIED": "..." },
    "reference_eligibility": { "INELIGIBLE": "...", "ELIGIBLE": "..." },
    "authority_basis": { ... }
  },
  "gate_predicates": { ... },
  "separation_from_ceremonial_tiers": "<free text>",
  "corpora": { ... },
  "enforcement": "<free text>"
}
```

## `corpora` entries

```
"<corpus_basename>": {
  "corpus_file":                "<rel path under the repo root>",
  "corpus_class":               "published | unverified | ground-truth",
  "verification_status":        "UNVERIFIED | VERIFIED",
  "reference_eligibility":      "INELIGIBLE | ELIGIBLE",
  "authority_basis":            "<one of the authority_basis values>",
  "reason":                     "<free text, brief>",
  "related_dispute_id":         "<DISPUTE-* id, or null>",
  "date_classified":            "<YYYY-MM-DD>",
  "evidence_review_artifact":   "<rel path>",
  "citation_keys_present_in_corpus": [
    "<AuthorYearShortTitle>",
    ...
  ],
  "preserved":                  true | false,
  "may_satisfy_validation_gate":        true | false,
  "may_justify_ruleset_promotion":      true | false,
  "may_be_described_as_ground_truth":   true | false
}
```

the three `may_*` fields are derived from `verification_status` and
`reference_eligibility` for fast machine-check; they are also
asserted explicitly so a future schema update that changes the
predicates does not silently change the recorded behavior.

## gate predicates

the gate predicates are functions, not just JSON fields. The Python
implementation lives in
`phase-1/src/dewatacalendar/corpus_status.py`:

- `can_satisfy_validation_gate(record) -> bool`
- `can_promote_ruleset_using(record) -> bool`
- `can_be_described_as_ground_truth(record) -> bool`
- `can_be_silently_copied_to_authoritative_fixture(record) -> bool`

all four are `(verification == VERIFIED) AND (eligibility == ELIGIBLE)`.
any other combination returns False. Unrecognized values fail closed.

## how downstream code MUST use this

any code path that:

- claims a corpus as authoritative,
- cites a corpus to justify a ruleset promotion,
- presents a corpus value as ground truth,
- silently copies values from a corpus into a new authoritative fixture

MUST pass through the gate predicates. If the corpus's axes do not
satisfy `VERIFIED + ELIGIBLE`, the claim must be downgraded to
"historical" or "diagnostic" and the corpus's status must be reported
to the caller.

the cross-validation machinery annotates every loaded vector with
`_corpus_verification_status`, `_corpus_reference_eligibility`,
`_corpus_authority_basis`, and `_corpus_legacy_status` fields.
Code that consumes a vector should check those fields before
treating the value as authoritative.

## separation from Dewata's ceremonial provenance ladder

this status governs the **bibliographic / evidence-chain layer** for
conformance corpora. It is NOT a substitute for, and does not
affect, Dewata's ceremonial/record provenance tiers:

| tier | meaning | governance |
|---|---|---|
| `computed`     | derived from a deterministic computation, not yet attested | PROTOCOL §2.6 |
| `registered`   | recorded in a Dewata registry; presence-only, not attested | PROTOCOL §2.6 |
| `predicted`    | the engine's forward-looking claim about a future value | PROTOCOL §2.6 |
| `verified`     | attested by an applicable human or customary authority | PROTOCOL §2.6 |

those tiers are about CEREMONIAL records (e.g. a banjar's computation
that a given day is a Purnama). corpus evidence status is about
BIBLIOGRAPHIC sources used to validate the engine's arithmetic. the
two namespaces do not interact.

in particular: a corpus's `verification_status: VERIFIED` does NOT
imply `verified` in the ceremonial provenance ladder. the ceremonial
tier requires a human or customary attestation per PROTOCOL §2.6,
which is a separate process.

## how this sidecar changes over time

- A corpus's `(verification_status, reference_eligibility)` may move in
  either axis as evidence is acquired or new evidence undermines the
  source.
- A corpus's status may move from UNVERIFIED → VERIFIED (citation
  found); from INELIGIBLE → ELIGIBLE (citation authority established);
  or in the opposite direction (citation refuted, authority withdrawn).
- Status transitions are append-only in the audit log (any status
  change should be recorded in `disputes.json` with a new dispute
  ID or as a resolution of an existing dispute).
- the `STATUS.json` file itself may be edited; the sidecar is a
  registry, not an event log. the event log is `disputes.json`.

## relationship to PROTOCOL v1.0

this sidecar is the implementation of the gap analysis Finding 5
remediation (corpus authority quarantine). It is part of the v1.0
PROTOCOL's evidence model (§2.4 artifact evidence standard, §2.7
canonical evidence root, §3 dispute classes including `bibliographic`).
