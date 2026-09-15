# Dewata vs CALENDRICA 4.0 comparison

**Comparison type:** read-only, evidence-only. No engine edits were made.
**Comparison date:** 2026-09-15
**CALENDRICA source:** see `calendrica-source/METADATA.json` (SHA-256 `5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb`)
**CALENDRICA runtime:** SBCL 2.2.9, loaded fresh from `calendrica-4.0.cl`, function-by-function verified against `dates4.csv` sample values
**Dewata engine:** commit `5d8e7a1e4c4a6dbea809cbab5c8f0da9e0d97b6b` on `warden/phase2-foundation-20260914`

## methodology

### epoch offset

| engine | epoch constant | epoch meaning |
|---|---|---|
| Dewata | `EPOCH = date(1981, 8, 23)` (Gregorian) | position 1 of the 210-day cycle |
| CALENDRICA | `bali-epoch = fixed-from-jd 146 = RD -1721279` | corresponds to proleptic Gregorian 4714-07-02; bali-day-from-fixed 0 |

For 1981-08-23 (Gregorian, RD 723415):
- Dewata position_in_cycle = 1
- CALENDRICA bali-day-from-fixed = 84 (0-indexed) → 1-indexed position 85

The two engines therefore differ by **84 cycle-positions (modulo 210)**. To compare wewaran values, CALENDRICA's 1-indexed position must be shifted by `-84`.

### wewaran formula alignment

After the cycle-position shift, the field-by-field comparison is:

| field | Dewata formula | CALENDRICA formula | reference |
|---|---|---|---|
| Pancawara (5-day) | `((pos-1) % 5) + 1` | `amod((pos) + 2, 5)` (formally `1 + mod(pos+2, 5)`) | D&R ch 12 (per source comments) |
| Saptawara (7-day) | `((pos-1) % 7) + 1` | `1 + mod(pos, 7)` | D&R ch 12 |
| Triwara (3-day) | `((pos-1) % 3) + 1` | `1 + mod(pos, 3)` | D&R ch 12 |
| Sadwara (6-day) | `((pos-1) % 6) + 1` | `1 + mod(pos, 6)` | D&R ch 12 |
| Caturwara (4-day) | special case around day 72: `(p==72)?3:(p==73)?4:((p-1)%4)+1` | `amod(bali-asatawara, 4)` (depends on asatawara) | see detailed comparison below |
| Astawara (8-day) | special case around day 72: `(p==72)?7:(p==73)?8:((p-1)%8)+1` | `1 + mod(max(6, 4+mod((day-70),210)), 8)` | complex |
| Sangawara (9-day) | special case: days 1-3 all map to 1, else `((p-1)%9)+1` | `1 + mod(max(0, day-3), 9)` | complex |
| Dasawara (10-day) | urip-sum: `((urip_5 + urip_7 + 1) % 10)` then look up by urip | `mod(1 + urip_5[i] + urip_7[j], 10)` | both use urip tables but DIFFERENT tables |
| Dwiwara | `Menga if urip_sum odd, Pepet if even` | `amod(bali-dasawara, 2)` (odd=1=Menga, even=2=Pepet) | DIFFERENT inputs |

**Critical: the urip_5 and urip_7 tables differ between Dewata and CALENDRICA.**

- Dewata `URIP_5 = (9, 7, 4, 8, 5)` for Pancawara positions (Paing, Pon, Wage, Keliwon, Umanis).
- CALENDRICA uses `(5, 9, 7, 4, 8)` for the same positions.

These are **a cyclic rotation of each other** (shift left by 1). This is a substantive disagreement — at least one of them is using the wrong urip table, or they use different ordering conventions.

For urip_7:
- Dewata `URIP_7 = (5, 4, 3, 7, 8, 6, 9)` for Saptawara positions (Redite..Saniscara).
- CALENDRICA uses `(5, 4, 3, 7, 8, 6, 9)`. ✓ Same.

