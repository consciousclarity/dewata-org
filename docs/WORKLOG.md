# Work Log — dewata.org

> rolling log. newest entry first.

## 2026-09-20 (later) — strip-saka-corrections-r2-20260920

**Context.** PR #15 was merged. Independent review of the merged state returned **request changes** for the prior branch (`strip-saka-unimplemented-fields-20260920`, head `253dd8a`) — five findings (F1-F5). This follow-up branch (`strip-saka-corrections-r2-20260920`) is corrections-only against main `802f9263`. **All merged work is preserved**, including Claude's `48dc5bc`, `25cbfde`, `25f9160`, `253dd8a` metadata changes and the project memory documents from `cb1dc90`.

**Base SHA.** `802f9263d18946694e8f9285d66181e4caf4f55a` (main HEAD = merge of PR #15).

**Reviewer.** Codex. PR target was #15 (base `65784ce`, head `253dd8a`). Decision: request changes; do not merge or deploy as written.

**Findings addressed (corrections-only, on top of merged state):**

- **F1 (P1).** Year-boundary change separated from field removal. Public `saka_year` is now `None` in `SakaDate` / `CalendarDay`. Raw January-rollover value lives in a separate `saka_year_diagnostic_january_rollover` field for the harness and dispute packet. Failing regressions for `2026-01-01`, `2026-03-18`, `2026-03-19` added.
- **F2 (P1).** New `CANDIDATE_ID = "candidate-2026-09-20-strip-corrections-r2"`. `compose_day` and the CLI both surface `candidate_id` alongside `ruleset`. `RULESET_VERSION` is unchanged.
- **F3 (P2).** Capability metadata corrected. `purnama_counted=False`, `tilem_counted=False`, `nyepi_counted=False`. `named_days = len(IMPLEMENTED_RAHINAN_IDS) = 9` (the runtime-of-record count, asserted by a 210-day scan). `pangunalatri_days=63` survives as `pangunalatri_days_declared` with `pangunalatri_implemented=False` (Claude's `48dc5bc`, preserved verbatim).
- **F4 (P2).** Nampih rule relabelled `nampih_rule_observed`; index 13 named `Nampih Sada`; explicit uncited note. The `nampih_rule_declared` field (Claude's `25cbfde`) is preserved verbatim with its explanation that the declared rule has never been implemented.
- **F5 (P2).** Wiki generator split `RHINAN_IDS` (9 emitted) from `RHINAN_UNEMITTED` (3 unimplemented, with `dispute_ids`). The purnama/tilem entries were removed from `RHINAN_NAMED` (they would otherwise overwrite the unimplemented status via last-write-wins). New round-trip test `wiki/tests/test_emit_term_pages_preservation.py` runs the writer against a temp copy of the wiki docs and asserts the unimplemented status is preserved.

**Cross-validation handles the unavailable year correctly.** `cross_validate_one` falls back to the diagnostic field when the public `saka_year` is `None`, and records the diagnostic-only comparison in `field_notes` so downstream consumers see the unavailable status, not a silent match.

**Public contract change.** `CalendarDay` now carries `candidate_id`, `unimplemented_observances`, and `note` fields. Live HTTP responses tested by `phase-1/tests/test_http_integration_corrections.py` (boots a real uvicorn instance, hits `/dsp/v0.1/calendar/date/2026-09-20` with httpx, asserts `candidate_id`, `unimplemented_observances`, `saka_year=null`, `saka_year_diagnostic_january_rollover=1948`, and the explanatory `note` all reach the wire).

**Files changed.**
- `phase-1/src/dewatacalendar/saka.py` (SakaDate adds `saka_year: int | None` and `saka_year_diagnostic_january_rollover: int`; `saka_for_gregorian` populates the diagnostic)
- `phase-1/src/dewatacalendar/rulesets.py` (add `CANDIDATE_ID`, `IMPLEMENTED_RAHINAN_IDS`, `UNIMPLEMENTED_RAHINAN_IDS`; rename `nampih_rule_actual` → `nampih_rule_observed`; correct rahinan `*_counted` flags; add `public_saka_year_returned=False` and `saka_year_diagnostic_field` references)
- `phase-1/src/dewatacalendar/api.py` (`CalendarDay` adds `candidate_id`, `unimplemented_observances`, `note`; `compose_day` populates them)
- `phase-1/src/dewatacalendar/cross_validation.py` (fall back to diagnostic field when public `saka_year` is `None`; record diagnostic-only comparison in `field_notes`)
- `phase-1/src/dewatacalendar/cli.py` (`cmd_ruleset` prints `candidate_id` alongside `version`)
- `phase-1/tests/test_saka_strip.py` (preserve merged regression; the two merged tests now assert on the diagnostic field instead of `saka_year` so they continue to pin the underlying epoch anchor)
- `phase-1/tests/test_saka_strip_corrections.py` (NEW: 10 tests pinning F1-F4 acceptance)
- `phase-1/tests/test_http_integration_corrections.py` (NEW: 4 live HTTP tests pinning F2 + F5 acceptance at the wire)
- `wiki/scripts/emit_term_pages.py` (split `RHINAN_IDS` from `RHINAN_UNEMITTED`; remove purnama/tilem from `RHINAN_NAMED`)
- `wiki/tests/test_emit_term_pages_preservation.py` (NEW: 5 tests pinning F5 acceptance, including a writer round-trip)
- `docs/CURRENT_STATE.md`, `docs/BACKLOG.md`, `docs/DECISIONS.md` (append D9-D13 supersession notes; preserve all merged content)

**Files NOT modified.** Nothing under `phase-1/src/api/`, `phase-1/docs/runbook/disputes.json`, `phase-1/conformance/STATUS.json`, `deploy/`, `registry/`, `wiki/docs/{en,id}/**` content files. The three Sasih disputes cited in the saka.py module docstring are still cited, still pending, still not resolved.

**Verification.**
- `cd phase-1 && python -m pytest -q -rs` → **324 passed**, 0 failed. Baseline on `802f9263` was 310 passed. +14 new tests: 10 in `test_saka_strip_corrections.py` + 4 in `test_http_integration_corrections.py`.
- SBCL tests: `python -m pytest tests/test_evidence_calendrica_runtime.py -v -rs` → **4 passed**. They run locally because `sbcl 2.2.9` is installed at `/usr/bin/sbcl`. **CI skips them** because the GitHub Actions runner does not have `sbcl` installed; the test guards `pytest.skip("sbcl not installed; CALENDRICA runtime test skipped")` activates there.
- `cd wiki && python -m pytest wiki/tests -q -rs` → **20 passed**, 0 failed. Baseline was 15. +5 new tests in `test_emit_term_pages_preservation.py`.
- CLI smoke: `python3 -m dewatacalendar ruleset` shows `version`, `candidate_id`, and `metadata`. `python3 -m dewatacalendar date 2026-09-20` shows `saka_year: null`, `saka_year_diagnostic_january_rollover: 1948`, `candidate_id: candidate-2026-09-20-strip-corrections-r2`, `unimplemented_observances: [purnama, tilem, nyepi]`, `note: "empty rahinan list -- engine does not currently compute: ..."`.
- HTTP smoke: `httpx.get('http://127.0.0.1:8137/dsp/v0.1/calendar/date/2026-09-20')` returns the same fields in JSON. Verified by `phase-1/tests/test_http_integration_corrections.py`.

**Remaining blockers (not addressed in this branch).**
- PR not yet opened — Alejandro opens it per standing instruction.
- Production deploy — out of scope per PROTOCOL.md §0.
- Three sasih_index_drift disputes remain pending; this branch does not touch them.
- Branch protection on main — owner-admin only.
- Decision packet for the three sasih disputes (Codex increment 4 from the prior review) — separate doc; not a code change.
- Astronomy prototype (Codex increment 5) — separate scope.
- Reviewer-facing prototype (Codex increment 6) — separate scope.

**Exact resumption steps for the next agent / session.**
1. `cd /opt/dewata.online && git checkout strip-saka-corrections-r2-20260920`
2. Re-run `python -m pytest -q -rs phase-1/tests/` (expect 324 pass) and `python -m pytest -q -rs wiki/tests/` (expect 20 pass).
3. Read `docs/CURRENT_STATE.md` → `docs/BACKLOG.md` → `docs/DECISIONS.md` (the supersession section D9-D13 is at the bottom of each).
4. To verify the boundary: `python3 -m dewatacalendar date 2026-01-01` and `2026-03-19` should show `saka_year: null` and the same `saka_year_diagnostic_january_rollover`.
5. PR URL to open: `https://github.com/consciousclarity/dewata-org/pull/new/strip-saka-corrections-r2-20260920`.

---

## 2026-09-20 — strip-saka-unimplemented-fields-20260920 (merged as PR #15)

**commit:** `2a302db` on branch `strip-saka-unimplemented-fields-20260920` (off main `65784ce`).

**what changed**
- `phase-1/src/dewatacalendar/saka.py`: `_saka_year_for_date` now derives from `SAKA_EPOCH_YEAR`. Removed `lunar_tithi`, `is_purnama`, `is_tilem`, `is_pangunalatri` from `SakaDate`. Removed `PANGUNALATRI_PERIOD` and `_new_moon_doy`. Module docstring rewritten: states what is implemented, that sasih indexing is unvalidated, and cites the three open sasih_index_drift disputes.
- `phase-1/src/dewatacalendar/rahinan.py`: removed the `purnama` and `tilem` branches; removed the unreachable `nyepi` branch with a comment explaining the predicate was unsatisfiable; updated the module docstring.
- `phase-1/src/dewatacalendar/__init__.py`: module-order comment no longer claims `tilem/purnama` are in scope.
- `phase-1/tests/test_saka_strip.py` (new): 7 tests — epoch→1901, 2026→1948, four removed fields absent from `compose_day` for one date and across a 1979-2027 span, three removed rahinan ids never emitted across 1979-2099.
- Wiki (14 pages): `wiki/docs/{en,id}/calendar/pangunalatri.md`, `wiki/docs/{en,id}/rahinan/{purnama,tilem,nyepi}.md`, `wiki/docs/{en,id}/rahinan/id-mapping.md`, `wiki/docs/{en,id}/rahinan/index.md`. Each unimplemented surface page is marked as such with the reason and the three dispute IDs. id-mapping tables remove the three ids (count: 12 → 9). index pages annotate Purnama/Tilem rows as unimplemented.

**what passed**
- `cd phase-1 && python -m pytest -q -rs` → `310 passed in 16.28s`. (303 prior + 7 new. 0 failed.)
- `python -m pytest wiki/tests -q -rs` → `15 passed in 16.35s`. (0 failed.)

**what the user expected that didn't happen**
- The user said: "I expect some tests to fail on the removed fields and I want to see which, not a summary." No existing test references the four removed fields directly, so nothing failed. The user's expectation was wrong (test fixtures only use `saka_year` / `sasih_idx` as dict keys, not as engine surface reads). The seven new tests are the regression guard they asked for.

**remaining blockers**
- PR not yet opened (user opens it per prompt).
- Production API not yet deployed. To deploy after merge: rebuild the editable install in `.venv`, `systemctl restart dewata-api.service`, verify via `curl https://api.dewata.org/dsp/v0.1/calendar/date/2026-09-20 | jq .saka.saka_year` returning `1948`.
- The three sasih_index_drift disputes remain pending. The strip does not resolve them.

**exact resumption steps for the next agent / session**
1. `cd /opt/dewata.online && git checkout strip-saka-unimplemented-fields-20260920`
2. Re-run the two pytest invocations; expect 310 + 15 pass.
3. Diff `origin/strip-saka-unimplemented-fields-20260920` against `origin/main` — should show only the 16 files in the commit.
4. PR URL to open: `https://github.com/consciousclarity/dewata-org/pull/new/strip-saka-unimplemented-fields-20260920`.
5. After merge, deploy per `deploy/runbook/DEPLOY.md` (out of scope for Hermes per PROTOCOL.md §0).

---

## prior work (read-only summary, captured here for continuity)

The following branches are recent in-flight or already-merged work. Captured so a new agent knows what's queued:

| branch | status | subject |
|---|---|---|
| `caddy-apex-wiki-handlers-20260920` | pushed | env-var indirection for release dirs (no Caddyfile hardcoded paths) |
| `cross-val-name-comparison-20260920` | merged (PR #14) | raw name comparison in harness; defer regeneration |
| `dewata-caddy-no-reload-20260920` | pushed | drop ExecReload, correct procedure to restart |
| `evidence-cs-provenance-20260920` | merged (PR #13 in `d3a194f`) | fetch-depth 0 + provenance test distinguishes missing-object from not-ancestor |
| `wiki-deployment-safety-20260917` | merged (PR #7 in `cf23840`) | wiki provenance before deployment |
| `wiki-fix-saraswati-wuku-30-20260919` | merged (PR #8 in `33f3142`) | fix saraswati predicate + id-mapping after Wuku table swap |
| `wiki-foundation-20260917` | merged (PR #6 in `5896ab9`) | wiki foundation repo |
| `wuku-table-fix-20260919` | merged (PR #5 in `21e5080`) | WUKU_NAMES_BALINESE per babadbali.com pin (governance 2026-09-19) |
| `range-guard-20260916` | merged (PR #5 in `a8c4728`) | /dsp/v0.1/calendar/range bound to 366 days |
| `strip-saka-unimplemented-fields-20260920` | **pushed, awaiting user PR** | this work |

A new agent should not pick up any of the merged branches — they are part of main. The four pushed-but-not-merged branches (`caddy-apex-wiki-handlers-20260920`, `cross-val-name-comparison-20260920`, `dewata-caddy-no-reload-20260920`, `strip-saka-unimplemented-fields-20260920`) belong to the user / next reviewer.

---

## previous Codex assessment (the prior hypothesis to recheck)

The user's prompt said: "Use the previous Codex assessment as a starting hypothesis. Recheck its findings before acting: it described a working API, a placeholder calendar page, pending calendar disputes and customary review, unprotected main, and inconsistencies between documentation and production."

**Recheck status:**
- ✅ **Working API**: confirmed. `https://api.dewata.org` returns calendar JSON. The four endpoints (`/health`, `/`, `/dsp/v0.1/calendar/ruleset`, `/dsp/v0.1/calendar/date/{date}`, `/dsp/v0.1/calendar/range`) are live.
- ✅ **Placeholder calendar page**: confirmed. `https://dewata.org/calendar.en.html` shows an "under development" banner pointing to the API.
- ✅ **Pending disputes and customary review**: confirmed. 27 disputes in `disputes.json`; 23 pending. `SIGNOFF.md` empty.
- ⚠️ **Unprotected main**: not re-verifiable from this runtime (no GitHub admin token). Still possible to be true.
- ✅ **Documentation ↔ production inconsistencies**: confirmed.
  - ARCHITECTURE.md §4 lists ~22 DSP endpoints; only 4 are mounted.
  - ARCHITECTURE.md §11 says Cloudflare Access is in front of operator routes; the live `/health` and `/` endpoints are open.
  - Production API emits `saka_year=48` for 2026; the module docstring claims the epoch is 1979-03-29 / Saka 1901.
  - `rulesets.py` says `pangunalatri_days=63` is a ruleset metadata field; the field is never used by the engine.

The strip PR addresses three of those inconsistencies (saka_year, lunar fields, purnama/tilem/nyepi rahinan). The remaining inconsistencies are flagged in `CURRENT_STATE.md` for the next session.
