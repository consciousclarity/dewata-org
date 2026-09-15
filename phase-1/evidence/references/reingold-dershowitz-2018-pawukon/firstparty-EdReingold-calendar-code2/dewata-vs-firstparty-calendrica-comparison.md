# Dewata vs first-party CALENDRICA 4.0 comparison

**Comparison type:** read-only, evidence-only. No engine edits were made.
**Comparison date:** 2026-09-15
**First-party source:** `EdReingold/calendar-code2` commit `9afc1f3277b839db1a70c2350d6c708ac83df78f`, file `calendar.l`, SHA-256 `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484`, git blob sha-1 `2e4ad0f58ac52cb5fd497aa97b2b9ffe57ec623d`, Apache 2.0.
**First-party runtime:** SBCL 2.2.9 on Linux 6.8.0-139-generic.
**Dewata engine:** commit `5d8e7a1e4c4a6dbea809cbab5c8f0da9e0d97b6b` on `warden/phase2-foundation-20260914`.
**Algorithm-equivalence note:** the first-party `calendar.l` and the Calixir `calendrica-4.0.cl` are byte-identical across the entire algorithm body (7344 lines); only the license header differs. The earlier comparison against Calixir (commit 4d37765) therefore applies unchanged to the first-party source. This document re-states the comparison with first-party provenance.

## methodology

### epoch anchor separation

Per the user's instruction: do not describe CALENDRICA's `fixed-from-jd 146` as a "historical Balinese epoch" unless a cultural/historical source supports that interpretation.

Three separate concerns:

1. **algorithmic anchor.** The CALENDRICA source defines `bali-epoch = fixed-from-jd 146 = -1721279 (Rata Die)`. This is an algorithmic choice within the implementation. The function `bali-day-from-fixed(date) = mod(date - bali-epoch, 210)` is well-defined for any `date`, regardless of historical meaning.
2. **mathematical Gregorian conversion.** By the Reingold Rata Die convention (RD 1 = 0001-01-01 Gregorian), RD -1721279 corresponds to proleptic Gregorian -4712-04-18 (4714 BCE). This is a mathematical derivation, not a historical claim.
3. **cultural/historical epoch meaning.** The Pawukon has no canonical epoch (per Wikipedia: "cycles are unnumbered, so the calendar has no epoch, and the choice of date on which to base a correspondence is arbitrary"). No cultural or historical source on this host identifies JD 146 / proleptic Gregorian -4712-04-18 as "the start of a Balinese Pawukon cycle." Therefore: **the JD-146 anchor has no cultural/historical meaning** beyond being the first-party implementation's algorithmic choice. This is recorded as a bibliographic/calendrical fact, not as a culturally-attested epoch.

### cycle-position shift

For Gregorian 1981-08-23 (RD 723415):
- CALENDRICA `bali-day-from-fixed(723415)` = 84 (0-indexed) → 1-indexed position 85
- Dewata `EPOCH = date(1981, 8, 23)` → position 1

The two engines therefore differ by 84 cycle-positions (mod 210) for any given Gregorian date. To compare wewaran fields at the same cycle position, the comparison applies a -84 shift to CALENDRICA's 0-indexed position before deriving the 1-indexed cycle position that Dewata would use.

### wewaran formula alignment

After the cycle-position shift, the field-by-field comparison is:

| field | Dewata formula | CALENDRICA formula (first-party) | reference |
|---|---|---|---|
| Pancawara (5-day) | `((pos-1) % 5) + 1` | `amod((day) + 2, 5)` (formally `1 + mod(day+2, 5)`) | functionally equivalent after cycle-position alignment |
| Saptawara (7-day) | `((pos-1) % 7) + 1` | `1 + mod(day, 7)` | functionally equivalent |
| Triwara (3-day) | `((pos-1) % 3) + 1` | `1 + mod(day, 3)` | functionally equivalent |
| Sadwara (6-day) | `((pos-1) % 6) + 1` | `1 + mod(day, 6)` | functionally equivalent |
| Caturwara (4-day) | special case around day 72 | `amod(bali-asatawara, 4)` | see below |
| Astawara (8-day) | special case around day 72 | `1 + mod(max(6, 4 + mod(day-70, 210)), 8)` | see below |
| Sangawara (9-day) | special case: days 1-3 → 1 (Dangu), else `((p-1) % 9) + 1` | `1 + mod(max(0, day-3), 9)` | see below |
| Dasawara (10-day) | urip-sum: `(urip_5 + urip_7 + 1) % 10` then urip match | `mod(1 + urip_5[i] + urip_7[j], 10)` | urip tables differ |
| Dwiwara | `Menga if urip_sum odd, Pepet if even` | `amod(bali-dasawara-from-fixed(date), 2)` | inputs differ |

