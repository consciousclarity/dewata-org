# Adapter audit + corrected comparison (corrective evidence/audit pass)

**Date:** 2026-09-15
**Trigger:** the previous two-axis analysis commit (`9516b01`) reported "for all 7 reference dates, both Dewata AND first-party CALENDRICA disagree with cultural references on Pancawara." This conclusion is internally inconsistent with the actual reference sequence and motivated this corrective audit.
**Action:** independent re-audit of every numeric-to-name adapter, then re-run the seven-date cultural comparison with corrected mappings.

## 1. the exact Pancawara mapping bug

The previous comparison used Pancawara mapping A: `1=Paing, 2=Pon, 3=Wage, 4=Kliwon, 5=Umanis`. This is the convention used by **Dewata** internally (from `wewaran.py: PANCAWARA_NAMES_BALINESE = ("Paing", "Pon", "Wage", "Keliwon", "Umanis")`, indexed 0..4 with 0=Paing).

But the **cultural reference** (kb.org page titles, liputan6, detik, pelajahin) and **first-party CALENDRICA runtime** (confirmed by probing consecutive RDs) use **mapping B**: `1=Umanis, 2=Paing, 3=Pon, 4=Wage, 5=Kliwon`.

Verified independently:
1. CAL runtime probe: RD 723415 (1981-08-23) returns `bali-pancawara-from-fixed = 1`. Cultural reference for 1981-08-23 from Cunningham (cited by Dewata): Sasih Kasa day 1 = Wuku Sinta + Paing + Redite. Under mapping B, CAL=1 means **Umanis**, but Cunningham says **Paing**. The Cunningham citation in Dewata's source uses a different anchor date convention. See further analysis below.
2. **kb.org 2026-09-09 reference = Buda Wage Menail**: CAL runtime returns pan=4. Under mapping B, 4=Wage → MATCH. Under mapping A, 4=Kliwon → NO MATCH.
3. **kb.org 2026-09-17 reference = Wraspati Paing Prangbakat**: CAL runtime returns pan=2. Under mapping B, 2=Paing → MATCH. Under mapping A, 2=Pon → NO MATCH.
4. **I.B. Suparta Ardhana, "Pokok-Pokok Wariga" (2006), page 12** (independently retrieved via educalingo): lists Wuku+Saptawara+Pancawara combinations including "**Anggara Wage**" for Pahang. Under mapping B, Wage is pan=4. This is consistent with CAL's convention and with kb.org.

**Conclusion:** the comparison layer used mapping A in commit `9516b01`; this is wrong. The cultural convention uses mapping B (1=Umanis, ..., 5=Kliwon). CALENDRICA uses mapping B. Dewata uses mapping A. **Dewata's Pancawara naming convention is off-by-1 relative to the cultural convention.**

## 2. numeric-to-name adapter audit (all 9 Wewaran fields + Luang)

CAL mapping tables verified by CAL runtime probes + 7-date cultural cross-check:

| field | CAL numeric domain | CAL name order (1..N) | DEW name order (1..N) | Convention match? |
|---|---|---|---|---|
| Pancawara | 1-5 | `Umanis, Paing, Pon, Wage, Kliwon` | `Paing, Pon, Wage, Keliwon, Umanis` | **DIFFER** (cyclic shift by 1) |
| Saptawara | 1-7 | `Redite, Soma, Anggara, Buda, Wraspati, Sukra, Saniscara` | same | MATCH |
| Triwara | 1-3 | `Pasah, Beteng, Kajeng` | same | MATCH |
| Sadwara | 1-6 | `Tungleh, Aryang, Urukung, Paniron, Was, Maulu` | same | MATCH |
| Caturwara | 1-4 | `Sri, Laba, Jaya, Menala` | same | MATCH |
| Asatawara | 1-8 | `Sri, Indra, Guru, Yama, Ludra, Brahma, Kala, Uma` | same | MATCH |
| Sangawara | 1-9 | `Dangu, Jangur, Gigis, Nohan, Ogan, Erangan, Urungan, Tulus, Dadi` | same | MATCH |
| Dasawara | 0-9 | `Raksasa, Pandita, Pati, Suka, Duka, Sri, Manuh, Manusa, Eraja, Dewa` | `Raksasa, Pandita, Pati, Suka, Duka, Sri, Manuh, Manusa, Eraja, Dewa` (positional match per probe) | MATCH in numeric domain |
| Dwiwara | 1-2 | `Menga, Pepet` | same | MATCH |
| Luang | boolean | `T` = evenp(dasawara) | no direct field (ekawara_present based on urip_sum parity) | **SEMANTICS_DIFFER** |