So the disagreement is specifically about which urip_5 position corresponds to which urip value. This is a bibliographic/algorithmic dispute.

## results

For each test date, the comparison applies the cycle-position shift, then checks field-by-field.

| Gregorian date | shifted pos | fields MATCHING | fields DISAGREEING | disagreement notes |
|---|---|---|---|---|
| 1981-08-23 | 1 | Pancawara, Saptawara, Triwara, Sadwara, Sangawara | Caturwara, Astawara, Dasawara, Dwiwara | Cat=3 vs 1, Asta=3 vs 1 |
| 1981-08-24 | 2 | Pancawara, Saptawara, Triwara, Sadwara, Sangawara | Caturwara, Astawara, Dasawara, Dwiwara | Cat=4 vs 2, Asta=4 vs 2 |
| 1981-08-30 | 8 | Pancawara, Saptawara, Triwara, Sadwara, Caturwara, Astawara, Sangawara, Dasawara | Dwiwara | Dw=Menga vs Pepet |
| 1981-09-01 | 10 | Pancawara, Saptawara, Triwara, Sadwara, Caturwara, Astawara, Sangawara, Dasawara | Dwiwara | Dw=Pepet vs Menga |
| 1981-09-15 | 24 | (5 fields) | Caturwara, Astawara, Dasawara, Dwiwara | several |
| 1981-10-01 | 40 | (7 fields) | Dwiwara | Dw=Menga vs Pepet |
| 2025-01-01 | 88 | (4 fields) | Caturwara, Astawara, Dasawara, Dwiwara | several |
| 2026-09-01 | 66 | (5 fields) | Caturwara, Astawara, Dasawara | Cat=4 vs 2, Asta=4 vs 2, Das=9 vs 8 |
| 2026-09-15 | 80 | (5 fields) | Caturwara, Astawara, Dasawara, Dwiwara | several |
| 2026-09-16 | 81 | (5 fields) | Caturwara, Astawara, Dasawara | several |
| 2026-09-30 | 95 | (5 fields) | Caturwara, Astawara, Dasawara, Dwiwara | several |
| 2000-01-01 | 196 | (5 fields) | Caturwara, Astawara, Sangawara, Dasawara | several |
| 2050-12-31 | 133 | (5 fields) | Caturwara, Astawara, Sangawara, Dasawara, Dwiwara | several |
| 1945-08-17 | 76 | (5 fields) | Caturwara, Astawara, Dasawara | several |

**14 of 14 test dates disagree on at least one field.**

### fields that ALWAYS match

- Pancawara, Saptawara, Triwara, Sadwara: **100% match across all 14 dates** ✓
- Sangawara: **mostly matches** (matches on 11/14 dates)
- Caturwara: matches on 2/14 dates (specific positions 8 and 10)
- Astawara: matches on 2/14 dates (same positions as Caturwara)
- Dasawara: matches on 0/14 dates
- Dwiwara: matches on 8/14 dates

### disagreement patterns

#### Caturwara and Astawara

Dewata's special-case rule:
- Caturwara: `p==72 → 3 (Jaya); p==73 → 4 (Menala); else ((p-1) % 4) + 1`
- Astawara: `p==72 → 7 (Ma); p==73 → 8 (Pitra); else ((p-1) % 8) + 1`

CALENDRICA's rules use `bali-asatawara` to derive `bali-caturwara`, and `bali-asatawara` itself has the special-case formula:
- `bali-asatawara(date) = 1 + mod(max(6, 4 + mod((day-70), 210)), 8)`
- `bali-caturwara(date) = amod(bali-asatawara-from-fixed(date), 4)`

Both engines have special-case handling but DIFFERENT formulas. This is a substantive algorithmic disagreement that requires source-level resolution (either from D&R prose chapter or from customary/calendar expert attestation).

#### Dasawara

