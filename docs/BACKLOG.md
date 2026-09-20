# Prioritized Backlog — dewata.org

> **snapshot date:** 2026-09-20
> ordering: impact × risk-reduction. items already addressed or in PR pipeline are noted.

## P0 — shipped defect, no in-flight PR

### B1. Strip Saka module of unimplemented fields  ✅ DONE (PR `2a302db` ready for review)
- Removes `lunar_tithi`, `is_purnama`, `is_tilem`, `is_pangunalatri` from `SakaDate`
- Removes `purnama`, `tilem`, `nyepi` rahinan ids (depended on removed fields; nyepi predicate was unreachable)
- Removes `_new_moon_doy` stub and `PANGUNALATRI_PERIOD`
- Fixes `_saka_year_for_date` to derive from `SAKA_EPOCH_YEAR`
- Wiki: marks pangunalatri / purnama / tilem / nyepi pages as unimplemented surfaces with the three open dispute IDs; removes the three ids from id-mapping tables
- Tests: 7 new tests in `phase-1/tests/test_saka_strip.py` pin: epoch→1901, 2026→1948, four removed fields absent from `compose_day`, three removed rahinan ids never emitted across 1979-2099
- **Status:** pushed to `origin/strip-saka-unimplemented-fields-20260920`, awaiting user's PR review (per Hermes prompt: user opens the PR, Hermes does not)
- **Result:** pytest 310 pass, wiki tests 15 pass

## P1 — calendar engine correctness, but blocked on customary sign-off

### B2. Resolve the three sasih_index_drift disputes  ⛔ BLOCKED
- `DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09`
- `DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET`
- `DISPUTE-ENGINE-SASIH-INDEX-INVERSION`
- **Why blocked:** RULESET_VERSIONING.md invariant 2 — "A ruleset must list at least one customary authority." Currently `SIGNOFF.md` is empty. PROTOCOL.md says: "Never resolve cultural disputes by silently changing formulas, expected values, reference classifications, or sign-off records. Prepare the evidence and decision packet for the appropriate reviewer."
- **What Hermes can do unblockedly:** (a) write a decision packet summarising the three disputes, the three sources (kalenderbali.info, Java library, KB Org), and the proposed engine change; (b) classify each into a candidate bucket (epoch_offset / rule_drift / calendar_variant). Implementation is gated on customary sign-off.

### B3. Move ruleset lock forward  ⛔ BLOCKED
- `RULESET_VERSION` in `phase-1/src/dewatacalendar/rulesets.py` is `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0`. Bumping without customary sign-off violates invariant 1 (cultural sovereignty) and invariant 2 (authority ordering).
- **What Hermes can do unblockedly:** freeze the strip PR as a separate commit ahead of any ruleset bump, so the bug-fix can ship without claiming to be a ruleset revision.

## P2 — operational readiness

### B4. main branch protection
- The user prompt mentions "unprotected main" as part of the prior Codex assessment; could not verify (no GitHub token at runtime). **Action:** ask user to verify and add a branch protection rule that requires CI pass + 1 review before merge to main. (Hermes cannot do this — admin action.)

### B5. Deployment of `2a302db` to production api
- The strip PR fixes the saka-year bug and removes four emitted-but-broken fields. Production still emits the broken output. Deploy requires: (a) user opens the PR (per Hermes prompt); (b) PR merges; (c) user runs the deploy runbook (out of scope for Hermes per PROTOCOL §0).
- **What Hermes can do unblockedly:** prepare the deploy runbook step (rebuild wheel in `.venv`, `systemctl restart dewata-api.service`, verify via `curl https://api.dewata.org/dsp/v0.1/calendar/date/2026-09-20 | jq .saka.saka_year` returns `1948` not `48`).

