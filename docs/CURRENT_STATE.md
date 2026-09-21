# Current State — dewata.org

> **snapshot date:** 2026-09-20
> **observed by:** Hermes (lead implementation agent)
> **scope:** what exists, what is live, how each claim was verified.

## What dewata.org is

A protocol for **recording, certifying, and preserving Balinese customary ceremony and cultural record**. Built for banjar / pura / desa adat — explicitly **not** for tourists or "what's open" navigation. See `README_BAL.md`, `README_ID.md`, `ARCHITECTURE.md §0`.

Five primitives: *piodalan*, *odalan*, *ngayah*, *paruman*, *pecalang-coverage*.

## What is live in production (verified)

| surface | URL | status | verified at |
|---|---|---|---|
| apex landing | https://dewata.org | 200, three-language (ban/id/en) stub | 2026-09-20 |
| API | https://api.dewata.org | 200, calendar-only DSP v0.1 | 2026-09-20 |
| Wiki | https://wiki.dewata.org | 200, static mkdocs build | 2026-09-20 |
| bci (cultural index) | https://bci.dewata.org | 503 — placeholder, "not yet shipped (v0.1.0)" | 2026-09-20 |
| protocol (DSP spec site) | https://protocol.dewata.org | 503 — placeholder | 2026-09-20 |
| datasets | https://datasets.dewata.org | 503 — placeholder, snapshot publication not shipped | 2026-09-20 |

**Live API surface** (`curl https://api.dewata.org/openapi.json`):
- `GET /health`
- `GET /`
- `GET /dsp/v0.1/calendar/ruleset`
- `GET /dsp/v0.1/calendar/date/{YYYY-MM-DD}`
- `GET /dsp/v0.1/calendar/range`

The ARCHITECTURE.md §4 specifies ~22 DSP endpoints (banjar, pura, ceremonies, mesh, visibility tiers, datasets, well-known, signing keys, webhook). **None of these are deployed.** The production API exposes only the calendar endpoints (phase-1).

## What is in the repository but not yet shipped

- **phase-2 work**: banjar / pura / ceremony identity model, CRUD, visibility tier enforcement (`/opt/nusa.business/` is unrelated).
- **phase-3 work**: cultural mesh, mirror subscriptions, signed SSE feeds.
- **phase-5+**: whatsapp bridge, USSD hotline, time-machine archive.
- **<id>.<kab>.dewata.org** subdomains: schema exists in `registry/*.tsv` (gianyar pilot: 22 banjar + 10 pura), no DNS delegation yet.
- **operators + cultural folders** in `phase-1/docs/`: handbook + ops runbooks exist but are draft.

## Repository architecture

```
/opt/dewata.online
├── ARCHITECTURE.md          full engineering plan (565 lines, scoped v0.1→v1)
├── README.md, README_BAL.md, README_ID.md, README_EN.md   language-split READMEs
├── CITATION.cff, LICENSE   MIT + cultural-sovereignty clause
├── CONTRIBUTING.md, CONTRIBUTING_ID.md
├── docs/PROTOCOL.md         Hermes Operating Protocol (ratified 2026-09-15)
├── phase-1/                 calendar engine (shipped)
│   ├── src/dewatacalendar/  the Python package (pawukon, saka, wewaran, rahinan, dsp, i18n, rulesets, cross_validation, runbook, corpus_status, exceptions)
│   ├── src/api/             fastapi entry — `api.main:app` mounted on 127.0.0.1:8765
│   ├── conformance/         corpora + STATUS.json (two-axis evidence model, claim-scoped)
│   ├── docs/runbook/        RULESET_VERSIONING, DISPUTE_REVIEW_PROTOCOL, SIGNOFF, CHANGELOG, RELEASE_v0.1.0, disputes.json
│   ├── docs/audit/          GAP_ANALYSIS_v1.0, REFERENCE_VALIDATION_*, CROSS_VALIDATION_*
│   ├── docs/handbook/       HANDBOOK_ID.md, HANDBOOK_BAL.md  (operator-facing)
│   ├── tests/               19 test files, 310 tests pass in 16s
│   └── pyproject.toml       pytest config, src/ on pythonpath
├── wiki/                    multilingual knowledge base (mkdocs-material)
│   ├── docs/{ban,id,en}/    term pages with YAML front-matter
│   ├── tests/               15 metadata + reproducibility tests
│   └── Makefile, mkdocs.yml, requirements.txt
├── deploy/
│   ├── caddy/Caddyfile.dewata    private vhost for *.dewata.org on :8443
│   ├── systemd/{dewata-api,dewata-caddy}.service
│   ├── bin/, atomic/, dns/      deploy tooling
│   ├── logs/                    access + error logs
│   ├── runbook/                 deploy procedures
│   └── www/                     versioned static releases (apex + wiki)
├── registry/
│   ├── banjar.gianyar.tsv       22 rows, pilot scope
│   └── pura.gianyar.tsv         10 rows
├── scripts/                       verify.sh, helpers
└── .github/workflows/tests.yml    pytest + wiki pytest (CI)
```

