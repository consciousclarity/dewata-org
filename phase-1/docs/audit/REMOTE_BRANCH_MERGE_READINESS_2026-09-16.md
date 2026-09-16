# Remote Branch Merge Readiness Audit

**Audit date:** 2026-09-16
**Auditor:** Warden / Hermes (audit-only, not a code or governance decision)
**Scope:** Repository-level audit of `origin/warden/phase2-foundation-20260914` (HEAD `3021a9bbd2c4df69213bd702b54df85c5e3f862c`) against `origin/main` (HEAD `5919cf4bf0b96a7ae0b3ab126e46a24e153542d7`).

This is an audit report. It does NOT recommend any merge, PR, or production change. Per user instruction, this audit is read-only; no files are deleted, modified, or rewritten.

---

## 0. TL;DR

The branch is a **mixed-purpose audit-and-evidence branch** containing:

1. **9 governance/evidence commits** (PROTOCOL v1.0 ratification, gap analysis, corpus quarantine, two-axis model, D&R/CALENDRICA evidence acquisition, Wariga evidence acquisition, Pancawara mapping correction) — these are well-scoped, audit-only, and appropriate for a clean integration branch.
2. **5 calendar-engine/scaffolding commits** (security primitives, db foundation schema, ceremony API, BCI web scaffolding, ops release engineering artefacts) — these are scaffold code, not production state.
3. **1 adr/docs commit** (snapshot signing mechanism) — historical ADR.
4. **12 commits of v0.1.0 apex bundle review work** (operator wrapper, install script, rollback, lifecycle test, repeated review fixes, manifest refreshes, deployment incident report) — these are **operational deployment history**, some of which contain sensitive operational data.
5. **14 commits of "intermediate" history** (older calendar validation docs, web scaffolding removal, db tests fix, etc.).

**Recommendation: Option D — preserve this branch as audit/history; create a clean integration branch from main using only the governance/evidence commits.** This is **not** assumed a priori; it follows from the audit findings below.

---

## 1. Complete 41-commit inventory

