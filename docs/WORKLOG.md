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

---

## 2026-09-20 (round 2) — strip-saka-corrections-r2-20260920 (continuation commits)

**Context.** After merging PR #15, Codex returned request-changes on F1-F5. The follow-up branch `strip-saka-corrections-r2-20260920` addressed F1-F5 across three commits (`1acb908`, `768aadd`, `eb0b715`) on top of `1018721`. This entry records the second round of corrections (the three remaining Codex findings): F1 (already shipped), F2 partial (already shipped), and the round-2 increments 2/4/5/6.

**Base SHA.** `802f9263d18946694e8f9285d66181e4caf4f55a` (merged main).
**Continuation commits.**
- `1acb908` — finding 1: always expose `unimplemented_observances` in `compose_day`.
- `768aadd` — finding 2: separate public validation from diagnostic comparisons.
- `eb0b715` — finding 3: protect manually-maintained pages from generator overwrite.
**Head.** `eb0b715d...` (round 2 continuation of `strip-saka-corrections-r2-20260920`).
**Branch ancestry from merged main.** 4 commits total: `802f9263` → `1018721` (r2 base) → `1acb908` → `768aadd` → `eb0b715`. Each preserves the previous as ancestor. No history rewrite, no strip replay, no branch deletion.

**Finding 1 (always expose unsupported observances).**
- `compose_day` now always populates `unimplemented_observances = UNIMPLEMENTED_RAHINAN_IDS`. Previously the list was empty whenever a different rahinan was emitted.
- HTTP regression tests added for 2026-01-01 (empty rahinan), 2026-03-18 (buda_kliwon), 2024-06-01 (tumpek_landep + kuningan). All three responses now carry the same `unimplemented_observances` list.
- Files: `phase-1/src/dewatacalendar/api.py`, `phase-1/tests/test_http_integration_corrections.py`, `phase-1/tests/test_saka_strip_corrections.py`.

**Finding 2 (separate public validation from diagnostic comparisons).**
- `CrossValidationOutcome` gains `fields_unavailable` and `fields_diagnostic_match`. Status is now `match | disputed | incomplete_public` -- never `match` when a required public field is unavailable.
- `runbook.classify` returns `unavailable_public_field` instead of `epoch_offset`/`calendar_variant` when the public `saka_year` is None. Diagnostic agreement is recorded in the classification note for human readers, but never auto-classifies.
- CLI cross-validation report (in `cmd_test`, after conformance) surfaces `incomplete_public` status with `unavailable_fields=saka_year` marker.
- Files: `phase-1/src/dewatacalendar/cross_validation.py`, `phase-1/src/dewatacalendar/runbook.py`, `phase-1/src/dewatacalendar/cli.py`, `phase-1/tests/test_cross_validation_unavailable.py` (NEW, 6 tests), `phase-1/tests/test_cultural_adapters.py` (status semantics updated).

**Finding 3 (preserve structured wiki evidence).**
- `emit_term_pages.py` exposes `MANUALLY_MAINTAINED_SLUGS` and skips those in the main() pass. The six manually-edited pages (en/rahinan/{purnama,tilem,nyepi}.md, id/rahinan/{purnama,tilem,nyepi}.md) retain their full content: structured `dispute_ids`, `customary_review_status` (status + note), source citations to real engine files, `translation_review_status`, and the `short_definition` "unimplemented" marker.
- Byte-equality test added: writer runs against a temp copy of wiki/docs, and the manually-maintained pages are byte-for-byte identical to the live tree afterwards.
- Preservation test asserts structured fields: `dispute_ids == {DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09, DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET, DISPUTE-ENGINE-SASIH-INDEX-INVERSION}`, `customary_review_status.status == "pending_customary_review"`, source citations point at files that exist on disk, both en and id versions exist.
- Test documentation rewritten to define exactly what is verified (byte equality, structured fields) and what is NOT verified (byte stability of non-maintained pages, future generator identity).
- Files: `wiki/scripts/emit_term_pages.py`, `wiki/tests/test_emit_term_pages_preservation.py` (rewritten, now 10 tests).