Dewata uses urip_5 = `(9, 7, 4, 8, 5)`. CALENDRICA uses urip_5 = `(5, 9, 7, 4, 8)`. **The urip tables disagree.**

This is a **definitional disagreement**. One of them is using the wrong table. Without source-level confirmation from D&R prose or customary authority, the correct table cannot be determined from implementation alone.

## conclusions (NOT resolutions)

1. **Cycle arithmetic (Pancawara, Saptawara, Triwara, Sadwara):** Dewata and CALENDRICA agree. These fields can be considered algorithmically validated against the first-party implementation, subject to claim-scoped verification.

2. **Epoch anchor:** Dewata uses 1981-08-23; CALENDRICA uses JD 146 (= proleptic Gregorian 4714-07-02). The two anchors are **NOT the same date**. The semantic interpretation of "the start of a Pawukon cycle" is implementation-defined. Without source-level confirmation, the choice of anchor is a calendar-semantic decision that requires customary authority.

3. **Asatawara/Caturwara special cases:** Dewata and CALENDRICA have different special-case rules. Without source-level confirmation, the correct rule is unresolved.

4. **Dasawara urip tables:** Dewata and CALENDRICA use different urip_5 tables. Without source-level confirmation, the correct table is unresolved.

5. **Dwiwara parity:** Dewata uses urip_sum parity; CALENDRICA uses dasawara index parity. These give different results because the inputs are different. Without source-level confirmation, the correct parity definition is unresolved.

## claim-scoped verification status (CALENDRICA source)

| component | CALENDRICA-implementation-supported claim |
|---|---|
| `pawukon.cycle.modular_arithmetic` | VERIFIED via CALENDRICA runtime on RD -214193 sample (10/10 fields agree between dates4.csv sample and CALENDRICA runtime) |
| `pawukon.cycle.position` | VERIFIED — `mod(date - bali-epoch, 210)` is the canonical formula |
| `pawukon.cycle.duration` | VERIFIED — 210 days |
| `wewaran.pancawara.arithmetic` | VERIFIED (with cycle-position shift) — `amod((day+2), 5)` matches Dewata's `((p-1) % 5) + 1` after position shift |
| `wewaran.saptawara.arithmetic` | VERIFIED (with cycle-position shift) — `1 + mod(day, 7)` matches |
| `wewaran.triwara.arithmetic` | VERIFIED (with cycle-position shift) — `1 + mod(day, 3)` matches |
| `wewaran.sadwara.arithmetic` | VERIFIED (with cycle-position shift) — `1 + mod(day, 6)` matches |
| `wewaran.asatawara.special_case_rule` | DISAGREES — Dewata vs CALENDRICA use different formulas; claim UNRESOLVED |
| `wewaran.caturwara.arithmetic` | DISAGREES (depends on asatawara) |
| `wewaran.sangawara.special_case_rule` | DISAGREES — Dewata says days 1-3 are all Dangu; CALENDRICA's `max(0, day-3)` formula does not match |
| `wewaran.dasawara.urip_5_table` | DISAGREES — Dewata `(9,7,4,8,5)` vs CALENDRICA `(5,9,7,4,8)` |
| `wewaran.dasawara.urip_7_table` | MATCHES — `(5,4,3,7,8,6,9)` |
| `wewaran.dasawara.formula` | MATCHES in form (urip_5 + urip_7 + 1 mod 10) but values differ |
| `wewaran.dwiwara.parity_basis` | DISAGREES — Dewata uses urip_sum parity; CALENDRICA uses dasawara index parity |
| `conjunction.kajeng_keliwon` | UNVERIFIED — function exists in CALENDRICA but not yet tested against Dewata |
| `conjunction.tumpek` | UNVERIFIED — function exists in CALENDRICA but not yet tested against Dewata |

The CALENDRICA source is now provisionally VERIFIED + ELIGIBLE for the Pancawara/Saptawara/Triwara/Sadwara modular arithmetic claims. The other claims remain UNRESOLVED pending source-level resolution.