| # | SHA | title | category | files/components | valid? | superseded? | safe-to-merge-as-is? | disposition |
|---|---|---|---|---|---|---|---|---|
| 1 | `690bfc1` | docs: correct stale release claims in v0.1.0 | documentation | release notes | yes | not yet | yes | docs-cleanup — safe to merge |
| 2 | `a9707b8` | feat(security): visibility tier primitives + redaction + threat model | security | `phase-1/src/dewatacalendar/security/*`, `phase-1/docs/security/MODEL.md` | yes | no | yes | scaffolding — keep |
| 3 | `3331903` | feat(db): foundation schema for cultural record layer (provisional) | database/schema | `phase-1/db/migrations/0001_initial_schema.sql`, `phase-1/src/dewatacalendar/db/*` | yes (provisional) | no | yes | scaffold-only, marked provisional |
| 4 | `6c05a91` | feat(api): ceremony api foundation with visibility-tier redaction | api | `phase-1/src/dewatacalendar/api/*` | yes | no | yes | scaffolding |
| 5 | `236224e` | feat(web): bci scaffolding - static site with i18n bundles | website/static assets | `phase-1/src/dewataweb/*` | yes | no | yes | scaffolding |
| 6 | `80a05a4` | chore(web): remove .gitkeep files now that dirs are populated | website/static assets | `phase-1/src/dewataweb/**/.gitkeep` | yes | no | yes | cleanup |
| 7 | `af4d06a` | feat(ops): quality + release engineering artefacts | deployment | `phase-1/tests/lifecycle/*`, release engineering scripts | yes (historical) | superseded by commits 8-25 | NO | historical — see §2 deployment audit |
| 8 | `b5aed8f` | docs(adr): snapshot signing mechanism (Workstream G) | documentation | `phase-1/docs/adr/0007-snapshot-signing.md` | yes | no | yes | ADR — safe |
| 9 | `6924a7f` | docs: final evidence report for phase 2 foundation | documentation | `phase-1/docs/reports/phase-2-evidence-report.md` | yes | no | yes | docs — safe |
| 10 | `ee56c50` | fix(tests): db tests run before api tests via conftest | tests | `phase-1/tests/conftest.py` | yes | no | yes | test fix — safe |
| 11 | `a093d1b` | feat(apex): validated install for dewata.org landing page (B1) | deployment | `deploy/apex-deploy.sh`, `deploy/atomic/install-apex-candidate.sh`, `deploy/atomic/rollback-apex.sh`, `deploy/production-deploy-manifest.txt`, `deploy/caddy/Caddyfile.dewata.proposed`, `deploy/www/dewata-org/v0.1.0-pre1/` | yes (historical) | superseded by commits 12-25 | NO | historical — see §2 |
| 12 | `283df62` | fix(apex): address review findings (admin off restart, sha256 staging, lifecycle test) | deployment | apex scripts | yes | no | NO | review fixes — historical |
| 13 | `22f2675` | fix(apex): address all 7 review findings | deployment | apex scripts | yes | no | NO | historical |
| 14 | `cd84d4d` | fix(apex): address all 6 review findings (4th iteration) | deployment | apex scripts | yes | no | NO | historical |
| 15 | `c04be70` | fix(apex): address 4th-bundle review (recovery, post-publish failures, no-restart, prod guard) | deployment | apex scripts | yes | no | NO | historical |
| 16 | `5f88be7` | fix(apex): address 5th-bundle corrections (mutually-exclusive flags, actual snapshot path, restore-before-restart) | deployment | apex scripts | yes | no | NO | historical |
| 17 | `064833a` | fix(apex): address 6th-bundle corrections (first-install recovery, real shim restart, wrapper end-to-end) | deployment | apex scripts | yes | no | NO | historical |
| 18 | `ba8bd2a` | docs(apex): regenerate production deploy manifest against HEAD 064833a | deployment | `deploy/production-deploy-manifest.txt` | yes | superseded by 19-29 | NO | historical |
| 19 | `7b3f1e0` | fix(apex): address 7th-bundle blockers (disposable-validation adapter, INCOMPLETE on validation failure, REPLACEMENT staging order, snapshot release backup preservation, wrapper test evidence) | deployment | apex scripts + `tests/test-wrapper-e2e.sh` | yes | no | NO | historical |
| 20 | `21c3db1` | fix(apex): address 8th-bundle blockers (rollback preserves snapshot, isolation, listener readiness, exact exit codes, repeated rollback proof) | deployment | apex scripts + `tests/test-wrapper-e2e.sh` | yes | no | NO | historical |
| 21 | `e702026` | chore(apex): regenerate v0.1.0-pre1 manifest against HEAD 21c3db1 | deployment | `deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt` | yes | superseded | NO | historical |
| 22 | `cea73c6` | chore(apex): update manifest with current HEAD e702026 + ruleset version | deployment | manifest | yes | superseded | NO | historical |
| 23 | `5237d1a` | chore(apex): update manifest generated timestamp | deployment | manifest | yes | superseded | NO | historical |
| 24 | `badc617` | fix(apex): enforce immutable production paths + per-file manifest + DEPLOY_* refusal test | deployment | `deploy/apex-deploy.sh`, `tests/test-wrapper-e2e.sh` | yes | no | NO | historical |
| 25 | `7eaea55` | chore(apex): refresh production-deploy-manifest with HEAD badc617 | deployment | `deploy/production-deploy-manifest.txt` | yes | superseded by 26-28 | NO | historical — manifest bound to commit `7eaea55` |
| 26 | `ad137e8` | chore(apex): refresh production-deploy-manifest against HEAD 7eaea55 + final wrapper sha 18848e06 | deployment | manifest | yes | superseded by 27 | NO | historical |
| 27 | `2dae450` | chore(apex): bind production-deploy-manifest to committed code baseline 7eaea55 | deployment | manifest | yes | superseded | NO | historical |
| 28 | `afe8477` | fix(apex): correct release-tree aggregate using the wrapper's sha256_of_tree algorithm | deployment | `deploy/apex-deploy.sh`, `tests/test-wrapper-e2e.sh` | yes | no | NO | historical — also modifies `deploy/caddy/Caddyfile.dewata` |
| 29 | `4a08f08` | docs(calendar): AUDIT_v0.1.0-audit1 -- pre-freeze source/epoch audit | evidence/research | `phase-1/docs/audit/AUDIT_v0.1.0-audit1.md` | yes | no | yes | audit docs — safe |
| 30 | `9e3c113` | docs(calendar): independent reference validation vs kalenderbali.info (Sept 2026) | evidence/research | `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_2026-09.md`, `phase-1/conformance/published/kalenderbali_2026-09.json` | yes | no | yes | evidence — safe |
| 31 | `8cb3d55` | docs(calendar): cross-validation vs 3 reference implementations | evidence/research | `phase-1/docs/audit/CROSS_VALIDATION_four_implementations_2026-09.md` | yes | no | yes | evidence — safe |
| 32 | `ffdb037` | docs(calendar): kalenderbali.org (KBD) cross-validation - real findings | evidence/research | `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_org_2026-09.md` | yes | no | yes | evidence — safe |
| 33 | `d2ba0c2` | docs(governance): ratify Hermes Operating Protocol v1.0 | governance | `docs/PROTOCOL.md` | yes | no | yes | governance — safe |
| 34 | `c8af8f3` | docs(audit+evidence): commit gap analysis + canonical evidence root under PROTOCOL v1.0 | governance | `phase-1/docs/audit/GAP_ANALYSIS_v1.0_2026-09-15.md`, `phase-1/evidence/root.md` | yes | no | yes | governance — safe |
| 35 | `f3261c5` | feat(conformance): corpus-authority quarantine + STATUS.json registry | governance | `phase-1/conformance/STATUS.json`, `phase-1/src/dewatacalendar/corpus_status.py`, `phase-1/src/dewatacalendar/conformance.py` | yes | no | yes (with audit caveats — see §5) | governance — safe |
| 36 | `5d8e7a1` | refactor(conformance): split corpus status into two-axis model + dispute-ID supersession + .gitignore exception | governance | corpus_status.py, .gitignore | yes | no | yes (with audit caveats — see §5) | governance — safe |
| 37 | `4d37765` | D&R Pawukon evidence package + CALENDRICA 4.0 first-party evidence | evidence/research | `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/*` | yes | superseded by 38 (first-party replacement) | yes (superseded) | evidence — historical context only |
| 38 | `6c82001` | Corrective evidence/provenance pass: replace Calixir with first-party EdReingold/calendar-code2 | evidence/research | firstparty CALENDRICA evidence | yes | no | yes | evidence — safe |
| 39 | `9516b01` | Two-axis analysis: RAW_GREGORIAN_MAPPING vs PHASE_NORMALIZED_FORMULA | evidence/research | `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2/two-axis-analysis.md`, `cycle-comparison/*` | yes | no | yes | evidence — safe |
| 40 | `d5c0a51` | Corrective audit: Pancawara mapping bug found, retracted false claim | evidence/research | `phase-1/docs/runbook/disputes.json`, `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2/cycle-comparison/adapter-audit.md` | yes | no | yes | evidence — safe |
| 41 | `3021a9b` | Wariga source evidence acquisition + two audit corrections | evidence/research | `phase-1/evidence/references/balinese-wariga-sources/*`, STATUS.json Wariga corpora | yes | no | yes | evidence — safe |

### category rollup

