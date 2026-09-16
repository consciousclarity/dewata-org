# Integration Manifest — Governance/Evidence Clean Branch

Compiled: 2026-09-16.
Purpose: documents the provenance of the clean governance/evidence
integration branch `integration/governance-evidence-20260916`.
This document describes integration provenance only; it does not
authorize any calendar-semantic change, deployment, or research.

== base SHA ==

`origin/main` = `5919cf4bf0b96a7ae0b3ab126e46a24e153542d7`
                (deploy: add cloudflared tunnel fallback runbook)

== source history branch ==

`warden/phase2-foundation-20260914` at stabilization baseline
`53ec52bc8e281bb101dfeca0555ff0b664e63e35`
(Stabilization: promotion fail-closed unconditionally, claim-scoped reference only)

== final clean branch HEAD ==

`integration/governance-evidence-20260916` HEAD = final commit on
this branch after the integration-specific manifest commit below.

== selected source commits successfully incorporated ==

15 governance/evidence commits cherry-picked from the Warden history
branch in dependency order. Cherry-picking creates new SHAs; original
SHAs are not preserved.

### A. pre-protocol evidence/audit foundation (4 commits)

| original SHA | subject |
|---|---|
| `4a08f08` | docs(calendar): AUDIT_v0.1.0-audit1 -- pre-freeze source/epoch audit |
| `9e3c113` | docs(calendar): independent reference validation vs kalenderbali.info (Sept 2026) |
| `8cb3d55` | docs(calendar): cross-validation vs 3 reference implementations |
| `ffdb037` | docs(calendar): kalenderbali.org (KBD) cross-validation - real findings |

### B. ratified governance + evidence model (4 commits)

| original SHA | subject |
|---|---|
| `d2ba0c2` | docs(governance): ratify Hermes Operating Protocol v1.0 |
| `c8af8f3` | docs(audit+evidence): commit gap analysis + canonical evidence root under PROTOCOL v1.0 |
| `f3261c5` | feat(conformance): corpus-authority quarantine + STATUS.json registry |
| `5d8e7a1` | refactor(conformance): split corpus status into two-axis model + dispute-ID supersession + .gitignore exception |

### C. Pawukon/CALENDRICA evidence chain (4 commits)

| original SHA | subject |
|---|---|
| `4d37765` | D&R Pawukon evidence package + CALENDRICA 4.0 first-party evidence |
| `6c82001` | Corrective evidence/provenance pass: replace Calixir with first-party EdReingold/calendar-code2 |
| `9516b01` | Two-axis analysis: RAW_GREGORIAN_MAPPING vs PHASE_NORMALIZED_FORMULA |
| `d5c0a51` | Corrective audit: Pancawara mapping bug found, retracted false claim |

### D. Balinese Wariga evidence (1 commit)

| original SHA | subject |
|---|---|
| `3021a9b` | Wariga source evidence acquisition + audit corrections |

### E. final gate/test stabilization (2 commits)

| original SHA | subject |
|---|---|
| `037e0be` | Corrective evidence-gate + test-integrity pass |
| `53ec52b` | Stabilization: promotion fail-closed unconditionally, claim-scoped reference only |

All 15 cherry-picks succeeded without conflicts.

== any source commit that could not be applied ==

None. All 15 cherry-picks succeeded cleanly.

== excluded commit categories ==

The following categories of commits from the Warden history branch
were INTENTIONALLY EXCLUDED from the clean integration branch.

### excluded: deployment commits

The Warden branch contains 17 operator-side deployment review commits
covering the v0.1.0-pre1 apex bundle review cycle. These reference
deployment artifacts (production-deploy-manifest.txt, install scripts,
rollback scripts, lifecycle-test outputs, Caddyfile snapshots, etc.)
that intentionally will not exist in the clean governance/evidence
integration branch.

Excluded SHAs (representative, not exhaustive): `a093d1b`, `283df62`,
`22f2675`, `cd84d4d`, `c04be70`, `5f88be7`, `064833a`, `ba8bd2a`,
`7b3f1e0`, `21c3db1`, `e702026`, `cea73c6`, `5237d1a`, `badc617`,
`7eaea55`, `ad137e8`, `2dae450`, `afe8477`, `af4d06a`.

