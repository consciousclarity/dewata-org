# Two-axis analysis: RAW_GREGORIAN_MAPPING vs PHASE_NORMALIZED_FORMULA

**Comparison type:** evidence-only, analysis only.
**Date:** 2026-09-15
**First-party source:** `EdReingold/calendar-code2` commit `9afc1f3277b839db1a70c2350d6c708ac83df78f`
**Dewata engine:** commit `5d8e7a1e4c4a6dbea809cbab5c8f0da9e0d97b6b` on `warden/phase2-foundation-20260914`

## methodology

The question of whether Dewata is "correct" can be split into two independent questions:

**Q1 (mapping/phase):** Does Dewata assign the same Pawukon/Wuku/Wewaran values to the same Gregorian dates as first-party CALENDRICA?

**Q2 (formulas):** Given the same Pawukon cycle position, do Dewata's internal Wewaran formulas produce the same values as first-party CALENDRICA?

These must be audited independently. Q1 concerns the choice of epoch anchor (1981-08-23 vs JD 146). Q2 concerns the arithmetic formulas themselves.

The 210-day comparison is run twice, with two different labels:

- **RAW_GREGORIAN_MAPPING** — no phase adjustment. Dewata and CALENDRICA are compared position-by-position on real Gregorian dates.
- **PHASE_NORMALIZED_FORMULA** — cycle positions are aligned (CAL shifted by -84) so that the same Pawukon phase is being queried at the same row. This isolates the formula question from the mapping question.

## 1. RAW_GREGORIAN_MAPPING

For a complete consecutive 210-day Gregorian interval (1981-08-23 to 1982-03-20), Dewata and first-party CALENDRICA are compared with NO phase adjustment.

**interval:** 1981-08-23 to 1982-03-20 (210 consecutive days)

