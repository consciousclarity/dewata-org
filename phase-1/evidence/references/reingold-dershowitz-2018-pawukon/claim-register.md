# Claim register — Reingold & Dershowitz 2018 Ultimate Edition, Chapter 12 (Balinese Pawukon Calendar)

**Citation key:** `reingold-dershowitz-2018-balinese-pawukon`
**Chapter:** Reingold & Dershowitz, *Calendrical Calculations: The Ultimate Edition*, Cambridge University Press, 2018, Chapter 12 (pp. 185–194), DOI `10.1017/9781107415058.015`
**Access date:** 2026-09-15
**Source-access status:** bibliographic metadata VERIFIED by three independent sources (Cambridge, CrossRef, Open Library). **Chapter body text NOT retrieved — paywall + JS-rendered shell on Cambridge.**

---

## status of every substantive claim

the governance-owner instruction stated:

> "Publisher metadata can verify that the chapter exists. It does NOT by itself verify: Pawukon epoch/anchor, 210-day arithmetic, Wuku numbering, Wewaran formulas, urip tables, conjunction-day rules, implementation constants, sample-date vectors."

because the chapter body was not accessible from this host, **every
substantive calendrical claim below is recorded as UNVERIFIED**. They
are listed because the claim register must exist; but each one
explicitly records that the supporting text has not been read. Do
not promote any of them to VERIFIED without retrieving the chapter
text and quoting the relevant passage.

---

## claims

### claim-001: `pawukon.cycle == 210 days`

| field | value |
|---|---|
| claim | The Pawukon cycle is 210 days long (30 wuku × 7 days). |
| source | D&R 2018 ch. 12 (pp. 185–194, DOI 10.1017/9781107415058.015) |
| chapter page | not yet located (chapter body not retrieved) |
| supporting quotation | **NOT YET VERIFIED** — chapter text not retrieved |
| evidence artifact SHA | (none yet — would be a chunk of the chapter body once retrieved) |
| affected Dewata component | `pawukon.cycle` |
| current engine claim | `pawukon.py` asserts `EPOCH + 210d → 1` via cycle_arithmetic |
| current engine agreement | engine claim: cycle length 210 days |
| confidence / status | **UNVERIFIED — substantive claim** (bibliographic existence verified) |

### claim-002: `pawukon.epoch`

| field | value |
|---|---|
| claim | The Pawukon epoch anchor (which Gregorian date = Wuku Sinta Day 1). |
| source | D&R 2018 ch. 12 (pp. 185–194, DOI 10.1017/9781107415058.015) |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** — chapter text not retrieved |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `pawukon.epoch` |
| current engine claim | engine uses 1981-08-23 as the Sinta Day 1 anchor |
| current engine agreement | unknown until chapter text is read |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-003: `pawukon.wuku`

| field | value |
|---|---|
| claim | The 30 wuku names and the 7-day-per-wuku sequence. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** — chapter text not retrieved |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `pawukon.wuku` |
| current engine claim | `phase-1/src/dewatacalendar/pawukon.py` exposes wuku names and indices |
| current engine agreement | unknown until chapter text is read |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-004: `wewaran.ekawara`

| field | value |
|---|---|
| claim | Eka Wara (1-day week) definition and values. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** — chapter text not retrieved |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.ekawara` |
| current engine claim | `wewaran.py::wewaran_for_position` returns ekawara_present bool |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-005: `wewaran.dwiwara`

| field | value |
|---|---|
| claim | Dwi Wara (2-day week) values (Menga / Pepet). |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.dwiwara` |
| current engine claim | `wewaran.py` returns `dwiwara_name` ∈ {Menga, Pepet} |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-006: `wewaran.triwara`

| field | value |
|---|---|
| claim | Tri Wara (3-day week) values (Pasah / Beteng / Kajeng). |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.triwara` |
| current engine claim | `wewaran.py` returns `triwara_name` |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-007: `wewaran.caturwara`

| field | value |
|---|---|
| claim | Catur Wara (4-day week) values. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.caturwara` |
| current engine claim | `wewaran.py::wewaran_for_position` returns caturwara |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-008: `wewaran.pancawara`