### excluded: `0fb0e28` (mixed-branch audit)

`0fb0e28` Audit: remote branch merge readiness, 41-commit
classification is INTENTIONALLY EXCLUDED.

That commit is specifically an audit of the mixed Warden/history
branch, including deployment files that intentionally will not exist
in the clean branch. Per user instruction: "Preserve it on the
history branch only."

### excluded: scaffold/feature commits (database/API/security/web)

Per user instruction, the clean branch is governance/evidence/
conformance only. Excluded:
- database foundation schema (`3331903`)
- ceremony API foundation (`6c05a91`)
- visibility-tier security primitives (`a9707b8`)
- BCI web scaffolding (`236224e`, `80a05a4`)
- operational release engineering (`af4d06a` partial)
- documentation scaffolding (`690bfc1`, `b5aed8f`, `6924a7f`)
- database/web tests (`conftest.py`, `db/*`, `api/*`, `security/*`)
- choret fixtures (`ee56c50`)

### excluded: 0fb0e28 rationale

The Warden branch at stabilization baseline 53ec52b contains 44
commits. Of those, 29 are non-governance/evidence and were excluded.
The clean integration branch contains 15 governance/evidence commits
plus 1 integration manifest commit = 16 total.

== why 0fb0e28 remains history-only ==

`0fb0e28` is the audit report on the **mixed** Warden/history branch.
It documents:
- 41-commit inventory across deployment + governance + evidence
- deployment drift between repo and production
- 17 deployment-history commits that intentionally will not merge
- operational artifacts (deploy/logs/*.log) that need .gitignore
- public IP exposure in deployment docs

None of these concerns apply to the **clean** integration branch —
the clean branch is by construction narrower than the history branch.
Including `0fb0e28` would either:
- reference deployment files that do not exist in the clean branch
- contradict the deliberate narrowing described in the integration
  plan
- duplicate evidence-package inventory that lives more usefully on
  the history branch as the authoritative audit record

Therefore `0fb0e28` is preserved on `warden/phase2-foundation-20260914`
as the audit record of the history branch and is NOT carried into the
clean integration branch.

== test results (final clean branch) ==

total collected: 215
passed:           215
failed:           0
skipped:          0

compared to the Warden branch stabilization baseline (243 passed,
8 skipped, 0 failed):
- 28 tests fewer (the difference is entirely from excluded
  scaffolding: ceremony API tests, db tests, security tests, db
  conftest)
- 8 fewer skips (all skipped tests on Warden were ceremony API tests
  gated on DEWATA_TEST_DSN, which are part of excluded scaffolding)

NO unexplained failure. The 28-test delta is exactly the count of
excluded scaffolding tests.

== algorithm-semantic diff result ==

Compared `integration/governance-evidence-20260916` to `origin/main`:
68 files changed, 22019 insertions(+), 82 deletions(-).

zero changes to algorithm implementation files:
  - no `pawukon.py` changes
  - no `wewaran.py` changes
  - no `saka.py` changes
  - no `rahinan.py` changes
  - no `rulesets.py` changes
  - no Wuku table changes
  - no epoch constant changes
  - no production API behavior changes

all changes are in evidence/audit/conformance/status machinery and
the related test files.

== evidence-path integrity result ==

dangling-references scan: 0 repository artifacts missing
all STATUS.json corpus_file references resolve to existing artifacts
OR are explicitly null with scope_limitations notes documenting why
the source is held at /tmp/refs/ instead of in the public repo.

Specifically:
- `reingold_dershowitz_2018_calendrica_4_0_calixir`: corpus_file=null;
  Calixir secondary copy intentionally NOT in public repo per
  Calixir restrictive license header. Metadata + SHA-256 in
  calendrica-source/METADATA.json.
- `wariga_babadbali_com`: corpus_file=null; babadbali.com is an
  external source held at /tmp/refs/babadbali-pancawara.html and
  /tmp/refs/babadbali-wuku.html for verification only. SHA-256
  fingerprints recorded in STATUS reason field.

classification of references:
  repository artifact (in-tree): 9 entries (wariga_kemendikbud,
    wariga_edysantosa Java, calendrica firstparty files, evidence
    markdown/json)
  external source (held at /tmp/refs/, NOT in repo): 2 entries
    (calendrica Calixir secondary, babadbali.com)
  intentionally unavailable source: 2 entries (wariga_suparta
    ardhana_2006, wariga_putra_manik_ariana_2009 — both INELIGIBLE
    bibliographic metadata only, corpus_file=null)
  historical-only reference: 0 dangling references

== known unresolved calendar disputes ==

The following PROTOCOL v1.0-class disputes remain PENDING and are
NOT resolved by this integration:

| dispute | class | blocking | subject |
|---|---|---|---|
| `DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15` | calendar_semantics (reclassified mapping_phase) | yes | +84 mod 210 offset between Dewata and CALENDRICA |
| `DISPUTE-wewaran-asatawara-special-case-formula-2026-09-15` | calendar_semantics (formula_semantics) | yes | Astawara special-case at Wuku Dungulan |
| `DISPUTE-wewaran-caturwara-transitive-dependency-on-asatawara-2026-09-15` | calendar_semantics (formula_semantics) | transitive | depends on asatawara |
| `DISPUTE-wewaran-sangawara-special-case-formula-2026-09-15` | calendar_semantics (formula_semantics) | yes | Sangawara special-case: 3 days (CALENDRICA) vs 4 days (Kemendikbud + S3) |
| `DISPUTE-wewaran-dasawara-urip-5-table-2026-09-15` | calendar_semantics (formula_semantics) | yes | Dasawara urip_5 cyclic rotation: 198/210 disagree |
| `DISPUTE-wewaran-dwiwara-parity-basis-2026-09-15` | calendar_semantics (reclassified indexing_representation) | non-blocking | parity input differs |
| `DISPUTE-pancawara-convention-shift-dewata-vs-cultural-2026-09-15` | calendar_semantics (reclassified indexing_representation) | non-blocking | mapping A (Paing at 1) vs Mapping B (Umanis at 1) |

The above disputes are recorded in
`phase-1/docs/runbook/disputes.json` per PROTOCOL v1.0 §3.2
append-only structured resolution records. They are NOT closed by
this integration pass.

== statement that ruleset promotion remains disabled ==

per user instruction:
- can_promote_ruleset_using(...) returns False unconditionally
- no caller input — including a complete RulesetPromotionContext
  with arbitrary strings as governance_authorization_artifact — can
  authorize a promotion today
- ruleset-promoting sources in current STATUS: 0
- the executable promotion-authority mechanism does not exist yet
- claim-validating sources in current STATUS: 0 (no STATUS entry has
  eligible_claim_ids populated; per instruction 8 we did NOT
  populate them during this integration)

== statement that no production action occurred ==

- production Caddyfile unchanged (still `4f06ce6f...` on production)
- no /root/.env.dewata.online modification
- no cloudflare/dns/tunnel modification
- no production database or systemd modification
- dewata-caddy.service MainPID = 3805187 (unchanged)
- https://dewata.org/ HTTP/2 200

== file count changed vs main ==

origin/main: 219 tree files in phase-1/, docs/, deploy/, ARCHITECTURE.md,
README.md, LICENSE, etc. (verified by `git ls-tree`).

integration/governance-evidence-20260916 HEAD: see `git diff origin/main...
integration/governance-evidence-20260916 --stat` — 68 files changed,
22019 insertions(+), 82 deletions(-).

Net effect: 68 files changed. Of these:
- 56 new files (evidence artifacts, test files, conformance files,
  docs)
- 12 modified files (mostly governance/conformance files)
- 0 deletions of pre-existing origin/main files

The clean branch is INTENTIONALLY narrower than the Warden history
branch (44 → 15 commits, ~28 fewer tests, no deployment files).

== remote branch HEAD (after push) ==

`integration/governance-evidence-20260916` HEAD = SHA of the final
commit on this branch (the integration-manifest commit below).
origin/main HEAD = `5919cf4` (unchanged).

== production confirmation ==

no production action taken. production state unchanged:
- dewata-caddy.service MainPID = 3805187
- https://dewata.org/ HTTP/2 200
- /opt/dewata.online/ untouched
- /root/.env.dewata.online untouched
- no cloudflare/dns/tunnel modification