## exact 210-day cycle comparison

The full 210-day cycle was generated starting at Gregorian 1981-08-23 (Dewata's EPOCH). For each of 210 cycle positions, Dewata's wewaran fields were compared to first-party CALENDRICA's wewaran fields after cycle-position alignment.

**Generated data:**
- first-party CALENDRICA cycle output: `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2/cycle-comparison/firstparty-cycle-210.csv`
- Dewata cycle output: `phase-1/evidence/references/reingold-dershowitz-2018-pawukon/firstparty-EdReingold-calendar-code2/cycle-comparison/dewata-cycle-210.csv`

### field-by-field counts (full 210-day cycle)

| field | matches / 210 | disagreements / 210 | match percent |
|---|---|---|---|
| cycle position (after -84 shift) | **210 / 210** | **0 / 210** | 100.0% |
| Pancawara | **210 / 210** | **0 / 210** | 100.0% |
| Saptawara | **210 / 210** | **0 / 210** | 100.0% |
| Triwara | **210 / 210** | **0 / 210** | 100.0% |
| Sadwara | **210 / 210** | **0 / 210** | 100.0% |
| **Caturwara** | **12 / 210** | **198 / 210** | 5.7% |
| **Astawara** | **12 / 210** | **198 / 210** | 5.7% |
| **Sangawara** | **125 / 210** | **85 / 210** | 59.5% |
| **Dasawara** | **12 / 210** | **198 / 210** | 5.7% |
| **Dwiwara** | **126 / 210** | **84 / 210** | 60.0% |
| Luang | n/a | n/a | different semantics — not comparable as a direct boolean field |

### cycle boundary test

Positions 207-210 of one cycle plus positions 1-6 of the next cycle (9-day sequence spanning the cycle boundary):

| offset | Gregorian | RD | shifted pos | pan | sap | tri | sad | cat | ast | sng | das |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 207 | 1982-03-18 | 723622 | 208 | 3 | 5 | 1 | 4 | 4 | 8 | 7 | 6 |
| 208 | 1982-03-19 | 723623 | 209 | 4 | 6 | 2 | 5 | 1 | 1 | 8 | 1 |
| 209 | 1982-03-20 | 723624 | 210 | 5 | 7 | 3 | 6 | 2 | 2 | 9 | 8 |
| 210 | 1982-03-21 | 723625 | 1 | 1 | 1 | 1 | 1 | 3 | 3 | 1 | 1 |
| 211 | 1982-03-22 | 723626 | 2 | 2 | 2 | 2 | 2 | 4 | 4 | 2 | 4 |
| 212 | 1982-03-23 | 723627 | 3 | 3 | 3 | 3 | 3 | 1 | 5 | 3 | 1 |

The cycle wraps cleanly at position 210/1 in CALENDRICA. The cycle-boundary behavior matches between first-party CALENDRICA and (after shift) Dewata's position-only field, but Caturwara, Astawara, and Dasawara continue to disagree at most positions.

### representative modern dates (11 dates, separate from the 210-day cycle)

For the 11 representative modern dates (2000-01-01, 2010-06-15, 2025-01-01, 2026-09-01, 2026-09-15, 2026-09-30, 2050-12-31, 1945-08-17, 1971-01-24, 1971-01-27, 1981-08-23):

| field | matches / 11 | disagreements / 11 |
|---|---|---|
| cycle position (after shift) | 11 / 11 | 0 / 11 |
| Pancawara | 11 / 11 | 0 / 11 |
| Saptawara | 11 / 11 | 0 / 11 |
| Triwara | 11 / 11 | 0 / 11 |
| Sadwara | 11 / 11 | 0 / 11 |
| **Caturwara** | **0 / 11** | **11 / 11** |
| **Astawara** | **0 / 11** | **11 / 11** |
| **Sangawara** | **8 / 11** | **3 / 11** |
| **Dasawara** | **1 / 11** | **10 / 11** |

The only date where Dasawara matches is 1981-08-23 (Dewata's EPOCH); for all other modern dates Dasawara disagrees.

## conclusions (NOT resolutions)

1. **Cycle arithmetic (Pancawara, Saptawara, Triwara, Sadwara):** Dewata and first-party CALENDRICA agree on 100% of positions in the full 210-day cycle (210/210 matches). These fields are algorithmically validated against the first-party implementation, claim-scoped.

2. **Cycle position (after shift):** 100% agreement on the 210-day cycle (210/210) and on the 11 representative modern dates (11/11). The shift between CALENDRICA's JD-146 anchor and Dewata's 1981-08-23 anchor is precisely 84 cycle-positions (mod 210), as expected from the difference between JD 146 + 723269 = 723415 (=RD for 1981-08-23) and JD 146's bali-day-from-fixed = 84.

3. **Asatawara/Caturwara special cases:** disagree on 198/210 cycle positions. The CALENDRICA formula uses a continuous `max(6, 4 + mod(day-70, 210))`; Dewata uses a hardcoded day-72/day-73 special case. Without source-level confirmation from prose or customary authority, the correct rule is unresolved.

4. **Sangawara special case:** disagrees on 85/210 cycle positions. CALENDRICA's `max(0, day-3)` formula does not match Dewata's "first three days all Dangu" rule.

5. **Dasawara urip_5 table:** disagrees on 198/210 cycle positions. Dewata uses `(9, 7, 4, 8, 5)` for Paing..Umanis; CALENDRICA uses `(5, 9, 7, 4, 8)`. These are cyclic rotations of each other.

6. **Dwiwara parity basis:** disagrees on 84/210 cycle positions. Dewata uses urip_sum parity; CALENDRICA uses dasawara index parity. These give different results because the urip value is not always equal to the index.

7. **Luang semantics:** CALENDRICA `bali-luang-from-fixed(date) = evenp(bali-dasawara-from-fixed(date))`. Dewata has no direct Luang field. Therefore Luang is **not comparable as a like-for-like boolean** between the two engines; it is omitted from the count.

## claim-scoped verification status (first-party CALENDRICA)

| component | first-party-CALENDRICA-supported claim |
|---|---|
| `pawukon.cycle.modular_arithmetic` | VERIFIED via first-party runtime (210/210 cycle positions agree) |
| `pawukon.cycle.position` | VERIFIED — `mod(date - bali-epoch, 210)` is the canonical formula |
| `pawukon.cycle.duration` | VERIFIED — 210 days |
| `wewaran.pancawara.arithmetic` | VERIFIED (with cycle-position shift) — 210/210 cycle positions agree |
| `wewaran.saptawara.arithmetic` | VERIFIED — 210/210 cycle positions agree |
| `wewaran.triwara.arithmetic` | VERIFIED — 210/210 cycle positions agree |
| `wewaran.sadwara.arithmetic` | VERIFIED — 210/210 cycle positions agree |
| `wewaran.asatawara.special_case_rule` | DISAGREES — 198/210 positions disagree; claim UNRESOLVED |
| `wewaran.caturwara.arithmetic` | DISAGREES transitively (depends on asatawara) — 198/210 positions disagree; claim UNRESOLVED |
| `wewaran.sangawara.special_case_rule` | DISAGREES — 85/210 positions disagree; claim UNRESOLVED |
| `wewaran.dasawara.urip_5_table` | DISAGREES — 198/210 positions disagree; claim UNRESOLVED |
| `wewaran.dasawara.urip_7_table` | matches — `(5, 4, 3, 7, 8, 6, 9)` in both |
| `wewaran.dasawara.formula` | MATCHES in form (urip_5 + urip_7 + 1 mod 10) but values differ |
| `wewaran.dwiwara.parity_basis` | DISAGREES — 84/210 positions disagree; claim UNRESOLVED |
| `conjunction.kajeng_keliwon` | UNVERIFIED at engine level (no comparison run) |
| `conjunction.tumpek` | UNVERIFIED at engine level (no comparison run) |

The first-party CALENDRICA source is now provisionally VERIFIED + ELIGIBLE for the Pancawara/Saptawara/Triwara/Sadwara modular arithmetic claims (4 claims at 210/210 match). Other claims remain UNRESOLVED pending source-level resolution.