| category | commits |
|---|---|
| governance | 4 (`d2ba0c2`, `c8af8f3`, `f3261c5`, `5d8e7a1`) |
| evidence/research | 8 (`4a08f08`, `9e3c113`, `8cb3d55`, `ffdb037`, `4d37765`, `6c82001`, `9516b01`, `d5c0a51`, `3021a9b` = 9; with `3021a9b` reclassified from "Wariga evidence" to "evidence/research") |
| calendar engine | 0 (no engine changes) |
| tests | 1 (`ee56c50`) — plus tests added alongside other commits |
| deployment | 17 (commits 7, 11-28) |
| production-history | 0 (no production-state changes; deployment commits are operator-side) |
| website/static assets | 3 (`236224e`, `80a05a4`, `af4d06a` partially) |
| database/schema | 1 (`3331903`) |
| security | 1 (`a9707b8`) |
| api | 1 (`6c05a91`) |
| documentation | 4 (`690bfc1`, `b5aed8f`, `6924a7f`) + audit docs (in evidence/research) |
| obsolete/superseded | 0 |

**Note: 17 of 41 commits are deployment-related.** This is the dominant non-governance/evidence category and the primary reason the branch should not be merged as-is.

---

## 2. Deployment-history concerns

### 2.1 files in `deploy/` that should NOT be merged unchanged