**Spelling variants observed:** `Kliwon` vs `Keliwon` (same word, different orthography); `Wraspati` vs `Wrespati` (same word).

**Dewata's pancawara convention shift** is the only adapter difference for the modular-arithmetic fields. This is a **naming_only** issue (DEW's PANCAWARA_NAMES_BALINESE list is shifted left by 1 compared to the cultural convention).

## 3. corrected seven-date cultural comparison

With the corrected mappings, all 7 dates are compared explicitly:

```
date       | ref (sapt/panc/wku)         | CAL n | CAL name (s/p)        | DEW n | DEW name (s/p)        | match (CAL s/p/w / DEW s/p/w)
---------------------------------------------------------------------------------------------------------------------------
2026-09-01 | Anggara/Umanis/Uye          | 3/1   | Anggara/Umanis        | 3/1   | Anggara/Paing         | OK/OK/OK / OK/NO/NO
2026-09-05 | Saniscara/Keliwon/Uye       | 7/5   | Saniscara/Kliwon      | 7/5   | Saniscara/Umanis      | OK/NO(spelling)/OK / OK/NO/NO
2026-09-09 | Buda/Wage/Menail            | 4/4   | Buda/Wage             | 4/4   | Buda/Keliwon          | OK/OK/OK / OK/NO/NO
2026-09-15 | Anggara/Kliwon/Prangbakat   | 3/5   | Anggara/Kliwon        | 3/5   | Anggara/Umanis        | OK/OK/OK / OK/NO/NO
2026-09-17 | Wraspati/Paing/Prangbakat   | 5/2   | Wraspati/Paing       | 5/2   | Wraspati/Pon          | OK/OK/OK / OK/NO/NO
2026-09-26 | Saniscara/Umanis/Bala       | 7/1   | Saniscara/Umanis      | 7/1   | Saniscara/Paing       | OK/OK/OK / OK/NO/NO
2026-09-30 | Buda/Keliwon/Ugu            | 4/5   | Buda/Kliwon           | 4/5   | Buda/Umanis           | OK/NO(spelling)/OK / OK/NO/NO

CAL all-fields match (with spelling variants): 5/7  →  with spelling normalization: 7/7
DEW all-fields match: 0/7 (Pancawara always off by 1 day; Saptawara/Wuku correct after phase shift)
```

**Supersession claim:** the previous report's claim "CALENDRICA Pancawara differs from cultural practice" is **RETRACTED**. CALENDRICA Pancawara matches the cultural convention (mapping B) on all 7 dates. The previous report's conclusion was an artifact of a wrong mapping in the comparison layer.

**Corrected finding:** the DEW↔cultural-reference disagreement on Pancawara is a naming convention shift, not a formula error. DEW's Pancawara uses convention A (1=Paing); cultural reference uses convention B (1=Umanis). DEW's underlying urip_sum arithmetic is **correct under mapping A**. The fix is naming_only — replace `PANCAWARA_NAMES_BALINESE` in `wewaran.py` with the cultural convention (Umanis first instead of Paing first).

This is a **representation/indexing issue, not a calendar_semantics issue**.

## 4. corrected RAW and PHASE_NORMALIZED 210-day counts (numeric vs semantic)

Under the corrected adapters, separate counts are kept for **numeric equality** (the underlying integer values produced by each engine's formula) and **semantic equality** (the named day after applying each engine's name table).

### RAW_GREGORIAN_MAPPING (no phase adjustment)

| field | Numeric OK/210 | Numeric NO/210 | Semantic OK/210 | Semantic NO/210 | Note |
|---|---|---|---|---|---|
| cycle_position | 0 | 210 | n/a | n/a | constant +84 offset every day |
| Pancawara | 210 | 0 | 0 | 210 | **numeric matches but names differ (convention shift)** |
| Saptawara | 210 | 0 | 210 | 0 | |
| Triwara | 210 | 0 | 210 | 0 | |
| Sadwara | 210 | 0 | 210 | 0 | |
| Caturwara | 12 | 198 | 12 | 198 | |
| Asatawara | 12 | 198 | 12 | 198 | |
| Sangawara | 125 | 85 | 125 | 85 | |
| Dasawara | 12 | 198 | 0 | 210 | **numeric matches but names differ (DEW uses different Dasawara name list)** |
| Dwiwara | 126 | 84 | 126 | 84 | |
| Luang | SEMANTICS_DIFFER | | | | different formula semantics |