## How a code change reaches production

```
local edit → branch → push to origin
    → CI: pytest phase-1 (310 tests), pytest wiki/tests (15 tests)
    → PR review (technical + cultural, two-tier per CONTRIBUTING)
    → merge to main
    → deploy runbook: build apex + wiki release dirs under deploy/www/
    → point DEWATA_RELEASE_ROOT / DEWATA_WIKI_RELEASE_ROOT env vars
    → `systemctl restart dewata-caddy.service` (NOT reload — see caddy-reload-policy.md)
    → for phase-1 API: rebuild wheel, restart dewata-api.service (out of scope for Hermes per PROTOCOL.md §0)
```

The **strip-saka-unimplemented-fields-20260920** PR (commit `2a302db`) is the most recent work. It is pushed, **not merged, not deployed**. It fixes the saka-year bug at the epoch, removes four unimplemented fields from the SakaDate dataclass, and removes the three rahinan ids (`purnama`, `tilem`, `nyepi`) that depended on those fields.

## Verified defects (from live inspection)

1. **saka_year bug in production** — `GET /dsp/v0.1/calendar/date/2026-09-20` returns `saka_year: 48` (was `gregorian_year - 1979`); for `1979-03-29` it returns `0`, contradicting `SAKA_EPOCH_YEAR = 1901`. **Fixed in `2a302db`, not yet deployed.**
2. **`lunar_tithi` / `is_purnama` / `is_tilem` / `is_pangunalatri` in production API** — emitted but backed by `return 88` stub and arithmetic windows. Documented as implemented, were never implemented. **Removed in `2a302db`.**
3. **Disputed sasih indexing on main** — three pending `sasih_index_drift` disputes:
   - `DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09`
   - `DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET`
   - `DISPUTE-ENGINE-SASIH-INDEX-INVERSION`
   All three are flagged in the saka.py module docstring after the strip. **No attempt to resolve them in the strip PR; this is correct per PROTOCOL.**
4. **bci / protocol / datasets subdomains** — Caddyfile serves 503 by design (per `deploy/caddy/Caddyfile.dewata`). Matches ARCHITECTURE.md phasing. **Not a defect.**
5. **Calendar page on dewata.org** is a stub with explicit "under development" banner pointing users at the API. **Matches ARCHITECTURE.md phasing.**

## Strengths observed

- **Wiki metadata discipline is high.** 15 wiki tests pass; front-matter validation catches the harness-leak regression of 2026-09-19 (commented in `wiki/tests/test_metadata.py`). `_iter_all_md_with_frontmatter` and `test_front_matter_has_only_declared_keys_and_subkeys` are good.
- **Cultural governance is real, not performative.** `STATUS.json` schema v3.0 makes `can_promote_ruleset_using` and `can_be_described_as_ground_truth` return FALSE unconditionally. `SIGNOFF.md` is empty, with a clear "human reviewers fill these in. do not auto-populate" warning. Disputes are tracked with `recorded_at`, `evidence`, `source`, `severity`, `blocking`.
- **Two-tier PR review** is documented in CONTRIBUTING.md (technical + cultural, non-dewata-affiliated reviewer). Even though enforcement is not yet automated, the contract is on the page.
- **CI is real and fast.** 310 + 15 tests run in ~30s total. `fetch-depth: 0` for provenance tests; `pytest -q -rs` matches what the workflow runs.
- **Operational boundaries are codified.** PROTOCOL.md §0 enumerates the standing production safety boundary. There is no ambiguity about what Hermes may or may not do to production.
- **Release engineering is sane.** Versioned static releases for apex + wiki, env-var indirection, restart-not-reload for caddy, no merge-on-ruleset-bump-without-signoff.
- **Five-adat primitives + computed/registered/predicted/operational fact distinction + visibility tiers** are all designed coherently in ARCHITECTURE.md §3. The schema enforces the four-level provenance and tier promotion is forbidden.

