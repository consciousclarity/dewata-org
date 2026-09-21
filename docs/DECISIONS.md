# Decision Log — dewata.org

> **snapshot date:** 2026-09-20
> decisions are facts that were settled; unresolved alternatives are at the bottom.

## D1. Strip the Saka module of unimplemented fields without resolving the open sasih_index_drift disputes
- **date:** 2026-09-20
- **decided by:** Hermes (per user's task prompt)
- **evidence:**
  - `_saka_year_for_date` returned 0 at 1979-03-29 and 48 for 2026 — contradicted the module's own constant `SAKA_EPOCH_YEAR = 1901`.
  - `_new_moon_doy` body was `return 88` with a synodic-month docstring the body never executed. Never called.
  - `is_purnama`, `is_tilem`, `is_pangunalatri`, `lunar_tithi` were arithmetic windows, not astronomical computations.
  - The Nyepi predicate (`sasih_idx == 9 and is_tilem and lunar_tithi == 1`) was unsatisfiable in practice — never emitted.
  - Production API was emitting the broken output: `curl /dsp/v0.1/calendar/date/2026-09-20` returned `saka_year: 48, lunar_tithi: 3, is_purnama: false, is_tilem: false, is_pangunalatri: false`.
- **reason:** Wrong output is worse than no output. Removing the four fields + three rahinan ids eliminates the wrong output without pretending to implement a lunisolar calendar. The user-prompt explicitly forbids attempting the lunisolar implementation.
- **alternatives considered and rejected:**
  - (a) Implement a real lunisolar calendar: requires an eligible published source the repository does not have. Rejected.
  - (b) Silently fix the saka_year arithmetic without removing the lunar fields: would still leave the engine emitting bogus `purnama`/`tilem` rahinan based on arithmetic windows. Worse than the strip. Rejected.
  - (c) Bump ruleset version (`saka-bali-v0.2.3` → `v0.2.4`): violates RULESET_VERSIONING.md invariant 2 (no customary authority on file). Rejected.
- **commit:** `2a302db` on branch `strip-saka-unimplemented-fields-20260920`.

## D2. Do not resolve any of the three sasih_index_drift disputes as part of the strip PR
- **date:** 2026-09-20
- **decided by:** Hermes
- **reason:** PROTOCOL.md: "Never resolve cultural disputes by silently changing formulas, expected values, reference classifications, or sign-off records." The strip PR cites all three dispute IDs in the saka.py module docstring but does not touch them.
- **alternative considered and rejected:** Treat the disputes as "the strip already removed the bad output, so the disputes are moot" — this would falsify dispute state and risk resurrecting broken logic under a different commit.

## D3. Keep `sasih_idx`, `sasih_name`, `is_nampih` on `SakaDate`
- **date:** 2026-09-20
- **decided by:** Hermes
- **reason:** `phase-1/src/dewatacalendar/cross_validation.py` reads `day.saka.get("sasih_idx")` for drift classification; `phase-1/src/dewatacalendar/runbook.py` reads it for dispute classification. Removing `sasih_idx` would break the conformance harness and the dispute packet.
- **trade-off:** The sasih indexing remains unvalidated (see module docstring + the three pending disputes). Users see the value; they should be told it's unvalidated.

## D4. Mark wiki pages describing unimplemented surfaces rather than delete them
- **date:** 2026-09-20
- **decided by:** Hermes
- **reason:** The terms pangunalatri / purnama / tilem / nyepi are real Balinese / Indonesian concepts. Deleting the pages would erase the cultural record. Marking them as "unimplemented surface" preserves the term while telling the user the engine does not compute it.
- **enforced in:** `wiki/docs/{en,id}/{calendar/pangunalatri,rahinan/purnama,rahinan/tilem,rahinan/nyepi}.md`.

## D5. Do not bump `RULESET_VERSION` as part of the strip
- **date:** 2026-09-20
- **decided by:** Hermes
- **reason:** RULESET_VERSIONING.md invariant 1 (cultural sovereignty) requires a customary sign-off entry in `SIGNOFF.md` before any ruleset bump. The strip is a bug-fix, not a ruleset revision. Leaving the version string unchanged avoids the false claim that a customary review occurred.
- **trade-off:** The live API continues to label its output `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0`. This is acceptable because (a) the strip PR does not change the rule, only the implementation; (b) the actual conformance behaviour after the strip is *less* output (no purnama/tilem/nyepi), not a different rule.

## D6. Pin the Saka epoch anchor at 1979-03-29 / SAKA_EPOCH_YEAR=1901 without verifying the conventional claim
- **date:** 2026-09-20
- **decided by:** Hermes (per user's task prompt)
- **reason:** The user's task prompt said: "Fix _saka_year_for_date to derive from SAKA_EPOCH_YEAR. It currently returns 0 at 1979-03-29 — the epoch the module itself declares as Saka 1901 — and 48 for 2026. The constant is dead code and the function contradicts it. Whether 1979-03-29 = Saka 1901 is a separate evidence question; the internal contradiction is just a bug."
- **what this is not:** This is NOT a customary anchor. Whether 1979-03-29 actually corresponds to Saka 1901 in Bali's customary reckoning is one of the open disputes and is not adjudicated by this PR.
- **module docstring:** explicitly flags this ("whether 1979-03-29 = Saka 1901 is the customary anchor is a separate evidence question").

## D7. Test layout: new file `phase-1/tests/test_saka_strip.py` rather than appending to existing test files
- **date:** 2026-09-20
- **decided by:** Hermes
- **reason:** The strip is a self-contained behaviour change; co-locating its tests in one file makes review and rollback straightforward. `test_cultural_adapters.py` already carries `test_engine_does_not_machine_translate_sacred_terms` which incidentally benefits from the strip but is not strip-specific.

## D8. Do not use `git checkout --` to abandon the strip branch while leaving the work
- **date:** 2026-09-20
- **decided by:** Hermes (implicit)
- **reason:** Branch `strip-saka-unimplemented-fields-20260920` is the work product. Pushing it to `origin` (where it is now) preserves the artefact for the user to PR / review / reject. Reverting local would lose the commit.

## Open / unresolved

- O1. **Main branch protection** — could not verify from this runtime; needs user-side GitHub admin action.
- O2. **Three sasih_index_drift disputes** — pending customary review.
- O3. **First customary sign-off** — `SIGNOFF.md` is empty. Until at least one sign-off is recorded, no ruleset bump is permitted.
- O4. **Whether `wiki.dewata.org` build is reproducible across CI + local** — `wiki/tests/test_build_reproducibility.py` exists but was not re-run by Hermes in this session.
- O5. **Snapshot publication pipeline (datasets.dewata.org)** — designed in ARCHITECTURE.md §8 but not implemented. Deferred until phase-3+.

## Supersessions and corrections from PR #15 review

These decisions were made after Codex returned request-changes on
PR #15. They are corrections-only (D9-D13); they do not overwrite
D1-D8, which still hold for the merged state on main.

### D9. **Partial supersession of D5** — separate candidate identity from frozen ruleset
- **date:** 2026-09-20 (post-PR-#15-review)
- **decided by:** Hermes, in response to Codex F2.
- **reason:** D5 reasoned that the strip is a bug-fix, not a ruleset revision, so leaving the ruleset identifier unchanged was acceptable. Codex correctly flagged that observable output did change (`saka_year` semantics, four removed fields, three removed rahinan ids) and that the user-facing identifier now fails to distinguish pre-strip from post-strip output. The corrections follow-up adds `CANDIDATE_ID = "candidate-2026-09-20-strip-corrections-r2"`. `RULESET_VERSION` is unchanged; the candidate identity is a required component of every emitted `CalendarDay` and CLI artefact.
- **what this does NOT do:** it does not bump `RULESET_VERSION`. That still requires customary sign-off. It does not claim the strip output is a release.

### D10. **Partial supersession of D6** — public `saka_year` is unavailable; the raw January-rollover value is a diagnostic only
- **date:** 2026-09-20 (post-PR-#15-review)
- **decided by:** Hermes, in response to Codex F1.
- **reason:** D6's reasoning about the epoch anchor still holds, but the user-facing consequence changes. Even after anchoring the constant, the formula advances on January 1, which is not a customary-attested boundary. The corrections follow-up exposes `saka_year = None` in the public `SakaDate` and `CalendarDay`, and keeps the raw January-rollover value as a separate `saka_year_diagnostic_january_rollover` field that the harness and dispute packet can read. The diagnostic is not validated, not customary-attested, and not part of any release candidate.
- **does not:** pick a different Gregorian boundary (April 1, Nyepi-aligned, etc.) — that is a `calendar_semantics` decision blocked on customary sign-off. The constants remain.

### D11. Capability metadata is authoritative only for runtime-of-record
- **date:** 2026-09-20 (post-PR-#15-review)
- **decided by:** Hermes, in response to Codex F3.
- **reason:** The corrections follow-up makes `IMPLEMENTED_RAHINAN_IDS` the runtime-of-record list (9 ids). `purnama_counted=False`, `tilem_counted=False`, `nyepi_counted=False`. `named_days = len(IMPLEMENTED_RAHINAN_IDS) = 9`. `pangunalatri_days=63` survives as `pangunalatri_days_declared` with `pangunalatri_implemented=False` (this is Claude's merged `48dc5bc` change, preserved verbatim — we add `nyepi_counted` and the `implemented_rahinan_ids` / `unimplemented_rahinan_ids` lists alongside).
- **does not:** delete the historical `named_days=24` record; that was a historical claim and is not part of the candidate.

### D12. Nampih rule is described as observed behaviour, not as the cultural convention
- **date:** 2026-09-20 (post-PR-#15-review)
- **decided by:** Hermes, in response to Codex F4.
- **reason:** Claude's merged `25cbfde` commit introduced `nampih_rule_actual` with the description "saka_year % 3 == 0 -> nampih Desta (13 sasih, 395-day year); uncited". Codex flagged that this falsely endorsed the loop's mod-3 rule as the cultural convention. The corrections follow-up renames the field to `nampih_rule_observed`, names index 13 `Nampih Sada` (matching actual output, not Desta as the prior comment claimed), and adds `nampih_observed_sasih_index=13`, `nampih_observed_sasih_name="Nampih Sada"`. The `nampih_rule_declared` field (Claude's) is preserved verbatim with its explanation that the declared rule has never been implemented.
- **does not:** endorse either Desta or Sada convention as culturally correct. The engine's behaviour here is not validated.

### D13. Wiki generator is a tool, not a source of truth; unimplemented surfaces need both a manual page and a generator guard
- **date:** 2026-09-20 (post-PR-#15-review)
- **decided by:** Hermes, in response to Codex F5.
- **reason:** The merged wiki pages (manual edits from PR #15) are marked as unimplemented, but the wiki generator (`emit_term_pages.py`) still declared purnama/tilem/nyepi as engine-emitted ids via `RHINAN_IDS` and `RHINAN_NAMED`. A future `python wiki/scripts/emit_term_pages.py` would silently restore the old "engine emits" claims. The corrections follow-up splits `RHINAN_IDS` (9 emitted) from `RHINAN_UNEMITTED` (3 unimplemented, with `dispute_ids` referencing the three open sasih_index_drift disputes), and removes the purnama/tilem entries from `RHINAN_NAMED` (since `RHINAN_UNEMITTED` already produces their pages, and the writer's last-write-wins ordering would otherwise overwrite the unimplemented status). A new round-trip test (`wiki/tests/test_emit_term_pages_preservation.py`) runs the writer against a temp copy of the wiki docs and asserts the unimplemented status is preserved.