| file | purpose | disposition |
|---|---|---|
| `deploy/apex-deploy.sh` (407 lines) | operator wrapper, reviewed, used for v0.1.0-pre1 install | **historical only** — frozen at commit `7eaea55` per `production-deploy-manifest.txt`; later commits changed it; do NOT re-merge without reconciliation against current production state |
| `deploy/atomic/install-apex-candidate.sh` (1175 lines) | installer | **historical only** |
| `deploy/atomic/rollback-apex.sh` (380 lines) | rollback script | **historical only** |
| `deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt` (56 lines) | reviewed release manifest | **historical only** — bound to commit `7eaea55`, superseded by later commits but never regenerated |
| `deploy/production-deploy-manifest.txt` (6898 bytes) | operator-passed values for the install | **historical only** — bound to commit `7eaea55`; later commits changed scripts but did not regenerate this manifest. Note: production is currently at this manifest's expected state |
| `deploy/caddy/Caddyfile.dewata` | current committed Caddyfile (NOT what's in production) | **drift detected** — production SHA `4f06ce6f964b309419aee6e258f86ed88522ea9bd0b597b28d8a0987ef69542e`, repo SHA `adf3990ccd4efaab427f71167799c99a3ddebcfc23ed468f95925c4adf11016a` |
| `deploy/caddy/Caddyfile.dewata.proposed` | proposed next-version Caddyfile | **candidate only** — NOT deployed; would route `dewata.org` apex to static files (already done via `Caddyfile.dewata` runtime) |
| `deploy/caddy/Caddyfile.dewata-apex-dev` | development variant | development-only |
| `deploy/caddy/Caddyfile.dewata.diff` | diff of original vs proposed | **historical** |
| `deploy/caddy/Caddyfile.dewata.runtime` | copy of production Caddyfile at one snapshot in time | **historical** |
| `deploy/caddy/dewata.vhost` | earlier vhost | development-only |
| `deploy/www/dewata-org/v0.1.0-pre1/` (50 files) | the v0.1.0-pre1 static bundle | **production release tree** — this IS what's currently served |
| `deploy/bin/dewata-deploy.sh` | older deploy script | development-only / superseded |
| `deploy/lifecycle-test/run-lifecycle-test.sh` (55925 bytes) | lifecycle test | historical |
| `deploy/lifecycle-test/lifecycle-test-output.txt` (5098 bytes) | test output capture | historical |
| `deploy/lifecycle-test/logs/run-*.log` (2 files) | lifecycle test logs | operational |
| `deploy/logs/*.log` (24 files, ~96KB total) | **operational caddy access/error logs** | **SHOULD NOT BE IN PUBLIC REPO** — see §7 |
| `deploy/incident-report-2026-09-14.md` (151 lines) | production incident report | historical; **contains public IP addresses** — see §7 |
| `deploy/dns/README.md` | operator DNS runbook | contains DNS commands, **contains public IP** — see §7 |
| `deploy/runbook/*.md` | deploy/cloudflare/crontab runbooks | operational docs; some contain public IP — see §7 |
| `deploy/systemd/*.service` | systemd unit files | historical |
| `tests/test-wrapper-e2e.sh` etc | deployment tests | historical |

### 2.2 deployment drift between branch and production

| artifact | repo SHA | production SHA | drift? |
|---|---|---|---|
| `Caddyfile.dewata` | `adf3990ccd4efaab427f71167799c99a3ddebcfc23ed468f95925c4adf11016a` | `4f06ce6f964b309419aee6e258f86ed88522ea9bd0b597b28d8a0987ef69542e` | **YES** — repo has post-`afe8477` version, production has pre-`afe8477` version |

**Per user ABSOLUTE BOUNDARY: "without asking first, do NOT... modify production... restart/alter production services."** This audit identifies the drift but does NOT modify production. Any reconciliation requires explicit user authorization.

### 2.3 manifest vs scripts binding

`deploy/production-deploy-manifest.txt` is **explicitly bound** to commit `7eaea55`:
```
COMMITTED CODE BASELINE (the reviewer's reference):
  HEAD:            7eaea55a7a82525e687ef81056fc51b58e79937b
  commit subject:  chore(apex): update manifest generated timestamp
```

But commits 26, 27, 28 (`ad137e8`, `2dae450`, `afe8477`) modified `apex-deploy.sh` AFTER this manifest was committed. The manifest is **stale relative to its own referenced commit's subsequent changes**. This is a documented hazard in the manifest itself:
```
# Mandatory drift-guard baseline -- capture this RIGHT NOW with:
#   sha256sum apex-deploy.sh install-apex-candidate.sh rollback-apex.sh run-lifecycle-test.sh > .deploy-baseline.sha256
```

**Finding: production-deploy-manifest.txt should NOT be re-merged into main without re-binding to a current commit.**

### 2.4 deployment commits that should NOT be merged unchanged

The 17 deployment commits (commits 7, 11-28) collectively form an operator-side review cycle. They:
- Modified production-adjacent scripts multiple times (8 review iterations)
- Each iteration regenerated `production-deploy-manifest.txt` but the regeneration was never atomic with the script changes
- Contain operational logs and incident reports with public IP addresses
- Are bound to commit `7eaea55` baseline that is itself now in the past

**Recommendation: do NOT merge these commits to main as-is.** They are appropriate for an audit/history branch where the binding to `7eaea55` remains valid and the full iteration history is preserved.

---

## 3. Stale-claims audit

### 3.1 search results

| pattern | hits | files/lines | disposition |
|---|---|---|---|
| `engine is verified` | 2 | `phase-1/evidence/.../claim-register.md:472` (table column header, not a claim); `phase-1/docs/audit/AUDIT_v0.1.0-audit1.md:426` (qualified claim: "verified against the engine's 1981-08-23 anchor") | **OK** — both uses are qualified, not absolute |
| `engine is correct` | 1 | `phase-1/docs/audit/AUDIT_v0.1.0-audit1.md:347` (table describing what `test_corpus_loads` asserts) | **OK** — describes the test's claim, not asserting it as fact |
| Cunningham authoritative | 2 | `phase-1/docs/runbook/disputes.json:262` + `phase-1/conformance/STATUS.json:37` | **OK** — both explicitly mark Cunningham as UNVERIFIED + INELIGIBLE, NOT authoritative |
| Igarashi authoritative | 1 | `phase-1/docs/runbook/disputes.json:285` | **OK** — same as Cunningham |
| ATTESTED used incorrectly | 12+ | all in `phase-1/src/dewatacalendar/corpus_status.py` and tests | **see §5** — `ATTESTED` is a code enum, not a claim about evidentiary status; it is correctly used as a derived value `(VERIFIED, ELIGIBLE)` |
| ruleset promoted | multiple | `STATUS.json` `may_justify_ruleset_promotion` field; `can_promote_ruleset_using()` function; tests | **see §5** — function does NOT enforce dispute gating |
| Phase 0 complete | 0 | — | no stale claim |
| v0.1.0 production-ready | 0 | — | no stale claim (only `v0.1.0-pre1` references, correctly marked as pre1) |
| customary review complete | 0 | — | no stale claim |

### 3.2 specific lines requiring audit annotation

| file:line | text | disposition |
|---|---|---|
| `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/claim-register.md:472` | "engine-verified" column header | **OK** — describes the table column, not making an absolute claim |
| `phase-1/docs/audit/AUDIT_v0.1.0-audit1.md:347` | "the engine is correct" (table cell describing a test) | **audit-annotation suggested**: clarify this is the test's assumption, not a verified claim |
| `phase-1/conformance/STATUS.json:25` | `"can_promote_ruleset_using": "verification_status == 'VERIFIED' AND reference_eligibility == 'ELIGIBLE'"` | **MISLEADING**: see §5 — this predicate does NOT include dispute gating |
| `phase-1/conformance/STATUS.json:74` (kalenderbali_2026-09) | `"may_justify_ruleset_promotion": false` (manually set in JSON) | OK as documentation; not enforced by code |
| `phase-1/conformance/STATUS.json:117-118` (reingold_dershowitz_2018_calendrica_4_0_firstparty) | `may_justify_ruleset_promotion: false`, `blocking_disputes_pending: [5 disputes]` | OK as documentation; **not enforced** — see §5 |

### 3.3 old dispute classifications presented as current

`disputes.json` uses two parallel taxonomies:
1. PROTOCOL v1.0 7-class taxonomy (`technical, bibliographic, implementation, security, cultural, calendar_semantics, institutional`) — stored in `class` field
2. secondary taxonomy (`mapping_phase, formula_semantics, indexing_representation, naming_only, insufficient_independent_evidence`) — stored in `reclassification.new_class` field

Both are in use. The PROTOCOL v1.0 is the canonical class. The secondary taxonomy is a refinement from the two-axis analysis. **No fix needed** — both are recorded.

### 3.4 obsolete test namespace

`phase-1/tests/test_cultural_adapters.py:276` defines:
```python
allowed = {"epoch_offset", "rule_drift", "calendar_variant", "transcription"}
```

These are NOT in PROTOCOL v1.0's class taxonomy (which is `technical, bibliographic, implementation, security, cultural, calendar_semantics, institutional`). The test is **obsolete** — it predates PROTOCOL v1.0 ratification.

**Disposition: this test should be updated** — but per user instruction, this audit does NOT mix test fixes into evidence work. The test should be addressed in a separate, dedicated commit.

---

## 4. Evidence-lineage audit

### 4.1 sources in STATUS.json

| corpus | verification_status | eligibility | authority_basis | lineage distinct from S3 (Java impl)? |
|---|---|---|---|---|
| `cunningham_1994` | UNVERIFIED | INELIGIBLE | unknown | yes (but UNVERIFIED) |
| `igarashi_1999` | UNVERIFIED | INELIGIBLE | unknown | yes (but UNVERIFIED) |
| `kalenderbali_2026-09` | VERIFIED | INELIGIBLE | practitioner | yes |
| `reingold_dershowitz_2018_pawukon_chapter` | VERIFIED | INELIGIBLE | scholarly | yes |
| `reingold_dershowitz_2018_calendrica_4_0_firstparty` | VERIFIED | ELIGIBLE | software_reference | yes (CALENDRICA ≠ Ardhana) |
| `reingold_dershowitz_2018_calendrica_4_0_calixir` | VERIFIED | INELIGIBLE | software_reference | superseded |
| `wariga_suparta_ardhana_2006` | VERIFIED | INELIGIBLE | scholarly | yes (printed book) |
| `wariga_putra_manik_ariana_2009` | VERIFIED | INELIGIBLE | scholarly | yes (printed book) |
| `wariga_kemendikbud_hindu_bs_kls_ix_2022` | VERIFIED | ELIGIBLE | institutional | yes (Ministry of Education textbook) |
| `wariga_babadbali_com` | VERIFIED | ELIGIBLE | practitioner | yes (independent cultural reference site) |
| `wariga_edysantosa_sakacalendar_java` | VERIFIED | ELIGIBLE | software_reference | **DERIVATIVE OF S1+S2** (explicitly cites Pokok-pokok Wariga + Tenung Wariga) |

### 4.2 S3 (edysantosa/sakacalendar) lineage verification

**Confirmed derivative, not independent.** The Java source code in `phase-1/evidence/references/balinese-wariga-sources/edysantosa-sakacalendar/extracted-functions.txt` contains:

> Reference books cited in code:
> - "Dasar Wariga" + "Tenung Wariga" by I.B. Putra Manik Aryana
> - "Pokok-pokok Wariga" by I.B. Supartha Ardana

S3 explicitly derives from S1 (Suparta Ardhana) and S2 (Putra Manik Aryana). When S3 agrees with CALENDRICA, that is **algorithmic corroboration between two software implementations** that both trace to overlapping Wariga traditions — it is NOT customary/cultural attestation.

This is correctly recorded in:
- `phase-1/evidence/references/balinese-wariga-sources/claim-register.md`
- `phase-1/evidence/references/balinese-wariga-sources/source-provenance-graph.md`
- `phase-1/evidence/references/balinese-wariga-sources/bibliographic-records.md`
- `phase-1/conformance/STATUS.json` (wariga_edysantosa_sakacalendar_java entry explicitly: "DERIVATIVE of S1+S2 — same lineage")
- `phase-1/tests/test_wariga_evidence.py::test_source_provenance_graph_exists` asserts derivative marker

### 4.3 PENDING-evidence-model-note-2026-09-15.md

The note's substance is **fully redundant** with what is already in commit `3021a9b`. Both observations (S3 derivative + S3/CALENDRICA = algorithmic corroboration) are recorded in:
- `claim-register.md`
- `source-provenance-graph.md`
- `STATUS.json`
- test assertions

**Recommendation: delete this file, do NOT commit it.** It is untracked on the local working tree (`git status` confirms). No commit will introduce it.

---

## 5. STATUS.json and promotion-gate audit

### 5.1 promotion-gate logic gap

The current gate predicates are defined in `STATUS.json:22-27` and implemented in `phase-1/src/dewatacalendar/corpus_status.py:256`:

```python
def can_promote_ruleset_using(record) -> bool:
    """return True iff a ruleset promotion may be justified by this corpus."""
    return can_satisfy_validation_gate(record)
```

This is **identical to `can_satisfy_validation_gate()`**. It does NOT check:
- whether `blocking_disputes_pending` is non-empty
- whether any `related_dispute_id` is `blocking: true` and `resolution: pending`
- whether `scope_limitations` excludes the proposed ruleset claim

### 5.2 caller path that could incorrectly promote

A caller could do:

```python
record = corpus_record_for("reingold_dershowitz_2018_calendrica_4_0_firstparty")
# record.verification_status == "VERIFIED"
# record.reference_eligibility == "ELIGIBLE"
# record has 5 blocking_disputes_pending (per STATUS.json)
if can_promote_ruleset_using(record):
    promote_ruleset("pawukon-v0.5.0")  # this would succeed!
```

The `blocking_disputes_pending` field is documentation-only. **The promotion gate does not enforce it.**

The `may_justify_ruleset_promotion: false` field on each STATUS.json entry is also documentation-only — it is not enforced by `can_promote_ruleset_using()`.

### 5.3 scope_limitations gap

`scope_limitations` arrays in STATUS.json (e.g., on `wariga_kemendikbud_hindu_bs_kls_ix_2022`) are **never read by code**. A caller cannot ask "is this corpus eligible to validate a Saka year claim?" — they get a single yes/no.

### 5.4 proposed gate refinement (NOT applied)

A correct gate would require:
1. `verification_status == "VERIFIED"`
2. `reference_eligibility == "ELIGIBLE"`
3. **for each blocking_disputes_pending, that dispute's resolution != "pending"** (or the dispute's scope does not overlap the proposed ruleset)
4. **for each scope_limitations, that the proposed ruleset does not fall within the limited scope**