**Corrected SBCL claim.**
The prior report said "4 SBCL tests" -- that count was incorrect. The file `phase-1/tests/test_evidence_calendrica_runtime.py` contains **4 tests** but only **2 require SBCL** (`test_calendrica_runtime_matches_sample_data`, `test_calendrica_bali_epoch_constant`, both `@pytest.mark.skipif(SBCL_PATH is None)`). The other two (`test_calendrica_source_sha256_matches_record`, `test_calendrica_license_recorded_sha`) are SHA-256 checks on `calendar.l` and the LICENSE file and run without SBCL.

**Verification (round 2 continuation).**
- `cd phase-1 && python -m pytest -q -rs` → **333 passed**, 0 failed. (Was 324 after `1acb908`; +6 new in `test_cross_validation_unavailable.py`, +3 net for `test_cultural_adapters.py` status update.)
- `cd wiki && python -m pytest wiki/tests -q -rs` → **25 passed**, 0 failed. (Was 20 after `1acb908`; +5 new in `test_emit_term_pages_preservation.py`.)
- `python -m pytest tests/test_evidence_calendrica_runtime.py -v --no-header --tb=no` → **4 passed** (2 SBCL, 2 source/license hash).
- HTTP demonstration (live uvicorn on `127.0.0.1:<free>`, see `phase-1/tests/test_http_integration_corrections.py`):
  - 2026-09-20: `rahinan=[]`, `unimplemented_observances=[purnama, tilem, nyepi]`, `note="empty rahinan list -- engine does not currently compute..."`
  - 2026-03-18: `rahinan=[buda_kliwon]`, `unimplemented_observances=[purnama, tilem, nyepi]` (always present)
  - 2024-06-01: `rahinan=[tumpek_landep, kuningan]`, `unimplemented_observances=[purnama, tilem, nyepi]` (always present)
- Cross-validation structured output (1981-08-23 from Cunningham 1994 corpus row, diagnostic=1903, public=None):
  - `status: "incomplete_public"`
  - `actual.saka_year: null`, `fields_ok.saka_year: false`, `fields_unavailable.saka_year: true`
  - `fields_diagnostic_match.saka_year: true` (recorded separately)
  - `runbook.classify` → `("unavailable_public_field", "public saka_year is unavailable ...; this is not an epoch error or regional variant. diagnostic saka_year matches expected: True.")`
- Wiki byte-equality (live vs after writer):
  - `en/purnama.md`, `en/tilem.md`, `en/nyepi.md`, `id/purnama.md`, `id/tilem.md`, `id/nyepi.md` -- **all byte-equal**.

**Diff summary vs `802f9263` (full r2 branch, including `1018721`).**
- 17 files changed, 1618 insertions(+), 64 deletions(-)
- New files: `phase-1/tests/test_cross_validation_unavailable.py`, `phase-1/tests/test_http_integration_corrections.py`, `phase-1/tests/test_saka_strip_corrections.py`, `wiki/tests/test_emit_term_pages_preservation.py`.
- Per-finding breakdown:
  - F1 (commit `1acb908`, 199 insertions in `test_http_integration_corrections.py` etc., api.py change): finding 1 always-expose-implemented-observances contract.
  - F2 (commit `768aadd`, 435 insertions / 39 deletions): separation of public validation from diagnostic comparisons.
  - F3 (commit `eb0b715`, 274 insertions / 78 deletions): manually-maintained page protection + byte-equality test.
  - Plus the r2 base (`1018721`): F1-F5 from Codex review of PR #15.