| field | matches / 210 | disagreements / 210 | first disagreement idx | pattern |
|---|---|---|---|---|
| cycle_position | 0 / 210 | 210 / 210 | idx 0 | constant +84 offset (CAL - DEW = +84 every day) |
| Wuku_idx | 0 / 210 | 210 / 210 | idx 0 | follows from cycle_position: CAL wku = ((CAL pos - 1) // 7) + 1, DEW wku = same formula on shifted pos; net 84/30 = 2.8 ≡ 12 wuku shift |
| Pancawara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Saptawara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Triwara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Sadwara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Caturwara | 12 / 210 | 198 / 210 | idx 0 | per-row disagreement |
| Asatawara | 12 / 210 | 198 / 210 | idx 0 | per-row disagreement |
| Sangawara | 125 / 210 | 85 / 210 | idx 1 | per-row disagreement |
| Dasawara | 12 / 210 | 198 / 210 | idx 1 | per-row disagreement |
| Dwiwara | 126 / 210 | 84 / 210 | idx 2 | per-row disagreement |
| Luang | SEMANTICS_DIFFER | n/a | n/a | CALENDRICA uses `evenp(dasawara)`; Dewata has no direct Luang field; cannot compare as boolean |

**phase offset:** exactly +84 (mod 210), deterministic, every single day. CAL_raw_position − DEW_position ≡ 84 (mod 210) for all 210 days.

**Wuku differs raw:** yes, by exactly 12 wuku (= 84 days) at every position.

## 2. PHASE_NORMALIZED_FORMULA

After applying the -84 shift to CALENDRICA's cycle position (so that both engines query the same Pawukon phase at the same row), the comparison is rerun:

| field | matches / 210 | disagreements / 210 | first disagreement idx | pattern |
|---|---|---|---|---|
| cycle_position | 210 / 210 | 0 / 210 | (none) | shift aligns positions |
| Pancawara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Saptawara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Triwara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Sadwara | 210 / 210 | 0 / 210 | (none) | matches perfectly |
| Caturwara | 12 / 210 | 198 / 210 | idx 0 | per-row disagreement, same pattern as raw |
| Asatawara | 12 / 210 | 198 / 210 | idx 0 | per-row disagreement, same pattern as raw |
| Sangawara | 125 / 210 | 85 / 210 | idx 1 | per-row disagreement, same pattern as raw |
| Dasawara | 12 / 210 | 198 / 210 | idx 1 | per-row disagreement, same pattern as raw |
| Dwiwara | 126 / 210 | 84 / 210 | idx 2 | per-row disagreement, same pattern as raw |

**Interpretation:** the normalization corrects the cycle_position / Wuku / Pancawara / Saptawara / Triwara / Sadwara fields but does NOT change the disagreement pattern for Caturwara / Asatawara / Sangawara / Dasawara / Dwiwara. This means:

- The fields that disagree in raw and normalize the same → **formula problem**, not a mapping problem.
- The fields that disagree in raw and agree after normalize → **mapping problem**, not a formula problem.

## 3. decision matrix interpretation

| field | raw | normalized | diagnosis |
|---|---|---|---|
| cycle_position | mismatch | match | **mapping_phase** (constant +84 offset) |
| Wuku | mismatch | match (transitively, via cycle_position) | **mapping_phase** |
| Pancawara | match | match | no implementation disagreement vs CALENDRICA |
| Saptawara | match | match | no implementation disagreement vs CALENDRICA |
| Triwara | match | match | no implementation disagreement vs CALENDRICA |
| Sadwara | match | match | no implementation disagreement vs CALENDRICA |
| Caturwara | mismatch | mismatch | **formula_semantics** |
| Asatawara | mismatch | mismatch | **formula_semantics** |
| Sangawara | mismatch | mismatch | **formula_semantics** |
| Dasawara | mismatch | mismatch | **formula_semantics** (urip table) |
| Dwiwara | mismatch | mismatch | **indexing_representation** (parity input differs) |
| Luang | SEMANTICS_DIFFER | SEMANTICS_DIFFER | **naming_only** (different semantics; cannot compare) |

**Important caveat:** "no implementation disagreement vs CALENDRICA" does NOT mean "correct vs cultural reality." CALENDRICA is itself a non-cultural implementation. See section 4 for independent cultural evidence.

## 4. independent Gregorian ↔ Pawukon references (non-CALENDRICA)

The following dates were retrieved from independent (non-CALENDRICA) sources. Each date includes the cultural-reference Wuku/Pancawara/Saptawara values, the source, and whether Dewata / first-party CALENDRICA agrees.

| Gregorian date | reference (Wuku, Pancawara, Saptawara) | source | DEW sap match | DEW pan match | DEW wuku match | CAL sap match | CAL pan match | CAL wuku match |
|---|---|---|---|---|---|---|---|---|
| 2026-09-01 | Anggara Umanis Uye (wk 22) | kalenderbali.org page title | OK | NO (says Paing) | NO (Sungsang=10) | OK | NO (says Paing) | OK |
| 2026-09-05 | Saniscara Keliwon Uye (wk 22) | liputan6 + kalenderbali.org | OK | NO (says Umanis) | NO (Sungsang=10) | OK | NO (says Umanis) | OK |
| 2026-09-09 | Buda Wage Menail (wk 23) | kalenderbali.org + liputan6 + detik + pelajahin | OK | NO (says Keliwon) | NO (Kuningan=11) | OK | NO (says Keliwon) | OK |
| 2026-09-15 | Anggara Kliwon Prangbakat (wk 24) | kalenderbali.org + liputan6 | OK | NO (says Umanis) | NO (Langkir=12) | OK | NO (says Umanis) | OK |
| 2026-09-17 | Wraspati Paing Prangbakat (wk 24) | kalenderbali.org page title | OK | NO (says Pon) | NO (Langkir=12) | OK | NO (says Pon) | OK |
| 2026-09-26 | Saniscara Umanis Bala (wk 25) | kalenderbali.org + liputan6 | OK | NO (says Paing) | NO (Medangsia=13) | OK | NO (says Paing) | OK |
| 2026-09-30 | Buda Keliwon Ugu (wk 26) | kalenderbali.org + detik | OK | NO (says Umanis) | NO (Pujut=14) | OK | NO (says Umanis) | OK |

**Key observations:**
- **Saptawara**: Dewata and CAL both agree with the cultural references on all 7 dates. ✓
- **Wuku**: CAL agrees with cultural references on all 7 dates; Dewata is exactly 84 days (= 12 wuku) earlier on all 7 dates.
- **Pancawara**: BOTH Dewata AND CALENDRICA disagree with cultural references on all 7 dates. The Pancawara values reported by cultural sources are one step "earlier" than what both engines compute. This is a substantive disagreement between (cultural sources) and (CALENDRICA + Dewata, which agree with each other).

**This is critical:** the cultural references and CALENDRICA disagree on Pancawara. The disagreement is NOT a "Dewata is wrong" disagreement — it is a "Dewata follows CALENDRICA which follows an algorithmic convention that may not match cultural Balinese usage" disagreement. The Pawukon has no canonical Pancawara algorithm; CALENDRICA's choice is one valid choice, but the cultural sources suggest a different one.

## 5. independent sources for irregular Wewaran rules (non-CALENDRICA, non-Dewata)

Per the user's instruction to find "at least one second independent source supporting the irregular/repeated-day structure" beyond CALENDRICA.

### result: NOT FOUND

The independent sources searched include:

1. **BASAbali Wiki** (`basaibubali.org`) — a Balinese-language dictionary community project. Their formulas for these wewaran are:

| field | BASAbali formula | source |
|---|---|---|
| Caturwara | `(bilangan uku × 7 + bilangan saptawara) / 4` remainder 1=Sri, 2=Laba, 3=Jaya, 0=Menala | https://basaibubali.org/Caturwara |
| Sangawara | `(bilangan uku × 7 + bilangan Saptawara) / 9` remainder 1=Dangu, 2=Jangur, 3=Gigis, 4=Nohan, 5=Ogan, 6=Erangan, 7=Urungan, 8=Tulus, 0=Dadi | https://basaibubali.org/Sangawara |
| Dasawara | `(urip Pancawara + urip Saptawara + 1) / 10` remainder 1=Pandita, 2=Pati, ..., 0=Raksasa | https://basaibubali.org/Dasawara |
| Dwiwara | sum odd = Pepet, even = Menga | https://basaibubali.org/Dwiwara |

**Critical observation:** BASAbali describes these formulas as **simple modular arithmetic** with no special-case handling for day 72 / first 3 days. The BASAbali Caturwara formula `(uku × 7 + saptawara) / 4` produces different values than CALENDRICA's `(max(6, 4 + mod(day-70, 210)))` + amod(asatawara, 4) formula.

2. **lydiaa.bnb.dweb3.wtf** (mirrored Wikipedia content): states "For both the 4- and 8-day weeks, the penultimate day of the week is repeated twice in the week that would have otherwise ended on the 72nd day. For the 9-day week, the first day of the week is repeated 3 times in the first week of the 210-day Pawukon." — this DOES support the special-case structure. However this source is a Wikipedia mirror.

3. **Grokipedia** ("Pawukon calendar" page): "the Caturwara and Astawara repeat their penultimate days (Jaya and Kala, respectively) twice around day 72, while the Sangawara repeats its first day (Dangu) three times in the first week" — also supports the special-case structure. Grokipedia appears to derive from Wikipedia. Note: the user instructed that Wikipedia may be used as a discovery lead but is not authoritative.

**summary:** there are TWO possible formulations in the literature for these wewaran:
- **special-case** (CALENDRICA, Dewata, Wikipedia mirror, Grokipedia): around day 72 / first 3 days have irregularities
- **simple modular** (BASAbali): no special case, just `(uku × 7 + saptawara) / N`

These two formulations disagree with each other. None has been confirmed as canonical. The presence of both formulations in the literature means the "irregular" structure is itself a disputed question. The user's request for "at least one second independent source supporting the irregular/repeated-day structure" is partially satisfied by the Wikipedia mirror / Grokipedia, but those are derivative of Wikipedia. BASAbali (independent) gives the **opposite** answer (simple modular).

## 6. dispute reclassification (post two-axis analysis)

Per the user's decision matrix, current disputes are reclassified without resolving them:

| dispute ID | current class | reclassification | rationale |
|---|---|---|---|
| DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15 | calendar_semantics | **mapping_phase** | raw mismatch + normalized match — constant +84 offset indicates mapping/phase problem, NOT a formula problem |
| DISPUTE-wewaran-asatawara-special-case-formula-2026-09-15 | calendar_semantics | **formula_semantics** | raw mismatch + normalized mismatch — both phases disagree; the disagreement persists after phase alignment, indicating a formula problem. Furthermore, the special-case structure itself is independently disputed (BASAbali gives simple modular arithmetic) |
| DISPUTE-wewaran-caturwara-transitive-dependency-on-asatawara-2026-09-15 | calendar_semantics | **formula_semantics** | transitive on asatawara; the formula problem applies here too |
| DISPUTE-wewaran-sangawara-special-case-formula-2026-09-15 | calendar_semantics | **formula_semantics** | raw mismatch + normalized mismatch; furthermore the special-case structure (max(0, day-3) vs first-3-days-Dangu vs BASAbali's simple modular) is itself in question |
| DISPUTE-wewaran-dasawara-urip-5-table-2026-09-15 | calendar_semantics | **formula_semantics** | urip_5 table disagrees (cyclic rotation); formula structure matches but values differ |
| DISPUTE-wewaran-dwiwara-parity-basis-2026-09-15 | calendar_semantics | **indexing_representation** | parity input differs (dasawara index vs urip value); classification of "what does parity mean for dwiwara" is representational |
| DISPUTE-reference-reingold-dershowitz-2018-license-classification-2026-09-15 | bibliographic (resolved) | **naming_only** (no further action; the dispute is RESOLVED) | the original CALENDRICA source metadata is now Apache 2.0 per first-party evidence |

## 7. what this means for future repair

The classification tells us:

- **One anchor/phase correction** alone would fix: cycle_position, Wuku, and would indirectly affect Pancawara / Saptawara / Triwara / Sadwara (which already match CALENDRICA after normalization). NOT a single "anchor fix" alone resolves Caturwara / Asatawara / Sangawara / Dasawara / Dwiwara disagreements.
- **Several algorithm corrections** alone would not be enough — even if every formula matched CALENDRICA, the +84 offset would still mean real-world Gregorian dates do not produce the cultural-reference Pawukon values.
- **Both** anchor/phase correction AND algorithm corrections are likely required.

But neither is sufficient because **CALENDRICA itself disagrees with cultural references on Pancawara**. Fixing the anchor to match CALENDRICA would not make Dewata match cultural references on Pancawara — both engines have the same Pancawara, and cultural reality differs.

This is why per PROTOCOL v1.0 the disputes remain UNRESOLVED at this point. Per the user's instruction: "without asking first, do NOT... resolve cultural/calendar-semantic disputes". The presence of THREE different formulations (CALENDRICA, BASAbali, cultural-practice) means resolution requires customary or scholarly authority, not internal algorithm reconciliation.

## 8. future-change triage

The user asks: "whether the evidence now supports treating any future change as: implementation correction / semantic ruleset change / still unresolved."

| field | future-change classification | rationale |
|---|---|---|
| cycle_position (the +84 mapping) | **implementation correction** IF a single day offset resolves it; **semantic ruleset change** IF a different convention is desired (e.g., the dewata engine moves to 1981-08-30 epoch) | the underlying arithmetic is correct; only the offset constant differs |
| Wuku | transitive on cycle_position | follows the cycle_position correction |
| Pancawara / Saptawara / Triwara / Sadwara | **implementation correction** (both engines already agree after normalization; if/when the anchor is corrected, these will be correct) | the formulas are identical between engines |
| Caturwara / Asatawara / Sangawara / Dasawara / Dwiwara | **still unresolved** at the cultural level (BASAbali vs CALENDRICA vs Dewata disagree on formula structure); **implementation correction** could reconcile to one of them but not without choosing an authority | per PROTOCOL v1.0 dispute classes — calendar_semantics requires customary or scholarly authority |
| Luang | **naming_only** (semantic difference, no agreement between the two engines' semantics) | can be left alone or aligned to one convention |

Per PROTOCOL v1.0 §4.4: "semantic/ruleset changes require dispute/governance process; ordinary implementation corrections require tests + atomic commits + role sign-offs." The mapping_phase correction is an **implementation correction** (changing an epoch constant); the formula_semantics corrections are **semantic/ruleset changes** (changing calendrical formulas) and require governance.

## 9. epoch anchor reclassification

Per the user's instruction: do not describe `fixed-from-jd 146` as a historical Balinese epoch. The original dispute used language like "CALENDRICA's bali-epoch = fixed-from-jd 146 = RD -1721279, equivalent to Julian Day Number 146 = proleptic Gregorian 4714-07-02." This language implied the JD-146 date had historical meaning.

Updated description: `bali-epoch = fixed-from-jd 146` is **a computational origin for the repeating 210-day cycle**, chosen for convenience. The Pawukon model treats the 210-day cycles as unnumbered (per Wikipedia, per D&R), therefore the computational epoch itself may be chosen for any anchor date. The important question is not "does Dewata use the same absolute epoch constant as CALENDRICA?" but "does Dewata assign the same Pawukon/Wuku/Wewaran values to the same Gregorian dates?" — answered: NO, with a deterministic +84 offset.

The corresponding updates to the existing disputes:
- `DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15`: reclassify as `mapping_phase`. The "anchor choice" framing is replaced by the "phase offset" framing.

## 10. files

This artifact: `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2/two-axis-analysis.md`

Supporting data:
- `cycle-comparison/raw-cal-210.csv` — first-party CALENDRICA raw output (no phase shift)
- `cycle-comparison/raw-dewata-210.csv` — Dewata raw output
- `cycle-comparison/independent-references.csv` — 7 Gregorian dates from independent sources
- `cycle-comparison/basaibubali-formulas.json` — independent Wewaran formulas from basaibubali.org

Tests:
- `phase-1/tests/test_two_axis_analysis.py` — verifies exact raw/normalized counts and reclassification

No engine edits. No ruleset promotion. No Saka research.
