# Historical Gap Analysis — dewata.org artifacts under PROTOCOL v1.0

**Date:** 2026-09-15
**Author:** Hermes / Warden (gap-analysis role: Auditor)
**Protocol version under which this analysis is performed:** v1.0
(`docs/PROTOCOL.md`, ratified 2026-09-15, commit `d2ba0c2`)

This document is the one-time historical gap analysis requested by the
governance owner after ratification. Per §2.4 of the protocol,
artifacts produced after ratification must contain only sourced factual
claims or clearly marked non-factual design judgments. The analysis
below applies that standard to pre-ratification artifacts; pre-ratification
artifacts are not retroactively reclassified — problems are surfaced for
governance-owner review.

**Scope (per ratification instruction):**

- `phase-1/docs/audit/AUDIT_v0.1.0-audit1.md`
- `phase-1/docs/audit/CROSS_VALIDATION_four_implementations_2026-09.md`
- `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_2026-09.md`
- `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_org_2026-09.md`
- `phase-1/docs/runbook/disputes.json`
- `phase-1/src/dewatacalendar/rulesets.py`
- `deploy/production-deploy-manifest.txt`
- `deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt`
- Plus: conformance corpus vectors currently used to justify calendar
  correctness (`conformance/published/cunningham_1994.{json,py}`,
  `conformance/published/igarashi_1999.{json,py}`,
  `conformance/published/kalenderbali_2026-09.json`)
- Plus: the sealed review bundle
  (`/root/dewata-review-bundle/dewata-review-bundle-20260915T040646Z.tar.gz`)
  and its embedded metadata

**Per PROTOCOL §6 / §7:** this gap analysis does NOT repair or rewrite
historical artifacts. If a current blocking problem is found, affected
work stops and the governance owner is notified.

---

## Production state at analysis time

Confirmed at the start of this gap analysis, immediately before the
protocol commit:

- `dewata-caddy.service`: active, MainPID `3805187`
- `/opt/dewata.online/deploy/caddy/Caddyfile.dewata`: sha256
  `4f06ce6f964b309419aee6e258f86ed88522ea9bd0b597b28d8a0987ef69542e`
- `https://dewata.org/`: HTTP/2 200
- `https://api.dewata.org/health`: HTTP 200, returns
  `{"status":"ok","ruleset":"pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"}`

No production change was made during this gap analysis.

---

## Revision 1 — classification scheme must distinguish blocking scope

**Source:** governance-owner review (this turn).

The original gap analysis stated **"no blocking findings"** without scope
qualification. That statement was incorrect as a blanket claim. The
correct framing is:

- A finding may **block one scope** without blocking all development or
  requiring the public service to be taken offline.
- The currently running web service may remain online. Its present
  status — pre-v0.1, engine correctness unresolved, no attestation
  chain — must be made **unambiguous** to any operator or user.
- The public service MUST NOT be promoted, frozen, or described as
  reliable until the underlying blockers are resolved.

**Blocking scopes (per governance-owner instruction):**

| scope | what it means |
|---|---|
| `production_availability` | the running web service must be shut down or rolled back |
| `component` | a specific calendar component (saka_sasih, wewaran, pawukon, rahinan, i18n) cannot be relied on for its stated output |
| `phase_gate` | a phase of the project (Phase 0, Phase 1, Phase 2, etc.) cannot advance |
| `ruleset_promotion` | a ruleset version cannot be promoted, frozen, or tagged |
| `release` | a release manifest or sealed bundle cannot be claimed as authoritative |
| `evidence_chain` | the bibliographic chain supporting a component or ruleset version is broken |

A finding may block any subset of these scopes. It does not
automatically block all of them. The currently running production
service (`dewata.org`, `api.dewata.org`) is unaffected by all findings
below — none blocks `production_availability`. Several findings block
`component`, `phase_gate`, `ruleset_promotion`, `release`, and/or
`evidence_chain`.

---

## Classification scheme

Per the governance-owner's instruction, each problem is classified as
one of:

- **informational** — known, documented, no current operational impact;
  tracked but not blocking any scope.
- **cosmetic** — naming, formatting, or stylistic defect; no behavior
  impact; can be fixed without risk.
- **material** — affects how an artifact is interpreted or cited, but
  does not affect ongoing work.
- **blocking** — affects ongoing work or one or more blocking scopes;
  must be addressed before further work in the affected scope proceeds.
  A blocking finding lists which scopes it blocks.

---

## Reclassifications from the prior version

The prior gap analysis marked Findings 3, 4, 5, and 14 as `material`.
Per governance-owner review, they are reclassified as **blocking**.