### B6. Snapshot publication pipeline
- ARCHITECTURE.md §8 specifies daily `tar.zst` + age signature + cloudflare-fronted minio + mirror partners (mempalace.gh, mastodon).
- ARCHITECTURE.md §11 lists `datasets.dewata.org` as a placeholder (currently 503). The pipeline is described but no code exists in `/opt/dewata.online` for it.
- **What Hermes can do unblockedly:** draft `phase-1/tools/snapshot.py` (CLI: `dewata-snapshots snapshot today`) that emits a deterministic tar.zst of conformance corpora + STATUS.json + sha256. age-signing should NOT be implemented by Hermes per PROTOCOL.md ("Implement Age as a signature mechanism" is on the prohibited list — so age is out, but the tar.zst and sha256 part is in scope).

### B7. CI / CD gap: api deploys are manual
- The phase-1 API runs from a `.venv` editable install at `/opt/dewata.online/.venv`; CI runs `pip install -e .[dev]`. There is no `deploy phase-1` job in `.github/workflows/tests.yml` — only the pytest job.
- **What Hermes can do unblockedly:** add a `phase-1-api-deploy.yml` workflow that gates deploy on main + manual dispatch, but the actual deploy steps are user-only per PROTOCOL.

### B8. Backups + DR
- ARCHITECTURE.md §12 says nightly `pg_dump` + `b2:dewata-prod/`. Could not verify this is wired up. **Action:** ask user to verify backup script exists and runs.

## P3 — user-facing completeness

### B9. bci / protocol / datasets surface hosts
- All three return 503 by design. Each requires phase-2/3 work that is not in this repo's current scope.
- **What Hermes can do unblockedly:** nothing until phase-2 lands. The Caddyfile currently returns 503 with a clear banner; users are not misled.

### B10. Wiki completeness
- 322 wiki pages across 4 statuses: `informational` (37), `pending_customary_review` (101), `implementation_definition` (108), `verified_source` (78).
- Most pages reference the engine. The strip PR updated 14 pages; the rest still describe the pre-strip engine.
- **What Hermes can do unblockedly:** re-run a script that diffs `phase-1/src/dewatacalendar/*.py` against wiki term pages and flags references to removed fields. (Best done after the strip PR merges so the wiki reflects what is actually deployed.)

### B11. Bilingual translation quality
- Most ban stubs defer to id/en. Bahasa Bali translations await customary review per CONTRIBUTING.md.
- **What Hermes can do unblockedly:** add a glossary cross-check test that ensures each `language_variants.ban.spelling` matches an entry in `phase-1/src/dewatacalendar/i18n.py` or `README_BAL.md`. (Actually already exists — `wiki/tests/test_metadata.py::test_bahasa_bali_spelling_only_from_repo_i18n_table`. Status: passing.)

### B12. Mobile usability + accessibility
- Could not verify from the read-only inspection; the static landing uses semantic HTML, `lang="ban"`, viewport meta, `role` attributes. But deep audit (WCAG 2.1 AA, keyboard nav, screen-reader flows) requires an actual browser pass.
- **What Hermes can do unblockedly:** add axe-core or pa11y to the wiki build. (User authorisation needed before adding a build-time accessibility check.)

## P4 — observability + ops

### B13. Metrics endpoint
- ARCHITECTURE.md §12 says `/metrics` per service scraped by host-level prom. Not present in phase-1 source.

### B14. Log rotation
- Caddyfile has `roll_size 50mb roll_keep 3` for the private log; API has `--no-access-log` (so no log to rotate). Acceptable for v0.1.

### B15. CI provenance test
- `phase-1/tests/test_evidence_provenance.py` exists and gates PR #12 (evidence-cs-provenance-20260920). This is good.

## What is out of scope

- Tourism / navigation / routing (per ARCHITECTURE.md §16)
- Payment, ads, "ceremony of the day" galleries
- Any change to the Saka ruleset that has not been customary-signed

## Items explicitly not on this backlog

- **v0.2 mesh, v0.2 banjar CRUD** — design is in ARCHITECTURE.md; no source in this repo yet. Belongs to a different phase / repo.
- **WhatsApp bridge** — phase 6, not started.
- **USSD hotline** — phase 7, not started.
- **time-machine archive** — phase 8.