**Protected paths audit (untouched in the entire r2 branch).**
- `phase-1/src/api/main.py` (live API entrypoint)
- `phase-1/docs/runbook/disputes.json` (27 disputes, 13 active blockers)
- `phase-1/docs/runbook/SIGNOFF.md` (empty by design)
- `phase-1/conformance/STATUS.json` (schema v3.0; `can_promote_ruleset_using` and `can_be_described_as_ground_truth` return FALSE unconditionally)
- `phase-1/conformance/published/*.json` (3 corpus files -- Cunningham 1994 × 2, Igarashi 1999 × 1)
- `phase-1/tests/test_evidence_calendrica_runtime.py` (corrected SBCL claim -- 2 SBCL, 2 source/license hash, not "4 SBCL")
- `deploy/caddy/Caddyfile.dewata`, `deploy/systemd/*`, `deploy/www/**` (production deploy configuration)
- `registry/*.tsv` (gianyar pilot data)
- `wiki/docs/**` (live wiki content files)

**Remaining limitations and owner decisions.**
- Codex increment 2 (candidate-identity policy): the existing `CANDIDATE_ID` is sufficient to distinguish observable output, but the project has not adopted an explicit `accepted_ruleset` rule for release promotion. Owner decision pending.
- Codex increment 4 (Sasih decision packets): three sasih_index_drift disputes are still pending; this branch does not attempt to resolve them. Customary sign-off required.
- Codex increment 5 (astronomy prototype): out of scope; default posture is decline until customary sign-off.
- Codex increment 6 (reviewer-facing view): out of scope; deferred.
- 13 vs 15 active blockers discrepancy in `disputes.json` (Codex flagged but not addressed): the count is `len([d for d in disputes if d.get('blocking') is True]) == 13`. Three disputes are missing the `blocking` field. Owner decision: do those missing-`blocking` disputes block promotion? Default reading is yes until declared otherwise.
- `DISPUTE_REVIEW_PROTOCOL.md` cron + 30/90-day variant advice: still contradicts PROTOCOL.md §2.6. Owner decision needed before either document is updated.
- Pre-existing CLI conformance failure in `cmd_test` (corpora reference stripped fields `saka.saka_year`, `lunar_tithi`, etc.): unrelated to this branch; corpora are not updated by the strip. Out of scope for round 2.

**Reporting and scope discipline.**
- Committed changes: `1acb908`, `768aadd`, `eb0b715`, `769e808` (all on `strip-saka-corrections-r2-20260920`, none pushed, none merged).
- Executed verification: full phase-1 pytest (333 pass), wiki pytest (25 pass), SBCL test file (4 pass), live HTTP demo (three boundary dates), cross-validation structured output, wiki byte-equality, CLI `ruleset` smoke.
- Unverified claims: branch protection on main (no GitHub admin token); production deploy (PROTOCOL §0 forbids); customary sign-off (out of scope).
- Stopped after preparing the local artifact for Codex independent review. Passing tests are not release approval.

---

## 2026-09-20 (round 3) — strip-saka-corrections-r2-20260920 (precedence fix)

**Context.** After round 2 was committed, Codex observed that the precedence correction had a residual defect: a required unavailable `saka_year` caused `status=incomplete_public` and `classification=unavailable_public_field` even when other required public fields (pawukon_position, pawukon_wuku_idx, sasih_idx) independently disagreed with the reference. The CLI then reported "0 disputed, 3 incomplete", hiding substantive disagreements on two of three corpus rows.

**Base SHA.** `769e808e6473969b45305ba1db277a57dbfad58f` (round-2 head, the prior WORKLOG commit).
**Commit.** `53fe078` — round-3 precedence fix: unavailability does not hide disagreement.
**Branch ancestry from merged main.** 5 commits total: `802f9263` → `1018721` → `1acb908` → `768aadd` → `eb0b715` → `769e808` → `53fe078`. Each preserves the previous as ancestor.

**Precedence correction.**
- 1. If any AVAILABLE required public field disagrees with expected: status=disputed.
- 2. Else if any required field is unavailable: status=incomplete_public.
- 3. Else: status=match.