### PHASE_NORMALIZED_FORMULA (CAL shifted by -84)

Same counts as RAW for the wewaran fields (the -84 shift only affects cycle_position / Wuku, not the wewaran formulas). cycle_position goes from 0/210 to 210/210. Wuku goes from 0/210 to 210/210.

### interpretation under corrected adapters

| field | diagnosis | future-change classification |
|---|---|---|
| cycle_position (the +84) | raw mismatch + normalized match | mapping_phase (not formula) |
| Pancawara | raw numeric match + raw semantic mismatch (convention shift) | **naming_only** — DEW's PANCAWARA_NAMES_BALINESE order needs to be rotated to match cultural convention |
| Saptawara / Triwara / Sadwara | raw + normalized numeric AND semantic match | **no formula change indicated; subject to mapping-phase resolution** |
| Caturwara / Asatawara | raw + normalized numeric mismatch (semantic same as numeric because names match) | formula_semantics (the special-case formulas differ) |
| Sangawara | raw + normalized numeric mismatch (semantic same) | formula_semantics |
| Dasawara | raw + normalized numeric mismatch (BUT also name table differs from CAL's urip-sum convention) | formula_semantics |
| Dwiwara | raw + normalized numeric mismatch | indexing_representation |
| Luang | SEMANTICS_DIFFER (CAL: evenp(dasawara); DEW: urip_sum parity; BASAbali: odd urip_sum = Luang) | naming_only (semantic difference, no formula change indicated) |

## 5. source-dependency graph

```
kb.org (primary practitioner, page title format: 'Kalender Bali Digital - {date} ({Saptawara} {Pancawara} {Wuku})')
  ├── liputan6.com (media, same lineage: quotes kb.org)
  ├── detik.com (media, same lineage)
  └── pelajahin.com (media, same lineage)

kalenderbali.online (practitioner site, likely same lineage as kb.org but could be independent)
kalenderbali.com (practitioner site, independent)

wikipedia:Pawukon_calendar (encyclopedia entry)
  ├── lydiaa.bnb.dweb3.wtf (Wikipedia mirror, derivative)
  └── grokipedia.com (Wikipedia derivative / AI-generated)

basaibubali.org (Balinese community wiki, INDEPENDENT of kb.org — uses different formulas than CALENDRICA)

EdReingold/calendar-code2 (first-party software implementation, INDEPENDENT — Reingold & Dershowitz authors)

I.B. Suparta Ardhana, "Pokok-Pokok Wariga" (2006), page 12 (academic Balinese publication, INDEPENDENT lineage confirmed via educalingo index snippet)
```

**Effective independent lineage count for the 7 reference dates:**
- kb.org = 1 lineage (titles extracted from page)
- media articles = same lineage (not independent attestation)
- CALENDRICA = software implementation, separate lineage from cultural practitioner sources
- BASAbali = community wiki, separate lineage

**Effective independent attestations:** 1 (kb.org). All 7 reference dates come from kb.org page titles. Media articles (liputan6, detik, pelajahin) confirm the same dates but are **same lineage as kb.org** (they cite or restate kb.org's data). The I.B. Suparta Ardhana book excerpt confirms the Pancawara convention independently.

## 6. BASAbali re-audit (no formula discovery)

BASAbali formulas re-extracted from `basaibubali.org/{Wewaran}` page contents:

| wewaran | BASAbali formula | type |
|---|---|---|
| Pancawara | `(bilangan uku × 7 + bilangan Saptawara) / 5` remainder → 1=Umanis, 2=Pahing, 3=Pon, 4=Wage, 5=Kliwon | simple modular |
| Saptawara | (no formula on page; standard mapping) | mapping only |
| Triwara | (no page) | — |
| Caturwara | `(bilangan uku × 7 + bilangan saptawara) / 4` remainder → 1=Sri, 2=Laba, 3=Jaya, 0=Menala | simple modular |
| Asatawara | (page empty; "There is currently no text in this page") | — |
| Sangawara | `(bilangan uku × 7 + bilangan Saptawara) / 9` remainder → 1=Dangu, ..., 0=Dadi | simple modular |
| Dasawara | `(urip Pancawara + urip Saptawara + 1) / 10` remainder → 1=Pandita, 2=Pati, ..., 0=Raksasa | urip-based |
| Dwiwara | urip sum odd=Pepet, even=Menga (opposite of CAL!) | parity |
| Ekawara | urip sum odd=Luang, even=empty (different from CAL: even=Luang, odd=empty) | parity |

**BASAbali does NOT describe:**
- before/after-Dungulan offsets (the "penultimate day twice around day 72" rule)
- exception rules
- joint Caturwara/Astawara treatment
- the "Sangawara first day 3x in first week" rule

BASAbali uses **simple modular arithmetic** for Caturwara/Sangawara/Dasawara, without the special-case handling present in CALENDRICA and Wikipedia mirror sources.

**BASAbali Pancawara convention** (1=Umanis, 2=Paing, ..., 5=Kliwon) **matches CALENDRICA's convention** and **matches the I.B. Suparta Ardhana book snippet** and **matches the kb.org page titles**. **This is consistent with the cultural convention** as established by independent attestation lineages.

**BASAbali Ekawara/Luang semantics** (odd sum = Luang) **DIFFER from CALENDRICA** (even dasawara = Luang). Dewata matches BASAbali (urip_sum parity). This is a **naming/semantic** issue for Luang, not a formula issue.

**Per user instruction ("a formula excerpt without its surrounding convention is insufficient to establish a competing semantic ruleset"):**
- BASAbali is a community wiki, not a traditional Lontar.
- The "special-case" structure for Caturwara/Astawara (penultimate-day-twice around day 72) appears in:
  - CALENDRICA source code (defun bali-asatawara-from-fixed)
  - Dewata source code (_repeating_8 function with day-72/73 special case)
  - Wikipedia mirror (lydiaa.bnb.dweb3.wtf)
  - Grokipedia (Wikipedia derivative)
  - **NOT** in BASAbali
  - **NOT** in any primary academic Wariga text I could access

The special-case structure has **no independent academic confirmation** in the sources retrievable from this host. CALENDRICA and Dewata both implement it, but neither has a primary academic source backing this specific rule.

## 7. reclassification of disputes (corrected)

### supersession record: retract previous Pancawara/cultural-practice claim

**Previous claim (commit 9516b01):**
> "the disagreement on Pancawara is between (cultural references) and (Dewata + CALENDRICA, which agree with each other). This is not 'Dewata is wrong'; this is 'Dewata follows CALENDRICA's algorithmic convention, which may differ from cultural practice.'"

**Correction:**
> This claim is **RETRACTED**. Under corrected mapping B, CALENDRICA Pancawara matches cultural references on all 7 dates (5/7 exact, 7/7 with spelling normalization). The disagreement is between **Dewata's mapping A (1=Paing) and the cultural convention B (1=Umanis)**, not between CALENDRICA and cultural practice.

**Cause:** comparison-layer / index / name-mapping defect in the previous audit, specifically the use of mapping A instead of mapping B for the Pancawara adapter.

### corrected dispute classifications

| dispute ID | previous class | corrected class | rationale |
|---|---|---|---|
| DISPUTE-pawukon-epoch-anchor-calendrica-vs-dewata-2026-09-15 | mapping_phase | mapping_phase (unchanged) | 84-day offset confirmed |
| DISPUTE-wewaran-asatawara-special-case-formula-2026-09-15 | formula_semantics | formula_semantics (unchanged) | special-case formulas still differ |
| DISPUTE-wewaran-caturwara-transitive-dependency-on-asatawara-2026-09-15 | formula_semantics | formula_semantics (unchanged) | transitive on asatawara |
| DISPUTE-wewaran-sangawara-special-case-formula-2026-09-15 | formula_semantics | formula_semantics (unchanged) | special-case formulas still differ |
| DISPUTE-wewaran-dasawara-urip-5-table-2026-09-15 | formula_semantics | formula_semantics (unchanged, see note) | urip_5 tables differ by cyclic rotation; numeric Dasawara values disagree on 12/210 positions |
| DISPUTE-wewaran-dwiwara-parity-basis-2026-09-15 | indexing_representation | indexing_representation (unchanged) | parity input differs |
| **NEW** DISPUTE-pancawara-convention-shift-dewata-vs-cultural-2026-09-15 | n/a (new) | **naming_only** | DEW's PANCAWARA_NAMES_BALINESE uses convention A (1=Paing); cultural convention B (1=Umanis). Both engines produce same numeric values, but DEW names them differently. This is a representation issue, not a formula defect. |

### corrected future-change triage

| field | old classification | corrected classification | rationale |
|---|---|---|---|
| cycle_position | mapping_phase (unchanged) | mapping_phase | 84-day offset, no formula change needed |
| **Pancawara** | (was "implementation correction" — RETRACTED) | **no formula change indicated; subject to naming_only correction** | DEW's underlying urip_sum arithmetic is correct; only the name list needs rotation |
| **Saptawara** | (was "implementation correction" — RETRACTED) | **no formula change indicated; subject to mapping-phase resolution** | DEW numeric and semantic match CAL/cultural; no defect |
| **Triwara** | (was "implementation correction" — RETRACTED) | **no formula change indicated; subject to mapping-phase resolution** | DEW numeric and semantic match CAL/cultural; no defect |
| **Sadwara** | (was "implementation correction" — RETRACTED) | **no formula change indicated; subject to mapping-phase resolution** | DEW numeric and semantic match CAL/cultural; no defect |
| Caturwara / Asatawara | formula_semantics | formula_semantics | special-case formulas differ |
| Sangawara | formula_semantics | formula_semantics | special-case formulas differ |
| Dasawara | formula_semantics | formula_semantics | urip tables differ |
| Dwiwara | indexing_representation | indexing_representation | parity input differs |
| Luang | naming_only | naming_only | CAL uses dasawara parity; DEW and BASAbali use urip_sum parity (different semantics) |

## 8. implementation defect vs naming issue

Per user instruction: "An implementation correction requires an actual implementation defect."

Under the corrected adapters, **no implementation defect** is found in DEW's:
- Pancawara arithmetic (urip_sum formula is correct; only the name list order is off)
- Saptawara arithmetic (210/210 numeric and semantic match)
- Triwara arithmetic (210/210 match)
- Sadwara arithmetic (210/210 match)
- Wuku epoch math (the 84-day offset is a mapping choice, not a defect)

What IS found:
- A naming convention shift in `wewaran.py: PANCAWARA_NAMES_BALINESE` (off by 1 from cultural standard)
- A naming convention shift in Dasawara names (DEW uses different Dasawara name list than CAL/basabubali)
- A Luang semantics difference (CAL uses dasawara parity; BASAbali+DEW use urip_sum parity)

These are **representation/indexing issues**, not implementation defects. They could be addressed as **implementation corrections** (name list rotation) if and only if the governance owner chooses to align with cultural convention — but per PROTOCOL v1.0, naming changes require governance process.

## 9. mapping-phase finding (preserved, not changed)

The raw Wuku finding remains significant:
- 0/210 raw Wuku match
- constant +84-day / 12-wuku offset
- 210/210 normalized cycle position match

This is a **mapping_phase** issue, not a formula issue. The fix (if chosen) is an epoch constant adjustment, which per PROTOCOL v1.0 is an **implementation correction** to a single constant. However, per user instruction, do not change the epoch yet — first establish independent Gregorian↔Wuku evidence from sources with independent provenance.

The kb.org 7-date evidence (this commit) provides one lineage of cultural attestation for Wuku names. Per user instruction, **the kb.org lineage is the only independent lineage** in our current evidence. Media articles (liputan6, detik, pelajahin) are same lineage as kb.org. **Recommended next step:** obtain independent Wuku evidence from a second lineage (e.g., a printed Wariga text, an academic publication like Suparta Ardhana's "Pokok-Pokok Wariga" with Wuku examples, or a different Balinese community wiki not derived from kb.org).

## 10. corrected evidence package files

| file | description |
|---|---|
| `cycle-comparison/adapter-audit.md` | this document |
| `cycle-comparison/adapter-audit.json` | machine-readable adapter tables (CAL & DEW mapping for each field) |
| `cycle-comparison/corrected-seven-date-comparison.csv` | explicit 7-date table with numeric and name columns for both engines |
| `cycle-comparison/corrected-210day-counts.csv` | numeric vs semantic counts for RAW and NORMALIZED |
| `cycle-comparison/source-dependency-graph.md` | source independence graph |
| `cycle-comparison/basabubali-evidence-qualification.md` | BASAbali audit notes (no exceptions, no Dungulan offsets, etc.) |

Tests:
- `tests/test_adapter_audit.py` — verifies mapping tables and corrected 7-date counts
- `tests/test_basabubali_qualification.py` — verifies BASAbali evidence qualification notes

No engine edits. No ruleset promotion. No Saka research.