This is an architecture concern, not a one-line fix. It should be addressed in a separate, dedicated commit.

---

## 6. Tests audit

### 6.1 known failing test

**`test_cultural_adapters.py::test_dispute_recordable_classifications`** — pre-existing failure (commit `4d37765` baseline).

```python
def test_dispute_recordable_classifications():
    """dispute classifications are bounded — no leaked free-text."""
    from dewatacalendar.disputes import load_disputes
    allowed = {"epoch_offset", "rule_drift", "calendar_variant", "transcription"}
    for d in load_disputes():
        assert d.get("classification") in allowed
```

**Root cause:** `allowed` is a stale namespace from before PROTOCOL v1.0. PROTOCOL v1.0's actual classes are `technical, bibliographic, implementation, security, cultural, calendar_semantics, institutional`. Real disputes use these + a secondary taxonomy in `reclassification.new_class`.

**Correct repair:** widen `allowed` to PROTOCOL v1.0's 7 classes. Or remove the test entirely (it is documentation-style, not behavioral).

**Disposition:** this audit does NOT mix this fix into evidence work. A dedicated repair commit is appropriate.

### 6.2 tests that silently skip if source artifacts are missing

| test | behavior if /tmp file missing |
|---|---|
| `phase-1/tests/test_evidence_calendrica_runtime.py` | `@pytest.mark.skipif` — explicit skip, NOT silent |
| `phase-1/tests/test_firstparty_cycle_counts.py` | no /tmp dependency — uses committed artifacts |
| `phase-1/tests/test_evidence_firstparty_calendrica.py` | no /tmp dependency |
| `phase-1/tests/test_wariga_evidence.py::test_sakacalendar_java_sha256_matches_recorded` | **`if os.path.exists(java_path):` then assert; else vacuous pass** — **silent if /tmp file is missing** |