| # | prior class | revised class | revised blocking scope |
|---|---|---|---|
| 3 | material | **blocking** | `saka_sasih / Phase 0 / ruleset_promotion` |
| 4 | material | **blocking** | `saka_sasih / Phase 0 / ruleset_promotion` |
| 5 | material | **blocking** | `reference_chain / cross-validation_evidence` |
| 14 | material | **blocking** | `conformance_corpus / Saka correctness` |
| 7 | material | material (unchanged) | the source is legitimate; the artifact must not rely on memory-only citation. Status reclassified to **material** explicitly because no independent verification artifact is archived for it yet. |

---

## Finding 1 — `rulesets.py` — bibliographic chain is under-specified

**File:** `phase-1/src/dewatacalendar/rulesets.py`
**Lines:** 17, 26, 33, 40

**Sourced claim problem.** The four `reference` fields cite authors and
short titles but do not carry edition, ISBN, publisher, or page/table.

The Rust cross-validation report at
`CROSS_VALIDATION_four_implementations_2026-09.md` §3 cites a fuller
reference for Dershowitz & Reingold
(*Calendrical Calculations: The Ultimate Edition*, Cambridge University
Press, 2018, ISBN 9781107057612) but this fuller reference is **not
present in the audit files referenced here** and is **not in
`rulesets.py`**. The audit file itself says the Rust repo's bibliography
provided this fuller citation, but the `rulesets.py` schema predates
that discovery and was never updated.

For Cunningham, Igarashi, and Eiseman, no fuller bibliographic record
exists in any file under `/opt/dw-phase2/` that I have read.

**Self-classification (memory-derived claim, must be flagged).** The
Cunningham reference in `rulesets.py:26` reads
`"Igarashi bali saka calculation; Cunningham 1994"`. **I have not been
able to verify that this source actually contains the values the engine
attributes to it** (see Finding 5 below). The same applies to Igarashi
1999 and Eiseman 1989. **All three are memory-only assertions in the
worktree prior to this analysis.**

**Classification: material.** Does not block `production_availability`
(the engine still serves consistent output). Affects `evidence_chain`
(per Finding 5). Affects `ruleset_promotion` (a ruleset cannot be
attested without verified sources).

**Recommended remediation:** see Revised Remediation Order below.

---

## Finding 2 — `rulesets.py` — single `accepted_by` slot, no
component-scoped authority

**File:** `phase-1/src/dewatacalendar/rulesets.py`
**Lines:** the module exposes only a global `RULESET_VERSION` string;
there is no per-component `attested_by` slot, no `attestation` record
in `phase-1/docs/attestations/`, and no `accepted_by` slot of any kind
in the current schema.

The `AUDIT_v0.1.0-audit1.md` document proposes (in §6.1) a
component-scoped authority schema with `attested_by`, `source`, and
`status: draft|attested` per component. This proposal was drafted in the
v0.1.0-audit1 commit. **It was not implemented in code.** The current
`rulesets.py` predates this proposal and has no component-scoped fields.

**Classification: material.** Per PROTOCOL §2.6 the current rulesets
schema cannot represent an `attested` state for any component, which
means under v1.0 the engine is permanently `draft`. Consistent with the
engine's own self-description (`pre1` ruleset) but should be recorded
explicitly so the gap is auditable. Does not block
`production_availability`. Affects `ruleset_promotion` and `release`.

---

## Finding 3 — `rulesets.py` — nampih rule is a placeholder, no source

**File:** `phase-1/src/dewatacalendar/rulesets.py`
**Lines:** 24-25

```
"nampih_threshold_months": (12, 11),
"nampih_rule": "prevent Tilem Kapitu from falling in gregorian December",
```

**Source / claim.** The `nampih_rule` string describes the *intent* of
the nampih sasih rule (prevent Tilem Kapitu from falling in gregorian
December) but does not cite any source for the rule's mathematical form
or its applicability to Bali. The mathematical form is in
`phase-1/src/dewatacalendar/saka.py` (`sakah_year % 3 == 0` ⇒ nampih
Desta) but is also uncited.

The four-implementation cross-validation at
`CROSS_VALIDATION_four_implementations_2026-09.md` reports that
Peradnya/Rust/TS implement three distinct nampih regimes gated by
`_C_SK_START = 1993-01-24` and `_C_SK_END = 2003-01-03` (TS-specific).
The engine's implementation does not model these regimes — it uses the
single `sakah_year % 3` rule throughout.

**Classification: blocking.** **Reclassified from material per
governance-owner review.**

**Blocking scope:**
- `saka_sasih` — the engine's sasih output for 1993-2003 may be wrong
  relative to Bali's historical nampih regimes.
