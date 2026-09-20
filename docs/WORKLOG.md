# Work Log — dewata.org

> rolling log. newest entry first.

## 2026-09-20 — strip-saka-unimplemented-fields-20260920

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