**Disposition:** `test_sakacalendar_java_sha256_matches_recorded` should be updated to either `@pytest.mark.skipif(not java_path.exists(), ...)` or assert the file's presence.

### 6.3 tests that are documentation-only

Multiple tests assert only that certain strings appear in evidence markdown files. Examples:
- `test_two_axis_analysis.py::test_*` — assert "mapping_phase" string appears in `two-axis-analysis.md`
- `test_adapter_audit.py::test_*` — assert string contents in `adapter-audit.md`
- `test_wariga_evidence.py::test_*` — assert string contents in Wariga evidence markdown

These are appropriate for evidence-package integrity checks (verifying documentation has not been silently altered). They are NOT a substitute for behavioral tests of the engine. **Classification: valid for evidence integrity, weak as engine verification.**

### 6.4 tests whose expected values come from Dewata itself

`phase-1/tests/test_conformance.py:475-490` (`test_engine_epoch_anchor_1981_08_23`):
```python
result = compose_day(date)
assert result.pawukon["wuku_name"] == "Sinta"  # Dewata's own output
assert result.wewaran["pancawara_name"] == "Paing"  # Dewata uses mapping A
assert result.wewaran["saptawara_name"] == "Redite"  # Dewata's own output
```

**Finding:** This test asserts that 1981-08-23 produces `Sinta/Paing/Redite`. This is **Dewata's self-consistency test**, not a cross-validation against any external source. It does not catch:
- The +84-day offset vs CALENDRICA
- The Mapping A vs Mapping B convention difference

Per the previous audit (commit `d5c0a51`), `Paing` here is Dewata's internal mapping A convention, which differs from the cultural convention (Mapping B = `Umanis`). The test passes anyway because it asserts Dewata's behavior.

**Disposition:** this is a known limitation. The cross-validation is done in `phase-1/src/dewatacalendar/cross_validation.py` separately. The conformance test should ideally include a known external reference date (e.g., 2026-09-01 from kb.org) and assert against that. Not addressed in this audit.

### 6.5 tests that skip if source artifacts are missing

`phase-1/tests/test_evidence_calendrica_runtime.py` — explicit `@pytest.mark.skipif` for SBCL availability + `/tmp/refs/calendrica-4.0.cl` presence. These are correctly marked as optional tests; not silent.

### 6.6 file with no test_ functions

`phase-1/tests/test_evidence_reingold_dershowitz_2018.py` — has only `def main()` returning int. **No pytest tests in this file.** It runs as a CLI script, not via pytest. **Classification: obsolete** — it does not run as part of `pytest`. Should either be converted to pytest tests or moved to a `scripts/` directory.

### 6.7 skipped tests

Skipped tests observed in the test suite output (8 total): all are the `@pytest.mark.skipif` ones from `test_evidence_calendrica_runtime.py` — appropriately skipped when SBCL or `/tmp/refs/` artifacts are absent. Not a concern.

---

## 7. Public-repository suitability audit

This is a **public GitHub repository**. The audit must confirm nothing in the 41-commit branch exposes:

### 7.1 secrets scan

| pattern | hits |
|---|---|
| github_pat / aws_key / private_key / cf_token / api_key / bearer / ssh_privkey_header / env_secret_val | **0 hits across 228 files** |

The branch contains no credentials, tokens, or private keys. `/root/.env.dewata.online` is correctly excluded by `.gitignore`.

### 7.2 public IP addresses (operational exposure)

| location | IP(s) | sensitivity | recommendation |
|---|---|---|---|
| `phase-1/docs/security/MODEL.md:29` | `62.72.7.218` (origin host) | low — known infrastructure IP from MEMORY.md | OK (already public knowledge via DNS A records) |
| `phase-1/docs/runbook/DEPLOY.md:23,24` | `62.72.7.218` | low | OK |
| `ARCHITECTURE.md:10,444-448` | `62.72.7.218` | low | OK |
| `deploy/runbook/DEPLOY.md:28` | `62.72.7.218` | low | OK |
| `deploy/incident-report-2026-09-14.md:44` | `54.149.79.189`, `34.216.117.25` (conflicting apex A records) | medium — public DNS exposure; not a secret per se but documents past infrastructure decisions | **annotation suggested**: clarify these are historical conflicting records being phased out |
| `deploy/production-deploy-manifest.txt:117-118` | `54.149.79.189`, `34.216.117.25` (DNS commands) | medium | **annotation suggested**: clarify these are legacy records pending deletion |
| `deploy/dns/README.md:25` | `62.72.7.218` (in DNS command example) | low | OK |

**Finding: public IP addresses are documented in plain text in a public repo.** This is a minor concern. Most are already public via DNS A records. The two conflicting apex records (54.x, 34.x) document a known operational issue.

### 7.3 copyright compliance