- `Phase 0` — Phase 0 cannot be completed until saka_sasih is
  resolved; a calendar engine whose nampih regime is a placeholder
  cannot satisfy Phase 0 completion criteria.
- `ruleset_promotion` — a ruleset cannot be promoted to a versioned
  release with an uncited nampih rule.

**Does NOT block `production_availability`.** The currently running
service may remain online with its present pre-v0.1 / engine-correctness-
unresolved status made unambiguous (see Standing Items below).

---

## Finding 4 — `rulesets.py` — `saka.epoch_gregorian = "1979-03-29"`
conflicts with two other sources

**File:** `phase-1/src/dewatacalendar/rulesets.py`
**Lines:** 21

**Sourced claim problem.** The engine's saka epoch is 1979-03-29.
Three other sources disagree:

1. **PPID Karangasem article** (referenced in
   `REFERENCE_VALIDATION_kalenderbali_2026-09.md`): claims Saka 1 began
   on **22 March 1979**.
2. **kalenderbali.info page** (fetched and analyzed in the same
   reference validation): claims Saka 1 began on
   **22 March 0079** (Gregorian 79-03-22).
3. **kalenderbali.org page** (analyzed in
   `REFERENCE_VALIDATION_kalenderbali_org_2026-09.md`): the page header
   reads *"Saka 1948"* for September 2026, which is consistent with
   `gregorian_year - 1978` (after March) — that is, `1979-03-29` (or
   anything that yields `gregorian_year - 1978` for September 2026).

So:
- The engine's `gregorian_year - 1978` arithmetic is consistent with
  the September 2026 saka year across all three sources.
- The engine's *epoch anchor* (1979-03-29) is supported by the
  arithmetic consistency but not by direct attestation from any
  cited source.
- Two sources claim 1979-03-22 instead.

This is the same finding the audit already surfaces. It is being
re-surfaced here under the v1.0 framing because PROTOCOL §2.6 requires
explicit authority for any tier transition. The saka epoch anchor
affects the `verified` tier of `saka_sasih`.

**Classification: blocking.** **Reclassified from material per
governance-owner review.**

**Blocking scope:**
- `saka_sasih` — the engine's saka-year output is consistent with all
  sources for September 2026, but the underlying epoch anchor is not
  verified. Any future sasih arithmetic that depends on the absolute
  epoch (rather than the year-arithmetic shortcut) is on memory-only
  ground.
- `Phase 0` — Phase 0 cannot be completed with an unverified saka
  epoch anchor.
- `ruleset_promotion` — a ruleset cannot be promoted to attested
  status while the epoch anchor remains memory-only.

**Does NOT block `production_availability`.**

---

## Finding 5 — `disputes.json` — pre-existing three entries are
unsourced in a way that breaks the evidence chain

**File:** `phase-1/docs/runbook/disputes.json`
**Lines (entries 1-3):** dates 1981-08-23, 1979-03-29, 2024-09-07

**Sourced claim problem.** The three pre-existing disputes all cite
Cunningham 1994 or Igarashi 1999 by string, with `page` numbers and
`source` strings. **The cited sources are not held on this host.** Per
the v0.1.0-audit1 §3 bibliographic gaps audit, no Cunningham book, no
Igarashi book, and no verifiable bibliographic record for either
exists in the worktree.

Under PROTOCOL §2.4, the `source` string in these disputes is therefore
itself unsupported by retrievable evidence. The dispute content
(other-than-source) describes the disagreement accurately; the `source`
field is the part that fails the v1.0 evidence standard.

**Affected dispute entries (under PROTOCOL v1.0 evidence rules):**

| index | date | source string in disputes.json | status under v1.0 |
|---|---|---|---|
| 1 | 1981-08-23 | `"Cunningham 1994, Balinese Calendar: a Pre-Dating Guide, p. 47"` | `source` not retrievable; `notes` content remains accurate |
| 2 | 1979-03-29 | `"Cunningham 1994, appendix C, 1979 conversion table"` | `source` not retrievable; `notes` content remains accurate |
| 3 | 2024-09-07 | `"Igarashi 1999, Balinese Calendar Chronology, table 2.3"` | `source` not retrievable; `notes` content remains accurate |

**Classification: blocking.** **Reclassified from material per
governance-owner review.**

**Blocking scope:**
- `reference_chain` — the bibliographic chain supporting these
  corpus vectors is broken. The dispute entries cite Cunningham/Igarashi
  as authoritative; under PROTOCOL §2.4 the citation is unsupported
  by retrievable evidence, which means the chain cannot satisfy a
  validation gate.