## Corrections follow-up to PR #15 (2026-09-20)

The merged PR #15 returned from independent review with five findings
(F1-F5). The corrections live on branch
`strip-saka-corrections-r2-20260920` against main `802f9263`. They
preserve all merged work, including Claude's metadata changes
(`48dc5bc`, `25cbfde`, `25f9160`) and the project memory documents
(`cb1dc90`). The corrections:

- F1: public `saka_year` is `None`; raw value lives in
  `saka_year_diagnostic_january_rollover` for the harness and dispute
  packet.
- F2: `CANDIDATE_ID = "candidate-2026-09-20-strip-corrections-r2"`
  separates the development artifact from the frozen
  `RULESET_VERSION`. Every `compose_day` and CLI artefact carries both.
- F3: capability metadata reflects the runtime-of-record
  (`IMPLEMENTED_RAHINAN_IDS` = 9, `purnama_counted=False`,
  `tilem_counted=False`, `nyepi_counted=False`).
- F4: `nampih_rule_actual` renamed to `nampih_rule_observed`; index 13
  named `Nampih Sada`; explicit uncited note.
- F5: wiki generator's `RHINAN_IDS` excludes purnama/tilem/nyepi; a
  separate `RHINAN_UNEMITTED` list writes the unimplemented surfaces
  with the three dispute IDs; `RHINAN_NAMED` no longer claims the
  engine emits those.

Verification (corrections branch, off `802f9263`):
- `phase-1` tests: 324 passed, 0 failed (was 310 before this branch).
  Includes 4 SBCL tests that run locally because `sbcl` is installed;
  CI skips them because `sbcl` is not installed in the GitHub runner.
- `wiki` tests: 20 passed, 0 failed (was 15 before this branch).
- HTTP integration tests: 4 live uvicorn endpoints asserted
  `candidate_id`, `unimplemented_observances`, `saka_year=null`,
  `saka_year_diagnostic_january_rollover=1948`, and the explanatory
  `note` field all reach the wire.

## Uncertainties and unknowns

- **Branch protection status on `main`** — could not verify (no `gh` CLI, no working GitHub token in the runtime env; the earlier Bash attempts to `/api.github.com/.../protection` returned 401). The PROTOCOL says Hermes may not push to main or merge, so this is academic from the agent's POV — but a reviewer checking from the GitHub UI should confirm main is protected.
- **Whether any conventional sign-off has actually occurred** — `SIGNOFF.md` is empty. The release note (`RELEASE_v0.1.0.md`) flags this as "BELUM" (not done). Three cross-validation disputes are pending. Until customary sign-off arrives, ruleset promotion remains blocked by the gate predicates in `STATUS.json`.
- **Dispute count** — 27 disputes total: 23 pending, 3 superseded, 1 resolved. Three pending are `sasih_index_drift` (the open sasih calibration problem). All other 24 are pre-strip-PR or unrelated (wewaran drift, pawukon epoch, i18n, bibliographic verification).
- **Live API's ruleset version is `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.2.0`** — this is what the broken saka.py is shipped under. The strip PR does not bump this string (it's an unvalidated ruleset anyway, and bumping without customary sign-off would violate RULESET_VERSIONING.md invariant 1).

## Documentation ↔ production differences

| claim | source | observed |
|---|---|---|
| ARCHITECTURE.md §4 lists ~22 DSP endpoints | `phase-1/src/api/main.py` | only 4 are mounted; others are not in source yet |
| ARCHITECTURE.md §11 lists Cloudflare Access + DNS delegation for `*.dewata.org` | DNS reality | `bci.`, `protocol.`, `datasets.` resolve to 62.72.7.218 (per Caddyfile `:8443`) but the Caddyfile responds 503 for those vhosts — so DNS is partially delegated but routing is a placeholder |
| README_BAL/ID describe a protocol for **banjar / pura / desa adat** | repo | correct; phase-2 work is in flight but not shipped |
| `registry/banjar.gianyar.tsv` claims 22 banjar pilot entries | file | 22 rows present; **but** the registry is TSV seed data only, not yet authoritative records |
| `phase-1/conformance/STATUS.json` says Cunningham 1994 is UNVERIFIED | repo | correct — the citation could not be bibliographically verified |