| artifact | copyright status | inclusion OK? |
|---|---|---|
| `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2/calendar.l` | **Apache-2.0** (verified SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`) | **YES** — Apache-2.0 §2 grants redistribution rights; LICENSE file included |
| `.../dates.l` | Apache-2.0 | YES |
| `.../LICENSE` | Apache-2.0 (verbatim) | YES |
| `.../calendrica-source/calendrica-4.0.cl` | older restrictive header (Calixir copy) | **NO** — not in git (Calixir source NOT in the branch — only `COPYRIGHT_DERSHOWITZ_RHEINGOLD.txt` LICENSE notice); preserved as historical evidence |
| `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/cambridge-chapter-page-ultimate-edition.html` | Cambridge publisher landing page | OK — this is a public webpage, not the chapter text |
| `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/crossref-chapter-metadata.json` | CrossRef metadata record (public API) | OK |
| `phase-1/evidence/references/balinese-wariga-sources/kemendikbud-hindu-bs-kls-ix/pages-37-40-extracted.txt` | Indonesian government open-content license (Kemendikbud + Kemenag textbook) | OK — government open-content; 6508 bytes extracted (0.03% of 20MB PDF); pages 37-40 only |
| `phase-1/evidence/references/balinese-wariga-sources/edysantosa-sakacalendar/extracted-functions.txt` | LGPL-2.1 Java source | OK — function-level extraction only (5940 bytes / 4.96% of full source); under fair-use citation; full source NOT in git |
| `phase-1/evidence/references/balinese-wariga-sources/*` (other 5 markdown files) | original synthesis (this project) | OK |
| `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/calendrica-source/dates4.csv` | sample data from CALENDRICA distribution | OK — sample data, not copyrightable |
| Pokok-pokok Wariga (S1) full text | copyright Paramita | **NOT in branch** — only bibliographic metadata |
| Tenung Wariga (S2) full text | copyright Bali Aga | **NOT in branch** — only bibliographic metadata |

**Finding: no copyrighted full-book material in the public branch.** Only short quotations (under 5% of each source) are retained, all under fair-use citation or explicit open-content licenses.

### 7.4 personal information / machine-specific data

| location | type | sensitivity | recommendation |
|---|---|---|---|
| `phase-1/docs/security/MODEL.md` | threat model referencing local paths | OK | OK |
| `deploy/runbook/*.md` | operator-runbook paths `/opt/dewata.online/*` | low — these are documented production paths | OK |
| `deploy/incident-report-2026-09-14.md` | MainPID numbers, caddyfile SHAs at incident times | low — operational incident metadata | OK |
| `deploy/logs/*.log` | HTTP access logs from `127.0.0.1` | **medium** — these are operational artifacts that should NOT be in a public repo | **see below** |

### 7.5 deploy/logs/*.log — operational artifacts in public repo

24 log files (~96KB total) are committed under `deploy/logs/`. They contain:
- Caddy HTTP access logs from `127.0.0.1` (localhost testing)
- Caddy startup/stderr logs from disposable lifecycle test runs
- Mostly 0-byte or 4KB files; one (`caddy-private-8444.log`) is 32KB
- Mostly HTTP request paths + status codes + sizes
- All from `127.0.0.1` (no external IPs in the log content itself)

**Sensitivity:** low-to-medium. These are local-test artifacts, but they:
1. Should NOT be in a public repo per common operational hygiene
2. Are **not gitignored** — should be added to `.gitignore`
3. Are tied to specific MainPID values from incident-response runs — document internal operational details

**Recommendation: these should be removed before any merge to main**, or `.gitignore` should be updated to exclude `deploy/logs/`. The files themselves are not secrets but their presence is non-standard.

### 7.6 temporary files / machine-specific data

No `/tmp/refs/*` files are in the branch (verified by full git ls-tree). Working copies are correctly held outside the repo at `/tmp/refs/`.

---

## 8. Merge-strategy recommendation

### options recap

| option | description | pros | cons |
|---|---|---|---|
| A | merge branch as-is | simple | merges 17 deployment-history commits + 24 operational log files + 2 conflicting IP records into main |
| B | one PR containing all 41 commits + corrective commits | single review | same cons as A, just delayed |
| C | split into several clean PRs | clean separation | requires cherry-picking 9 governance/evidence commits out of a 41-commit branch; the deployment commits are entangled with manifest refreshes |
| D | preserve this branch as audit/history; create clean integration branch from main using selected commits | clean integration branch; full audit trail preserved | requires identifying which 9 commits to cherry-pick; some scaffolding (security/api/db) is not yet ready for production main |

### analysis

The 41 commits decompose naturally:
- **9 governance/evidence commits** (`d2ba0c2`, `c8af8f3`, `f3261c5`, `5d8e7a1`, `4d37765`, `6c82001`, `9516b01`, `d5c0a51`, `3021a9b`): audit-ready, evidence-only, ready for a clean integration branch.
- **5 calendar-engine/scaffolding commits** (`a9707b8`, `3331903`, `6c05a91`, `236224e`, `80a05a4`): scaffolding, marked provisional. These may or may not be ready for production main depending on user policy.
- **4 documentation commits** (`690bfc1`, `b5aed8f`, `6924a7f`, `4a08f08`): docs, generally safe but some may be tied to specific commits.
- **17 deployment-history commits** (`af4d06a`, `7-28`): operator-side review history, bound to commit `7eaea55`, contains operational logs with public IP exposure. **NOT safe to merge to main as-is** per §2.
- **9 cross-validation evidence commits** (`9e3c113`, `8cb3d55`, `ffdb037`): evidence, safe.
- **1 test fix** (`ee56c50`): safe.

**Recommendation: Option D.**

This branch serves as the **audit/history branch**. A clean integration branch (e.g., `governance/protocol-v1.0-integration`) should be created from `main`, cherry-picking only the governance/evidence commits. The 17 deployment commits remain on this branch as historical record of the v0.1.0-pre1 apex bundle review cycle.

### what NOT to merge to main (without remediation)

| category | reason |
|---|---|
| All 17 deployment-history commits | bound to commit `7eaea55`; manifest stale; Caddyfile drift detected |
| `deploy/logs/*.log` (24 files) | operational artifacts; should be gitignored |
| `deploy/caddy/Caddyfile.dewata` | drift from production; repo version ≠ production version |
| `deploy/incident-report-2026-09-14.md` (lines 44) | documents conflicting apex DNS records |
| `deploy/production-deploy-manifest.txt` (lines 117-118) | documents conflicting apex DNS records |

### what CAN be merged to main (clean integration branch)

| SHA | what |
|---|---|
| `d2ba0c2` | PROTOCOL v1.0 ratification |
| `c8af8f3` | gap analysis + canonical evidence root |
| `f3261c5` | corpus-authority quarantine + STATUS.json registry |
| `5d8e7a1` | two-axis model + dispute-ID supersession |
| `4d37765` | D&R Pawukon evidence package |
| `6c82001` | first-party CALENDRICA replacement |
| `9516b01` | two-axis analysis |
| `d5c0a51` | Pancawara mapping correction |
| `3021a9b` | Wariga evidence acquisition |

### what to NOT merge until further audit

| SHA | what | reason |
|---|---|---|
| `a9707b8` | security primitives | scaffolding — needs security audit pass before main |
| `3331903` | db foundation schema | provisional — needs production-readiness audit |
| `6c05a91` | ceremony API | scaffolding — needs API contract audit |
| `236224e` | BCI web scaffolding | scaffolding — needs content audit |
| `80a05a4` | remove .gitkeep | cleanup — safe but coupled to `236224e` |
| `af4d06a` | release engineering artefacts | historical — bound to deployment history |
| `690bfc1` | correct stale release claims | depends on `af4d06a` |
| `b5aed8f` | snapshot signing ADR | historical — depends on `af4d06a` |
| `6924a7f` | phase 2 evidence report | historical summary |
| `ee56c50` | conftest db-tests-first | safe — but coupled to `3331903` |
| `9e3c113`, `8cb3d55`, `ffdb037`, `4a08f08` | calendar validation docs | safe — but document historical engine state |
| 11-28 (deployment) | apex bundle review | historical — DO NOT MERGE |

---

## 9. New blockers identified by this audit

| blocker | severity | requires |
|---|---|---|
| `test_cultural_adapters.py::test_dispute_recordable_classifications` uses obsolete namespace | medium | update test allowed set to PROTOCOL v1.0 7 classes |
| `test_wariga_evidence.py::test_sakacalendar_java_sha256_matches_recorded` silently passes if /tmp file is missing | low | convert to `@pytest.mark.skipif` or assert presence |
| `test_evidence_reingold_dershowitz_2018.py` has no `test_*` functions | low | convert `main()` to pytest tests, or move to `scripts/` |
| `test_conformance.py::test_engine_epoch_anchor_1981_08_23` is self-referential (asserts Dewata's own output) | medium | add cross-validation test against external reference (e.g., 2026-09-01 from kb.org) |
| `can_promote_ruleset_using()` does NOT enforce blocking disputes or scope_limitations | **HIGH** | implement gate that checks `blocking_disputes_pending` + `scope_limitations` |
| `deploy/caddy/Caddyfile.dewata` drift from production | low | per ABSOLUTE BOUNDARY: requires explicit user authorization to reconcile |
| `deploy/logs/*.log` (24 files, 96KB) operational artifacts in public repo | medium | add to `.gitignore` and remove from branch |
| `deploy/production-deploy-manifest.txt` bound to commit `7eaea55`, manifest is stale relative to commits 26-28 | medium | re-bind or annotate as historical |
| Public IP addresses (`54.149.79.189`, `34.216.117.25`) in 3 files | low | annotate as historical/legacy |
| PENDING-evidence-model-note-2026-09-15.md is untracked + redundant | low | delete (do not commit) |

---

## 10. Audit commit

This audit is committed to the existing `warden/phase2-foundation-20260914` branch as an audit-only commit. The commit:

- does NOT modify any code
- does NOT modify STATUS.json or disputes.json
- does NOT change any production state
- does NOT tag or release
- does NOT open a PR

After this commit, the branch HEAD advances from `3021a9b` to the new audit SHA. The new audit SHA will be the new remote branch HEAD. (See git log for actual SHA after this commit completes.)

---

## 11. Files / commits that should DEFINITELY not be merged unchanged

Per user instruction 8: "files/commits that should definitely not be merged unchanged"

| item | reason |
|---|---|
| `deploy/logs/` (all 24 .log files) | operational artifacts |
| `deploy/caddy/Caddyfile.dewata` | drift from production |
| `deploy/production-deploy-manifest.txt` | bound to commit `7eaea55`; manifest stale |
| `deploy/incident-report-2026-09-14.md` | contains historical IP exposure |
| `deploy/dns/README.md` | contains operator DNS commands |
| commits `a093d1b` through `afe8477` (17 deployment commits) | operator-side review history, not production state |
| `phase-1/src/dewatacalendar/corpus_status.py::can_promote_ruleset_using()` | does not enforce dispute gating (HIGH-severity blocker) |
| `phase-1/tests/test_cultural_adapters.py:273-282` | uses obsolete namespace |

---

## 12. Files / commits that CAN be merged cleanly

Per user instruction 8: the 9 governance/evidence commits (commits 33-41 above) form a clean integration set. A new integration branch from main with cherry-picks of these 9 commits would result in a clean main PR.

---

## 13. Final summary

| aspect | finding |
|---|---|
| governance | clean (4 commits, PROTOCOL v1.0 ratified, two-axis model, corpus quarantine) |
| evidence | clean (9 commits, bibliographic metadata + first-party CALENDRICA + Kemendikbud textbook) |
| deployment | **DO NOT MERGE UNCHANGED** (17 commits, bound to commit `7eaea55`, manifest stale, Caddyfile drift, operational logs in repo) |
| tests | 1 obsolete test (`test_dispute_recordable_classifications`), 1 self-referential test, 1 silently-passing test, 1 file with no `test_*` functions |
| public-repo suitability | mostly clean (no secrets, no copyrighted full-book material); minor concerns: 24 operational log files, public IP exposure in 3 files |
| STATUS.json | correct schema, but `can_promote_ruleset_using()` does not enforce dispute gating — **HIGH-severity blocker** |
| promotion gates | `can_satisfy_validation_gate` and `can_promote_ruleset_using` are identical functions; no dispute gating in code |
| evidence model | S3 derivative correctly recorded; CALENDRICA-vs-S3 agreement correctly framed as algorithmic corroboration |
| PENDING note | redundant, recommend deletion |

**Final recommendation: Option D.** Preserve this branch as audit/history; create a clean integration branch from `main` with only the 9 governance/evidence commits.

**No production changes made. No merge performed. No PR opened.**

stopping per instruction.