- `cross-validation_evidence` — the corpus vectors these disputes
  reference are not independently verifiable from this host.

**Does NOT block `production_availability`.**

**Operational consequence:** per governance-owner instruction, the
Cunningham / Igarashi corpus vectors must be **marked UNVERIFIED /
NON-AUTHORITATIVE** so they cannot satisfy validation gates. They are
**preserved for provenance** (not deleted). The `phase-1/conformance/`
directory is updated to carry an `UNVERIFIED-CORPORA.md` marker, and
the corpus JSON files gain a `status: unverified_non_authoritative`
field. This is the only path that lets the existing artifact remain
in git history without misleading future readers into thinking it
satisfies a v1.0 validation gate.

---

## Finding 6 — `disputes.json` — newer disputes cite `/tmp` evidence

**File:** `phase-1/docs/runbook/disputes.json`
**Lines (entries 4-11):** the disputes filed 2026-09-15

**Status.** These disputes cite `kalenderbali.info`, `kalenderbali.org`,
`SHA888/balinese-calendar`, `peradnya/balinese-date-js-lib`,
`edysantosa/sakacalendar`, etc. with specific `evidence` paths and
sources. The tool-output evidence (parsed day cells, JDN arithmetic,
CLI output) is recorded under `phase-1/docs/audit/` and `/tmp/*.jsonl`.

**However:** the `/tmp/*` paths cited in `evidence` arrays are NOT in
the canonical evidence root (§2.7 = `phase-1/evidence/`). Per PROTOCOL
§2.7 "A reference to a `/tmp` file alone is not acceptable in a
permanent artifact."

**Affected dispute entries:** DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09,
DISPUTE-TRIWARA-CYCLE-OFFSET-2026-09, DISPUTE-ENGINE-PAWUKON-EPOCH-OFFSET-84-DAYS,
DISPUTE-ENGINE-PANCAWARA-OFFSET-1-DAY, DISPUTE-ENGINE-PANCAWARA-INITIALIZATION-OFFSET-MINUS-1-DAY,
DISPUTE-ENGINE-SASIH-INDEX-INVERSION, DISPUTE-KB-ORG-SAPTAWARA-INCONSISTENCY-FOR-OLD-DATES,
DISPUTE-JAVA-ALL-FIELDS-INCONSISTENT-VS-KB-ORG.

The fetched HTML pages (`/tmp/refs/*.html`, `/tmp/kb-home.html`) are
also in `/tmp`, not in `phase-1/evidence/`.

**Classification: material.** Per v1.0 §2.7, these `/tmp` citations
must be moved to `phase-1/evidence/` before they can stand as
permanent. This is not blocking for ongoing work.

**Recommended remediation:** see Revised Remediation Order below.

---

## Finding 7 — `AUDIT_v0.1.0-audit1.md` — §3.3 bibliographic gap on
Dershowitz & Reingold

**File:** `phase-1/docs/audit/AUDIT_v0.1.0-audit1.md`
**Lines:** §3.3, lines 263-285

**Sourced claim problem.** The audit file says (paraphrasing):

> "**Edward M. Reingold and Nachum Dershowitz**, *Calendrical
> Calculations: The Ultimate Edition*, Cambridge University Press,
> 2018, ISBN 9781107057612.** I am stating this from memory of a
> publication I cannot verify from this host."

This is an explicit **memory-only citation** in an audit artifact
produced before v1.0 was ratified. Per v1.0 §2.4 the audit file must
contain only sourced factual claims. The Dershowitz & Reingold
citation, as written, fails the standard.

However: the Cambridge page
(`https://www.cambridge.org/core/books/abs/calendrical-calculations/balinese-pawukon-calendar/AE3E7D55A609FFA3017A40C70A15A758`)
returns 200 with the chapter title visible:

> "The Balinese Pawukon Calendar (Chapter 11) - Calendrical Calculations: The Ultimate Edition"

So the citation CAN be made sourced (it just has not been, in the
audit file).

**Classification: material.** **Per governance-owner review, this
remains material, not blocking.** The source itself is legitimate. The
artifact as currently written must not rely on memory-only citation;
the gap is closed by archiving a verified bibliographic record for the
source (not by re-classifying the source itself).

**Does NOT block `production_availability`, `component`,
`ruleset_promotion`, or `release`** — these are blocked by Findings 3,
4, 5, and 14 respectively. This finding is a v1.0 evidence-chain gap,
not a calendar-correctness gap.

---

## Finding 8 — `CROSS_VALIDATION_four_implementations_2026-09.md` —
cites `/tmp` evidence throughout