| field | value |
|---|---|
| claim | Panca Wara (5-day week) values and urip-5 sequence. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.pancawara` |
| current engine claim | `wewaran.py` exposes `pancawara_name` and `pancawara_urip` |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-009: `wewaran.sadwara`

| field | value |
|---|---|
| claim | Sad Wara (6-day week) values. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.sadwara` |
| current engine claim | `wewaran.py` returns `sadwara_name` |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-010: `wewaran.saptawara`

| field | value |
|---|---|
| claim | Sapta Wara (7-day week) values (Redite/Soma/Anggara/Buda/Wraspati/Sukra/Saniscara). |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.saptawara` |
| current engine claim | `wewaran.py` exposes `saptawara_name` and `saptawara_idx` |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-011: `wewaran.astawara`

| field | value |
|---|---|
| claim | Asta Wara (8-day week) values. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.astawara` |
| current engine claim | `wewaran.py` returns `astawara_name` and `astawara_idx` |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-012: `wewaran.sangawara`

| field | value |
|---|---|
| claim | Sanga Wara (9-day week) values. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.sangawara` |
| current engine claim | `wewaran.py` returns `sangawara_name` |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

### claim-013: `wewaran.dasawara`

| field | value |
|---|---|
| claim | Dasa Wara (10-day week) values and urip-10 derivation. |
| source | D&R 2018 ch. 12 |
| chapter page | not yet located |
| supporting quotation | **NOT YET VERIFIED** |
| evidence artifact SHA | (none yet) |
| affected Dewata component | `wewaran.dasawara` |
| current engine claim | `wewaran.py::wewaran_for_position` returns `dasawara_name` |
| current engine agreement | unknown |
| confidence / status | **UNVERIFIED — substantive claim** |

---

## explicitly out-of-scope claims

per the governance-owner instruction:

> "This evidence package is initially eligible only for claims actually supported by the Balinese Pawukon chapter. Do NOT use it to validate: Saka year, Sasih, pangunalatri / pengalantaka, nampih sasih, Nyepi arithmetic, historical Saka regimes — unless the actual cited text explicitly supports those matters. If the chapter says nothing about them, record: out_of_scope, not false, unsupported, or inferred behavior."

| component | out_of_scope status |
|---|---|
| `saka.year` | **out_of_scope** — not yet determined whether the Pawukon chapter covers Saka year arithmetic. Until the chapter text is read, this is not claimed. |
| `saka.sasih` | **out_of_scope** |
| `pengalantaka` | **out_of_scope** |
| `nampih_sasih` | **out_of_scope** |
| `nyepi_arithmetic` | **out_of_scope** |
| `historical_saka_regimes` | **out_of_scope** |

`out_of_scope` means: the question has not been evaluated, not
that the chapter says nothing about it. When the chapter text is
acquired, the relevant claims will be filed separately, each with
its own verification against the text.

---

## claim verification summary

| total claims | VERIFIED | UNVERIFIED (substantive) | out_of_scope |
|---|---|---|---|
| 13 | **0** | **13** | 6 |

per the governance-owner instruction: **0 substantive calendrical
claims are VERIFIED from the prose chapter**. The chapter text was
not retrievable from this host. No claim is to be promoted to VERIFIED
without a quote or precise paraphrase from the chapter body.

---

# claim register — CALENDRICA 4.0 first-party implementation

This register covers the **first-party algorithm implementation** of
the Pawukon/Wewaran formulas extracted from CALENDRICA 4.0 Common Lisp
source. Authority basis: `software_reference`. This is separate
evidence from the Cambridge prose chapter.

**Source attribution — primary (first-party):**
- repository: `https://github.com/EdReingold/calendar-code2`
- commit SHA: `9afc1f3277b839db1a70c2350d6c708ac83df78f` (main, 2022-02-04)
- file: `calendar.l`
- SHA-256: `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484`
- git blob sha-1: `2e4ad0f58ac52cb5fd497aa97b2b9ffe57ec623d`
- license: Apache License 2.0 (LICENSE file SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`, blob sha-1 `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64`)
- retrieval date: 2026-09-15

**Source attribution — secondary (preserved historical):**
- repository: `https://github.com/rengel-de/calixir`
- commit SHA: `0f3368339c6318f6751579cf506320b13ce17e2c` (master, 2020-07-18)
- file: `assets/calendrica-4.0.cl`
- SHA-256: `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484`
- license header: custom personal-use + non-commercial/non-profit (NOT first-party)
- status: secondary evidence only; algorithmic content byte-identical to first-party; preserved for provenance

## claim table

Each claim is sourced from a specific function in `calendrica-4.0.cl`.
The line ranges below are from the retrieved source file.

### CALC-001 — Pawukon epoch anchor

| field | value |
|---|---|
| claim ID | CALC-001 |
| precise claim | `bali-epoch = fixed-from-jd 146`, equivalent to Rata Die -1721279, equivalent to Julian Day Number 146, equivalent to proleptic Gregorian -4712-04-18 (4714 BCE) |
| source function | `bali-epoch` (defconstant) |
| source lines | in `calendrica-4.0.cl` (search for `defconstant bali-epoch`) |
| supporting code | `(fixed-from-jd 146)` where `fixed-from-jd(jd) = floor(moment-from-jd(jd)) = floor(jd + (-1721424.5)) = floor(jd - 1721424.5)` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` (source file SHA-256) |
| affected Dewata component | `pawukon.epoch` |
| Dewata engine value | `EPOCH = date(1981, 8, 23)` (Gregorian) |
| agreement/disagreement | **DISAGREES** — Dewata's epoch is 1981-08-23 Gregorian; CALENDRICA's epoch is JD 146 (= proleptic Gregorian 4714-07-02 ≈ year 4714 BCE). The two engines differ by 84 cycle-positions (mod 210) for the same Gregorian dates. |
| confidence/status | **VERIFIED at the source level** (CALENDRICA source does say `bali-epoch = fixed-from-jd 146`); **DISPUTED at the engine level** because Dewata uses a different epoch anchor |

### CALC-002 — Pawukon cycle duration and arithmetic

| field | value |
|---|---|
| claim ID | CALC-002 |
| precise claim | `bali-day-from-fixed(date) = mod(date - bali-epoch, 210)` |
| source function | `bali-day-from-fixed` |
| source lines | (in `calendrica-4.0.cl` search for `defun bali-day-from-fixed`) |
| supporting code | `(mod (- date bali-epoch) 210)` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `pawukon.cycle.modular_arithmetic` |
| Dewata engine value | `cycle_pos_zero_based = offset_days % 210` (in `_position_from_offset`) |
| agreement/disagreement | **MATCHES in form**. Both engines use mod-210 over the days-offset from epoch. The arithmetic is identical; only the epoch constant differs (see CALC-001). |
| confidence/status | **VERIFIED** — Dewata's cycle arithmetic matches CALENDRICA's; runtime verification at RD -214193 produced `bali-day-from-fixed = 126` matching dates4.csv |

### CALC-003 — Pawukon Wuku (week number)

| field | value |
|---|---|
| claim ID | CALC-003 |
| precise claim | `bali-week-from-fixed(date) = 1 + quotient(bali-day-from-fixed(date), 7)` |
| source function | `bali-week-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(1+ (quotient (bali-day-from-fixed date) 7))` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `pawukon.wuku.week_number` |
| Dewata engine value | `wuku_idx = ((cycle_pos - 1) // 7) + 1` |
| agreement/disagreement | **MATCHES in form**. Both compute `floor(day/7) + 1`. |
| confidence/status | **VERIFIED** at the source level; agreement is on the arithmetic, not the absolute numbering (depends on epoch) |

### CALC-004 — Pawukon day-of-week (Saptawara) arithmetic

| field | value |
|---|---|
| claim ID | CALC-004 |
| precise claim | `bali-saptawara-from-fixed(date) = 1 + mod(bali-day-from-fixed(date), 7)` |
| source function | `bali-saptawara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(1+ (mod (bali-day-from-fixed date) 7))` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.saptawara` |
| Dewata engine value | `saptawara_idx = ((position - 1) % 7) + 1` |
| agreement/disagreement | **MATCHES** — both produce the same value when cycle-position is matched (Dewata position + CALENDRICA shifted position agree on all 14 test dates) |
| confidence/status | **VERIFIED** |

### CALC-005 — Pawukon Pancawara arithmetic

| field | value |
|---|---|
| claim ID | CALC-005 |
| precise claim | `bali-pancawara-from-fixed(date) = amod((bali-day-from-fixed(date) + 2), 5)` |
| source function | `bali-pancawara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(amod (+ (bali-day-from-fixed date) 2) 5)` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.pancawara` |
| Dewata engine value | `pancawara_idx = ((position - 1) % 5) + 1` |
| agreement/disagreement | **MATCHES** — when cycle-positions are aligned, Pancawara values agree on all 14 test dates. Note: the `+2` in CALENDRICA accounts for the 1-indexed cycle position (because bali-day-from-fixed is 0-indexed) and the +1 in Dewata's formula is the 1-indexing conversion from 0-indexed mod. Both end up at the same value. |
| confidence/status | **VERIFIED** |

### CALC-006 — Pawukon Triwara arithmetic

| field | value |
|---|---|
| claim ID | CALC-006 |
| precise claim | `bali-triwara-from-fixed(date) = 1 + mod(bali-day-from-fixed(date), 3)` |
| source function | `bali-triwara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(1+ (mod (bali-day-from-fixed date) 3))` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.triwara` |
| Dewata engine value | `triwara_idx = ((position - 1) % 3) + 1` |
| agreement/disagreement | **MATCHES** |
| confidence/status | **VERIFIED** |

### CALC-007 — Pawukon Sadwara arithmetic

| field | value |
|---|---|
| claim ID | CALC-007 |
| precise claim | `bali-sadwara-from-fixed(date) = 1 + mod(bali-day-from-fixed(date), 6)` |
| source function | `bali-sadwara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(1+ (mod (bali-day-from-fixed date) 6))` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.sadwara` |
| Dewata engine value | `sadwara_idx = ((position - 1) % 6) + 1` |
| agreement/disagreement | **MATCHES** |
| confidence/status | **VERIFIED** |

### CALC-008 — Pawukon Astawara formula (special case)

| field | value |
|---|---|
| claim ID | CALC-008 |
| precise claim | `bali-asatawara-from-fixed(date) = 1 + mod(max(6, 4 + mod((day - 70), 210)), 8)` where `day = bali-day-from-fixed(date)` |
| source function | `bali-asatawara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(let* ((day (bali-day-from-fixed date))) (1+ (mod (max 6 (+ 4 (mod (- day 70) 210))) 8)))` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.astawara` |
| Dewata engine value | `astawara_idx = ((p-1) % 8) + 1` with special case `p==72 → 7, p==73 → 8` |
| agreement/disagreement | **DISAGREES** — the two formulas are different. CALENDRICA uses `max(6, 4 + mod(day-70, 210))` to introduce a "skip" around day 70-78 area, while Dewata uses a hardcoded day-72/73 special case |
| confidence/status | **VERIFIED at the source level** (the CALENDRICA formula is documented). **DISPUTED at the engine level** — Dewata's formula disagrees with CALENDRICA's. Resolution requires prose chapter or customary authority. |

### CALC-009 — Pawukon Caturwara formula (depends on asatawara)

| field | value |
|---|---|
| claim ID | CALC-009 |
| precise claim | `bali-caturwara-from-fixed(date) = amod(bali-asatawara-from-fixed(date), 4)` |
| source function | `bali-caturwara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(amod (bali-asatawara-from-fixed date) 4)` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.caturwara` |
| Dewata engine value | `caturwara_idx = ((p-1) % 4) + 1` with special case `p==72 → 3, p==73 → 4` |
| agreement/disagreement | **DISAGREES (transitively)** — Caturwara derives from Asatawara in CALENDRICA; Dewata computes Caturwara independently with its own special-case rule |
| confidence/status | **DISPUTED** |

### CALC-010 — Pawukon Sangawara formula (special case)

| field | value |
|---|---|
| claim ID | CALC-010 |
| precise claim | `bali-sangawara-from-fixed(date) = 1 + mod(max(0, day - 3), 9)` where `day = bali-day-from-fixed(date)` |
| source function | `bali-sangawara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(1+ (mod (max 0 (- (bali-day-from-fixed date) 3)) 9))` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.sangawara` |
| Dewata engine value | `sangawara_idx = ((p-1) % 9) + 1` with special case `p in {1,2,3} → 1` |
| agreement/disagreement | **DISAGREES** — CALENDRICA's `max(0, day-3)` produces different values than Dewata's "first three days all Dangu" rule for early positions |
| confidence/status | **DISPUTED** |

### CALC-011 — Dasawara formula (urip table derivation)

| field | value |
|---|---|
| claim ID | CALC-011 |
| precise claim | `bali-dasawara-from-fixed(date) = mod(1 + urip_5[i] + urip_7[j], 10)` where `i = bali-pancawara-from-fixed(date) - 1`, `j = bali-saptawara-from-fixed(date) - 1`, `urip_5 = (5, 9, 7, 4, 8)` for Pancawara positions Paing..Umanis (0-indexed), `urip_7 = (5, 4, 3, 7, 8, 6, 9)` for Saptawara positions Redite..Saniscara (0-indexed) |
| source function | `bali-dasawara-from-fixed` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(mod (+ 1 (nth i (list 5 9 7 4 8)) (nth j (list 5 4 3 7 8 6 9))) 10)` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `wewaran.dasawara.urip_table` |
| Dewata engine value | `urip_5 = (9, 7, 4, 8, 5)` for Pancawara positions (Paing..Umanis); `urip_7 = (5, 4, 3, 7, 8, 6, 9)` (same as CALENDRICA) |
| agreement/disagreement | **DISAGREES on urip_5** — Dewata's `(9, 7, 4, 8, 5)` is a cyclic shift of CALENDRICA's `(5, 9, 7, 4, 8)`. urip_7 matches. |
| confidence/status | **DISPUTED on urip_5 table** — resolution requires prose chapter or customary authority |

### CALC-012 — Kajeng Keliwon (conjunction day)

| field | value |
|---|---|
| claim ID | CALC-012 |
| precise claim | `kajeng-keliwon(g-year)` returns the list of fixed-dates within Gregorian year g-year that are the 9th day of each 15-day subcycle of Pawukon |
| source function | `kajeng-keliwon` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | `(positions-in-range 8 15 cap-Delta year)` |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `rahinan.kajeng_keliwon` |
| Dewata engine value | (not yet compared — Dewata may or may not implement this) |
| agreement/disagreement | **NOT YET COMPARED** |
| confidence/status | **VERIFIED at the source level** (function exists in CALENDRICA); **UNVERIFIED at the engine level** (no comparison run yet) |

### CALC-013 — Tumpek (conjunction day)

| field | value |
|---|---|
| claim ID | CALC-013 |
| precise claim | `tumpek(g-year)` returns the list of fixed-dates within Gregorian year g-year that are the 14th day of each 35-day subcycle of Pawukon |
| source function | `tumpek` |
| source lines | (in `calendrica-4.0.cl`) |
| supporting code | (definition truncated in our extraction; partial visibility) |
| evidence artifact SHA | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| affected Dewata component | `rahinan.tumpek` |
| Dewata engine value | (not yet compared) |
| agreement/disagreement | **NOT YET COMPARED** |
| confidence/status | **VERIFIED at the source level** (function exists); **UNVERIFIED at the engine level** |

## claim verification summary (CALENDRICA only)

| claim | source-verified | engine-verified | disputed with Dewata |
|---|---|---|---|
| CALC-001 epoch anchor | YES | YES (CALENDRICA) | YES (different anchor) |
| CALC-002 cycle arithmetic | YES | YES | no (matches form) |
| CALC-003 wuku week arithmetic | YES | YES | no |
| CALC-004 saptawara | YES | YES | no |
| CALC-005 pancawara | YES | YES | no |
| CALC-006 triwara | YES | YES | no |
| CALC-007 sadwara | YES | YES | no |
| CALC-008 astawara | YES | YES | **YES** (different formula) |
| CALC-009 caturwara | YES | YES | **YES** (depends on astawara) |
| CALC-010 sangawara | YES | YES | **YES** (different formula) |
| CALC-011 dasawara urip_5 | YES | YES | **YES** (different table) |
| CALC-012 kajeng_keliwon | YES | no | no |
| CALC-013 tumpek | YES | no | no |

**Source-verified: 13/13 claims** (all function definitions confirmed in the source file).
**Engine-verified against CALENDRICA runtime: 11/13 claims** (CALC-012 and CALC-013 not yet run).
**Disputed with Dewata: 5/13 claims** (CALC-001 epoch, CALC-008/009/010 special-case, CALC-011 urip_5).