**Implementation.**
- `cross_validation.py`: new `fields_disagree_available: dict[str, bool]` on `CrossValidationOutcome`. Status branch order flipped (disputed → incomplete_public → match). Notes list disagreeing available field(s) AND saka_year unavailability.
- `runbook.py::classify`: helper `_available_ok(k) -> bool | None` treats unavailable fields as `None` instead of `False`. Substantive heuristics check True/False/None; only available-field truth values drive classification. When classification is substantive AND saka_year is unavailable, the classification notes append `[addendum: saka_year was unavailable...]` so both facts are visible. Rows where all available fields agree AND a required field is unavailable still classify as `unavailable_public_field` (the substantive check is inconclusive, not wrong).
- `cli.py` cross-validation summary: reports `match`, `disputed (X of those also had unavailable fields)`, `incomplete_public (X total rows with unavailable fields)`. The parentheticals make explicit that disputed and incomplete are not mutually exclusive.

**Expected high-level outcomes on current v0.1 corpora.**
- 1981-08-23: `incomplete_public` / `unavailable_public_field` (all available fields agree; only saka_year unavailable).
- 1979-03-29: `disputed` / `rule_drift`, with saka_year unavailability noted (pawukon and sasih disagree on available fields).
- 2024-09-07: `disputed` / `rule_drift`, with saka_year unavailability noted (same pattern as 1979-03-29).

**Tests.**
- Revised `test_f2_incomplete_outcome_status_field_is_incomplete_public` to use 1981-08-23 (where the available fields actually agree in the corpus) instead of 1979-03-29 (which has substantive disagreements).
- New `test_round3_unavailable_does_not_hide_disagreement`: required saka_year unavailable + diagnostic matches + pawukon/sasih disagreeing. Asserts the diagnostic does NOT satisfy saka_year, saka_year remains unavailable, fields_disagree_available flags each disagreement, status=disputed, notes expose both facts, runbook.classify yields rule_drift with the addendum.
- New `test_round3_cross_validate_all_does_not_silently_become_zero_disputed`: aggregate guard. Asserts n_disputed >= 2, n_incomplete >= 1, n_match == 0, n_with_unavailable == total rows, n_disputed_with_unavailable >= 2.

**Verification.**
- `cd phase-1 && python -m pytest -q -rs` → **335 passed**, 0 failed (was 333 after `769e808`; +2 new tests; 0 failed).
- `cd . && python -m pytest wiki/tests -q -rs` → **25 passed**, 0 failed (unchanged).
- `python -m pytest phase-1/tests/test_evidence_calendrica_runtime.py -v` → **4 passed** (2 SBCL, 2 source/license hash; unchanged from round-2 count).

**Protected paths audit (untouched in round-3 commit).**
- `phase-1/src/api/main.py` (live API entrypoint)
- `phase-1/docs/runbook/disputes.json` (27 disputes, 13 active blockers)
- `phase-1/docs/runbook/SIGNOFF.md` (empty by design)
- `phase-1/conformance/STATUS.json` (schema v3.0)
- `phase-1/conformance/published/*.json` (3 corpus files)
- `phase-1/tests/test_evidence_calendrica_runtime.py` (SBCL tests)
- `deploy/caddy/Caddyfile.dewata`, `deploy/systemd/*`, `deploy/www/**`
- `registry/*.tsv`
- `wiki/docs/**`
- The accepted API capability fix (commit `1acb908`)
- The accepted wiki preservation fix (commit `eb0b715`)
- The candidate identifier (`candidate-2026-09-20-strip-corrections-r2`)

**Reporting and scope discipline.**
- Committed changes: `53fe078` only (single focused follow-up).
- Executed verification: full phase-1 pytest (335 pass), wiki pytest (25 pass), SBCL tests (4 pass), live cross_validate_all() output, CLI summary reconstruction, three corpus rows classified as expected.
- Unverified claims: branch protection on main; production deploy; customary sign-off.
- Stopped for Codex independent review. Passing tests are not release approval.