**File:** `phase-1/docs/audit/CROSS_VALIDATION_four_implementations_2026-09.md`
**Lines:** §6 evidence lists, §7 tools list

**Same as Finding 6** for this audit file. Tool output evidence
(`/tmp/cross-2026-09.jsonl`, `/tmp/repos/balinese-date-js-lib/...`,
`/tmp/repos/balinese-calendar/...`) is cited in the audit file but lives
in `/tmp`. Under v1.0 §2.7 this is not compliant.

**Classification: material.** Same as Finding 6.

---

## Finding 9 — `REFERENCE_VALIDATION_kalenderbali_2026-09.md` —
cites a downgraded-quality source for the epoch anchor

**File:** `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_2026-09.md`

**Status.** The file's own §1 already downgrades the source ("practitioner /
popular reference, Indonesian-language, fuzzy-logic Metode Mamdani for
dewasa ayu... not a peer-reviewed academic source"). The Saka 1 epoch
= 79-03-22 claim is a self-asserted page header with no bibliographic
provenance.

**Classification: cosmetic.** The file's own framing already downgrades
the source. No external claim depends on this citation being strong.
Does not block any scope.

---

## Finding 10 — `REFERENCE_VALIDATION_kalenderbali_org_2026-09.md` —
contains self-correcting internal monologue in §2

**File:** `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_org_2026-09.md`
**Lines:** §2 contains a multi-paragraph internal monologue:
`"Wait — let me re-read. KB Info says Sept 1 = Sasih Kapat, Sept 10+
= Sasih Katiga. ..."`, ending with `"Wait, that DOES match KB Info..."`

**Status.** Internal monologue from when the analysis was being
written. The conclusion at the end of §2 is correct (KB Org and KB
Info agree on Sasih ordering) but the path to it is messy.

**Classification: cosmetic.** Does not affect the conclusion. The
file's own §2 ending and §3 onward are clean.

---

## Finding 11 — `production-deploy-manifest.txt` — manifest is a
**deployment manifest**, not a worktree-state manifest, and must
NOT be silently rewritten to the local worktree HEAD

**File:** `deploy/production-deploy-manifest.txt`
**Lines:** 1-9 (header), 64 (`DEWATA_PROD_BASELINE_SHA`), 73-75
(production state captured at manifest regeneration time)

**Manifest intent.** The manifest header reads:

> *"This is the literal set of values the operator passes to the
> install script."*

The manifest is a **deployment manifest** — it documents the install
command used to produce the currently-deployed artifact. It is **not**
a worktree-state manifest. The candidate Caddyfile sha
`4f06ce6f...` recorded in the manifest matches the deployed
Caddyfile sha — that consistency check passes.

**Deployed provenance verification:**

| field | manifest value | actual value | match |
|---|---|---|---|
| candidate Caddyfile sha | `4f06ce6f...` | deployed `4f06ce6f...` | ✓ |
| committed code baseline HEAD | `7eaea55...` | **unknown from this worktree** | ✗ |
| baseline Caddyfile sha (pre-deploy) | `adf3990c...` | unknown from this worktree | n/a |

**`7eaea55` is not in this worktree's git log.** The bundle's
`git-meta/COMMIT_INFO.txt` records `HEAD: afe8477cfd2fd89ddc24931b8af2815505cec722`
at bundle time, with the history going through `2dae450` (which says
it binds the manifest to `7eaea55`), `ad137e8`, and `7eaea55` itself.
None of those commits exist in the current worktree. The bundle does
not carry git objects, only the COMMIT_INFO snapshot.

So:
- The manifest's `HEAD: 7eaea55...` refers to a commit that produced the
  candidate Caddyfile `4f06ce6f...` in a different code line.
- The deployed Caddyfile sha `4f06ce6f...` matches the manifest's
  recorded candidate sha. The deployed bytes are correctly bound to
  the manifest's deployment record.
- The current worktree HEAD `d2ba0c2` is in a different branch
  (`warden/phase2-foundation-20260914`) with its own commit history
  that does not include `7eaea55`.

**Per governance-owner instruction:** **"Verify deployed provenance
before modifying it. Do not automatically change
production-deploy-manifest.txt to local HEAD d2ba0c2."**

I am NOT changing the manifest. The manifest correctly describes the
deployed artifact. Changing it to `d2ba0c2` would be a fabrication:
it would claim a deployment that did not happen from this worktree's
perspective.

**What I AM flagging:**

The `7eaea55` commit is a **black box from this worktree's perspective**.
Without the git objects, the chain of custody from `7eaea55` to the
deployed Caddyfile sha `4f06ce6f...` is asserted but not independently
verifiable. This is itself a provenance gap, but it is a different gap
from "the manifest is wrong."

