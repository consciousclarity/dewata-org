# Gap Analysis Addendum — Conformance Test Discovery (Finding 18)

**Date:** 2026-09-15
**Author:** Hermes / Warden (Auditor role, item B of the v1.0 remediation order)
**Scope:** append-only addendum to
`phase-1/docs/audit/GAP_ANALYSIS_v1.0_2026-09-15.md` (commit `c8af8f3`)
**Reference:** PROTOCOL v1.0 (`docs/PROTOCOL.md`, ratified 2026-09-15, commit `d2ba0c2`)

This is an **append-only addendum**, not a rewrite of the committed
gap analysis. Per PROTOCOL §6 and the governance owner's instruction
on 2026-09-15, the committed gap analysis stands as-is; subsequent
discoveries are recorded as addenda to preserve audit history.

---

## Finding 18 — existing parameterized conformance tests searched
the wrong corpus location and therefore exercised zero published
corpus vectors

**File:** `phase-1/tests/test_conformance.py` (pre-B state, the version
in `c8af8f3`)
**File:** `phase-1/conformance/` (layout pre-B)

**Discovery context.** While implementing item B of the v1.0 remediation
order (corpus-authority quarantine machinery, see
`phase-1/conformance/STATUS.json` and `phase-1/src/dewatacalendar/corpus_status.py`),
the candidate test suite was rewritten to exercise the published
corpora explicitly. The pre-B test fixture used
`Path("conformance").glob("*.json")` to enumerate corpus files.

The `conformance/` directory layout is:

    conformance/
    ├── STATUS.json            ← metadata (canonical authority registry)
    ├── STATUS.schema.md
    └── published/             ← historical corpus material
        ├── cunningham_1994.json
        ├── cunningham_1994.py
        ├── igarashi_1999.json
        ├── igarashi_1999.py
        └── kalenderbali_2026-09.json

The pre-B test enumerator used `glob("*.json")` against the top-level
`conformance/` directory. The published corpora live under `conformance/
published/`, **not at the top level**. Therefore the pre-B enumerator
matched:

- Zero published corpus files (no `*.json` exists at the top level
  before STATUS.json was added in item B).

After STATUS.json was added in B, the pre-B enumerator matched exactly
one file (`STATUS.json`), which is **metadata**, not a corpus. The
pre-B loader (`conformance.load_corpus`) then tried to load STATUS.json
as a corpus and failed with `ValueError("unknown corpus format for STATUS")`.

**The pre-B parameterized tests therefore exercised zero real corpus
vectors.** The pre-B result line was:

    tests/test_conformance.py::test_corpus_loads[NOTSET] SKIPPED (got em...)
    tests/test_conformance.py::test_corpus_topic_match[NOTSET] SKIPPED (...)
    tests/test_conformance.py::test_corpus_first_vector_passes[NOTSET] SKIPPED
    tests/test_conformance.py::test_corpus_sample_passes[NOTSET] SKIPPED
    3 passed, 4 skipped in 0.03s

Four corpus-vector tests were SKIPPED because the enumerator returned
zero corpora. The "3 passed" are non-corpus invariant tests
(`test_epoch_anchor`, `test_cycle_completes_at_210`,
`test_ruleset_constant`) which do not load any corpus.

**This means the pre-B test suite had no actual cross-validation
coverage of the published corpora.** The corpus files existed on disk
but were never loaded by any test. Any "the engine matches the corpus"
assertion in the prior audit was therefore made by ad-hoc Python
scripts (e.g. `/tmp/crossvalidate.py` referenced in audit files), not
by the in-tree pytest suite.

**Severity:** material.
**Component:** conformance/testing.
**Blocking scope:**
- `evidence_chain` — no in-tree test exercises the cross-validation
  machinery against the actual corpus vectors, so an evidence-chain
  failure (e.g. STATUS.json drift) is not caught by `pytest`.
- `ruleset_promotion` — the path from "engine matches corpus vectors"
  to "ruleset promoted" runs through these tests; without them, the
  promotion gate is not enforced in CI.

**Does NOT block `production_availability`.**

**Evidence:**
- Pre-B test run at commit `c8af8f3` (true baseline, STATUS.json
  absent from disk): `3 passed, 4 skipped` in `test_conformance.py`.
- Post-B candidate run (STATUS.json present, test fixture rewritten
  to use explicit enumeration): `38 passed, 0 failed` in
  `test_conformance.py`. New tests assert:
  - `STATUS.json` exists at canonical location (`phase-1/conformance/STATUS.json`)
  - `STATUS.json` does not live under `published/`
  - `STATUS.json` is not loadable as a corpus
  - `STATUS.json` registry status matches expected for each published corpus
  - unknown corpora fail-closed to UNVERIFIED
  - only ATTESTED passes the independent-reference gate
  - UNVERIFIED / NON_AUTHORITATIVE corpora cannot justify ruleset_promotion
  - UNVERIFIED / NON_AUTHORITATIVE corpora cannot be described as ground truth
  - UNVERIFIED / NON_AUTHORITATIVE corpora cannot be silently copied to authoritative fixtures
  - Each published corpus file exists
  - Each published corpus loads and each vector carries `_corpus_status` annotation
  - Each annotated vector carries `_corpus_record` with reason + date_classified + evidence_review_artifact
  - Each published corpus cannot satisfy any authority gate (status matches expected, gate returns False)
  - Each published corpus cannot justify ruleset_promotion
  - Each published corpus cannot be described as ground truth
  - The engine produces internal-consistency output for every date in every published corpus (quarantine ≠ silence)

**Resolution.** Resolved in commit B (in-progress as of this addendum).
The pre-B `tests/test_conformance.py` is replaced with an explicit-
enumeration version that:
- declares `PUBLISHED_CORPORA` as a tuple (no glob)
- uses the STATUS.json registry as the single source of truth for
  corpus authority
- asserts the gate behaviors described above

The pre-B `test_dispute_recordable_classifications` failure in
`tests/test_cultural_adapters.py` is **pre-existing** on commit
`c8af8f3` (verified by stash-and-re-run). It is not part of Finding
18 and belongs to the v1.0 dispute-schema migration (item 7 of the
revised remediation order).

**Cunningham / Igarashi vector values are unchanged.** Per the
governance owner's instruction, no historical vector values were
modified. The quarantined corpora remain loadable for diagnostic
comparison; they just cannot satisfy authority gates.

**STATUS.json canonical location preserved** at
`phase-1/conformance/STATUS.json`. It is not in `published/`. The
`published/` directory contains historical corpus material; authority
comes from STATUS metadata, not directory placement.
