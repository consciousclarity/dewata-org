# STATUS.json schema — corpus authority registry

This document specifies the schema of `phase-1/conformance/STATUS.json`,
the sidecar manifest that records the authority status of every
conformance corpus file under `phase-1/conformance/`.

## why a sidecar exists

Per PROTOCOL v1.0 §2.4 and the v1.0 gap analysis Finding 5, a
conformance corpus's directory placement (`published/`, `ground-truth/`,
etc.) does NOT confer authority. Authority must be explicit,
per-corpus, and machine-readable so that the cross-validation and
conformance machinery can enforce gates deterministically.

The sidecar exists to:

1. Separate **preservation** (the corpus stays on disk for historical
   evidence) from **authority** (whether the corpus may satisfy a
   validation gate).
2. Make the authority status a first-class field that downstream
   code must consult, not a string check buried in a comment.
3. Provide an audit trail: every status entry records who classified
   it, when, on what evidence, and which dispute (if any) it is bound
   to.

## top-level shape

```
{
  "schema_version": "1.0",
  "last_modified": "<ISO8601 timestamp>",
  "policy": "<free text, brief>",
  "gate_predicates": { ... },
  "corpora": { ... },
  "status_meanings": { ... },
  "enforcement": "<free text, brief>"
}
```

## `corpora` entries

```
"<corpus_basename>": {
  "corpus_file":          "<rel path under the repo root>",
  "corpus_class":         "published | unverified | ground-truth",
  "status":               "UNVERIFIED | NON_AUTHORITATIVE | ATTESTED",
  "reason":               "<free text, brief>",
  "related_dispute_id":   "<DISPUTE-* id, or null>",
  "date_classified":      "<YYYY-MM-DD>",
  "evidence_review_artifact": "<rel path>",
  "citation_keys_present_in_corpus": [
    "<AuthorYearShortTitle>",
    ...
  ],
  "preserved":            true | false,
  "may_satisfy_validation_gate":        true | false,
  "may_justify_ruleset_promotion":      true | false,
  "may_be_described_as_ground_truth":   true | false
}
```

The three `may_*` fields are derived from `status` for fast
machine-check; they are also asserted explicitly so a future schema
update that changes the predicates does not silently change the
recorded behavior.

## status values

| status | meaning | may_satisfy_validation_gate |
|---|---|---|
| `UNVERIFIED` | source citation in the corpus could not be independently verified from this host | **no** |
| `NON_AUTHORITATIVE` | source is verified (returns 200 with content) but the source itself is not authoritative (practitioner, encyclopedia, etc.) | **no** |
| `ATTESTED` | source is verified AND authoritative; may satisfy validation gates | **yes** |

## gate predicates

The gate predicates are functions, not just JSON fields. The Python
implementation lives in
`phase-1/src/dewatacalendar/corpus_status.py`:

- `can_satisfy_validation_gate(status) -> bool`
- `can_promote_ruleset_using(corpus_status) -> bool`
- `can_be_described_as_ground_truth(corpus_status) -> bool`
- `can_be_silently_copied_to_authoritative_fixture(corpus_status) -> bool`

All four are `status == ATTESTED`. Any other status returns False.
Unrecognized statuses fail closed.

## how downstream code MUST use this

Any code path that:

- claims a corpus as authoritative,
- cites a corpus to justify a ruleset promotion,
- presents a corpus value as ground truth,
- silently copies values from a corpus into a new authoritative fixture

MUST pass through the gate predicates. If the corpus's status is not
ATTESTED, the claim must be downgraded to "historical" or "diagnostic"
and the corpus's status must be reported to the caller.

The cross-validation machinery already calls
`annotate_vectors_with_status` so every loaded vector carries a
`_corpus_status` field. Code that consumes a vector should check that
field before treating the value as authoritative.

## how this sidecar changes over time

- A corpus's status may move from UNVERIFIED → NON_AUTHORITATIVE →
  ATTESTED as evidence is acquired.
- A corpus's status may move from any status → UNVERIFIED if new
  evidence undermines the source.
- Status transitions are append-only in the audit log (any
  status change should be recorded in `disputes.json` with a new
  dispute ID or as a resolution of an existing dispute).
- The `STATUS.json` file itself may be edited; the sidecar is a
  registry, not an event log. The event log is `disputes.json`.

## relationship to PROTOCOL v1.0

This sidecar is the implementation of the gap analysis Finding 5
remediation. It is part of the v1.0 PROTOCOL's evidence model
(§2.4 artifact evidence standard, §2.7 canonical evidence root, §3
dispute classes including `bibliographic`).