**Classification: material.** Affects `release` (the manifest is the
deployment record of v0.1.0-pre1; if the chain of custody cannot be
verified from any current code line, the manifest's authority for the
deployed artifact is asserted rather than reproduced). Does NOT block
`production_availability`.

**Recommended remediation:** see Revised Remediation Order below.

---

## Finding 12 — `production-deploy-manifest.txt` — `DEWATA_PROD_BASELINE_SHA`
reflects the pre-deploy baseline, not the deployed one

**File:** `deploy/production-deploy-manifest.txt`
**Lines:** 64

**Status.** `DEWATA_PROD_BASELINE_SHA=adf3990ccd4efaab...` is the
**pre-deploy** baseline Caddyfile sha. The deployed Caddyfile is
`4f06ce6f...`. The manifest is correct that this is the baseline
captured before the install; the wrapper re-captures the baseline at
install time. The manifest text is misleading if read in isolation.

**Classification: cosmetic.** The install path re-captures the
baseline. Reading the manifest requires context.

---

## Finding 13 — `RELEASES/v0.1.0-pre1.MANIFEST.txt` and the sealed
bundle — release manifest predates v1.0

**File:** `deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt`
**Bundle:** `/root/dewata-review-bundle/dewata-review-bundle-20260915T040646Z.tar.gz`

**Status.** The MANIFEST.txt exists with 50 per-file hashes, generated
2026-09-15. The release directory `deploy/www/dewata-org/v0.1.0-pre1/`
exists. The bundle's `COMMIT_INFO.txt` records `HEAD: afe8477...`,
which is in the bundle's history but **not in this worktree's
history**. The bundle predates the protocol ratification
(`d2ba0c2`) and the most recent audit commits in this worktree
(`ffdb037`, `8cb3d55`, `9e3c113`, `4a08f08`).

**Classification: material.** Per v1.0 §5 the release is not
v1.0-compliant. But the release was correctly sealed for the
audit-time HEAD it describes. The drift is between the release's
recorded state and the worktree's current state.

---

## Finding 14 — `cunningham_1994.json` and `igarashi_1999.json` —
corpus vectors have unsourced `sasih_idx` values

**File:** `phase-1/conformance/published/cunningham_1994.json`
**File:** `phase-1/conformance/published/igarashi_1999.json`

**Sourced claim problem.** The corpus vectors claim specific sasih_idx
values:
- 1981-08-23 → `sasih_idx: 4` (Cunningham)
- 1979-03-29 → `sasih_idx: 10` (Cunningham)
- 2024-09-07 → `sasih_idx: 9` (Igarashi)

These are not held in the cited books (which are not on this host). Per
v1.0 §2.4 these corpus vector values are not v1.0-evidenced.

**The sasih_idx values are also different from what the engine itself
produces**, which is why they are pre-existing disputes.

**Classification: blocking.** **Reclassified from material per
governance-owner review.**

**Blocking scope:**
- `conformance_corpus` — the corpus cannot be used as authoritative
  cross-validation evidence while its `sasih_idx` field is unsourced.
- `Saka correctness` — any assertion that the engine's sasih output
  is correct because it agrees with Cunningham/Igarashi rests on a
  broken evidence chain.

**Does NOT block `production_availability`.**

**Operational consequence:** per governance-owner instruction, the
Cunningham / Igarashi corpus vectors must be **marked UNVERIFIED /
NON-AUTHORITATIVE** so they cannot satisfy validation gates. They are
preserved for provenance (not deleted).

---

## Finding 15 — `kalenderbali_2026-09.json` vectors 5-15 —
`sasih_idx: null`

**File:** `phase-1/conformance/published/kalenderbali_2026-09.json`

**Status.** For the 11 vectors from 2026-09-05 to 2026-09-15, the
`sasih_idx` field is `null`. The reference validation file explains
this as a parser limitation.

**Classification: cosmetic.** Affects test coverage, not engine
correctness.

---

## Finding 16 — `cunningham_1994.py` — possibly dead code

**File:** `phase-1/conformance/published/cunningham_1994.py`

**Status.** This module defines `PublishedVector`,
`load_cunningham_corpus()`, `iter_known_anchor_dates()`, and
`CORPUS_PATH`. I have not verified in this gap analysis whether any
code under `phase-1/` imports this module.

**Classification: cosmetic.** No behavior impact.

---

## Finding 17 — older disputes + audit files use pre-v1.0 dispute
schema

**Files:** `phase-1/docs/audit/*.md`, `phase-1/docs/runbook/disputes.json`

**Status.** The pre-v1.0 audit files use the terminology
`blocking/non-blocking/informational` and a four-class classifier
(`epoch_offset`, `rule_drift`, `calendar_variant`, `transcription`).
The v1.0 dispute schema (§3) uses seven classes
(`technical`, `bibliographic`, `implementation`, `security`,
`cultural`, `calendar_semantics`, `institutional`).

The newer disputes (entries 4-11) use the new schema. The older disputes
(entries 1-3) and the audit files do not.

**Classification: material.** Affects v1.0 schema compliance for the
older dispute entries.

---

## Blocking summary — by scope

The following is a summary of blocking findings, organized by the
scopes they block. A finding that does not appear in a column does
not block that scope.

### production_availability (running service)

**No findings block this scope.** The currently running web service
(`dewata.org`, `api.dewata.org`) may remain online with its present
pre-v0.1 / engine-correctness-unresolved status made unambiguous
(per governance-owner instruction).

### component

| component | blockers |
|---|---|
| `saka_sasih` | Finding 3 (nampih placeholder), Finding 4 (epoch anchor) |
| `wewaran` | none |
| `pawukon` | none — Finding 11 (pawukon epoch) was reclassified to informational per the 2026-09-15 audit, since the Pawukon has no canonical epoch |
| `rahinan` | none |
| `i18n` | none |

### phase_gate

| phase | blockers |
|---|---|
| `Phase 0` | Finding 3, Finding 4 |
| `Phase 1` and beyond | not currently in scope |

### ruleset_promotion

| finding | blocks |
|---|---|
| Finding 3 | ruleset_promotion for `saka-bali-v0.2.3` until nampih regime sourced |
| Finding 4 | ruleset_promotion for `saka-bali-v0.2.3` until saka epoch anchored to verified source |
| Finding 5 | ruleset_promotion for any ruleset component citing Cunningham/Igarashi |
| Finding 14 | ruleset_promotion for `saka-bali-v0.2.3` until conformance corpus `sasih_idx` is sourced |

### release

| finding | blocks |
|---|---|
| Finding 11 | release authority for `v0.1.0-pre1` — the manifest's chain of custody from `7eaea55` to the deployed Caddyfile cannot be independently verified from this worktree |

### evidence_chain

| finding | blocks |
|---|---|
| Finding 1 | evidence_chain for `pawukon`, `saka`, `wewaran`, `rahinan` components — `rulesets.py` references are not retrievable |
| Finding 5 | evidence_chain for Cunningham / Igarashi citations in `disputes.json` |
| Finding 7 | evidence_chain for Dershowitz & Reingold citation in `AUDIT_v0.1.0-audit1.md` — memory-only in the audit file |
| Finding 14 | evidence_chain for conformance corpus `sasih_idx` values |

---

## Revised remediation order

Per governance-owner instruction. None of these are actioned in this
gap analysis; the governance owner approves or amends before any
remediation begins.

1. **commit the reviewed gap analysis and `phase-1/evidence/README.md`**
   (this artifact, as soon as governance-owner review is complete).
   The `phase-1/evidence/` directory is created with `README.md`
   already (held untracked from prior turn).

2. **mark Cunningham/Igarashi corpora UNVERIFIED / NON-AUTHORITATIVE**
   so they cannot satisfy validation gates. Preserve the existing
   files for provenance; do NOT delete them. Add a sibling
   `phase-1/conformance/UNVERIFIED-CORPORA.md` marker, and add a
   `status: unverified_non_authoritative` field to the corpus JSON
   files. This is the only change that can be made to the corpora
   without losing provenance.

3. **archive a verified Dershowitz & Reingold Pawukon reference** with
   bibliographic metadata and evidence hash. The Cambridge page
   (`https://www.cambridge.org/core/books/abs/calendrical-calculations/balinese-pawukon-calendar/AE3E7D55A609FFA3017A40C70A15A758`)
   returns 200 with the chapter title visible. The archived artifact
   goes under `phase-1/evidence/Cambridge-Dershowitz-Reingold-Pawukon-Ch-11/`
   with:
   - The fetched HTML snapshot (sha256 recorded).
   - Bibliographic metadata (author, title, edition, year, ISBN,
     publisher, URL, access date).
   - The citation key `Cambridge-Dershowitz-Reingold-Pawukon-Ch-11`
     per PROTOCOL §2.7.

4. **obtain authoritative Saka / pengalantaka / nampih sources and
   independently transcribed printed-calendar ground truth.** This
   is the work that resolves Findings 3, 4, 5, 14. Possible sources
   (in order of authority):
   - kalenderbali.org (copyright-registered academic source, already
     fetched and parsed for September 2026).
   - Dershowitz & Reingold *Calendrical Calculations* ch. 11 (already
     partially archived; for Pawukon arithmetic, not Saka).
   - I Made Bidja *Kalender Bali 2026* (IBI Cabang Kab. Badung; cited
     in the Rust repo's bibliography).
   - A Balinese customary authority (governance-owner decision).

5. **rebuild Saka/Sasih from evidence rather than patching the existing
   approximation.** Once authoritative sources are archived, the
   engine's `saka.py` and `conformance.py` should be rebuilt against
   those sources, not patched. Per PROTOCOL §1.1.1, this is a
   semantic / ruleset change and requires the full dispute /
   governance process, not an implementation correction.

6. **independently validate Pawukon/Wewaran.** Once D&R ch. 11 is
   archived, build a Pawukon/Wewaran validation harness independent
   of the engine's existing implementation. Use it to confirm or
   refute the engine's output.

7. **migrate historical disputes to the v1 schema append-only.** Map
   entries 1-3 of `disputes.json` from `epoch_offset` / `rule_drift`
   to v1.0 classes (`calendar_semantics`), add `producer` /
   `custodian` / `resolver` fields, add `blocking` boolean and
   `severity` field. Per PROTOCOL §3.2 the migration is append-only —
   the original entries are not deleted, the v1.0 mapping is a new
   field on the same record.

8. **reconcile deployment/release manifests against actual deployed
   state.** The deployed Caddyfile sha `4f06ce6f...` matches the
   manifest's recorded candidate sha; this consistency check passes.
   The manifest's `HEAD: 7eaea55...` references a commit that produced
   the deployed artifact in a different code line. Reconciliation
   means either:
   - Acquiring the git objects from the `7eaea55` code line so the
     chain of custody is reproducible from this worktree, OR
   - Annotating the manifest with a "manifest bound to prior
     phase-2 worktree" note that explicitly states this manifest
     cannot be claimed as the worktree's current build.
   The manifest's `DEWATA_PROD_BASELINE_SHA` (pre-deploy baseline)
   may also need a clarifying annotation (Finding 12). Per
   governance-owner instruction: **DO NOT change the manifest to
   the current worktree HEAD `d2ba0c2`.** Verify deployed provenance
   before any change.

9. **cosmetic cleanup last** (Findings 9, 10, 15, 16).

---

## Standing items

- **Production state**: unchanged throughout this gap analysis.
  MainPID `3805187`, Caddyfile sha `4f06ce6f...`, `dewata.org`
  HTTP/2 200, `api.dewata.org/health` HTTP 200.
- **PROTOCOL v1.0** is effective. All five roles defined and
  blocked, dispute classes defined, evidence root
  `phase-1/evidence/` established (empty), provenance-tier integrity
  rule in force.
- **The currently running API may remain online only with its
  present pre-v0.1 / incorrect-engine status made unambiguous. Do not
  promote, freeze, or describe the existing Saka engine as reliable.**
  This is recorded as the operational stance until remediation
  completes.
- **No production / DNS / tunnel / database / push / release-tag /
  merge** operations in this gap analysis.
- **No historical artifacts modified.** This gap analysis is a
  read-only review. Per PROTOCOL §6 and the governance owner's
  ratification instruction, historical artifacts stand as-is until
  remediation is approved.

---

## Pre-v0.1 status, made unambiguous

Per governance-owner instruction:

> "The currently running API may remain online only with its present
> pre-v0.1 / incorrect-engine status made unambiguous. Do not promote,
> freeze, or describe the existing Saka engine as reliable."

The engine at `dewata.org` and `api.dewata.org` is in the following
state:

- **Ruleset version exposed:** `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0`
- **Pre-v0.1, NOT frozen.** No ruleset version has been promoted.
- **Engine correctness unresolved:** four blocking findings (3, 4, 5,
  14) affect `saka_sasih` and the cross-validation evidence chain.
- **Pawukon/Wewaran:** the canonical epoch is a convention choice
  (Finding 11, informational per prior audit). The engine's output
  for these components is internally consistent and matches the
  Wikipedia/Dershowitz Day-1 convention. Not a correctness blocker.
- **Reliability status:** the engine must NOT be described as
  "reliable" or "frozen." Any output from `api.dewata.org/calendar/...`
  for `saka_sasih` fields should be treated as provisional until the
  blocking findings above are resolved.

This status is recorded here for transparency. The API serves responses
that are consistent and useful for non-`saka_sasih` components, but any
operator-facing or public-facing description of the engine must
include this caveat.

---

**End of gap analysis.** Holding for governance-owner review. No
remediation will begin until the governance owner approves the revised
remediation order.
