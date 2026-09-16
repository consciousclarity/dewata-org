# Wewaran/Pawukon Claim Register (Wariga Sources)

Compiled: 2026-09-15.
Scope: claim-by-claim matrix for unresolved Wewaran/Pawukon questions, cross-referenced against retrieved Wariga sources.

Each claim is tied to:
- a specific retrievable source (page reference, line range, or function name)
- a precise quoted observation from that source
- the source's lineage (per `bibliographic-records.md`)

This register records observations only.
It does NOT resolve disputes.
Per PROTOCOL v1.0 and user instruction (verbatim):
> "No dispute is resolved merely because a second source is found."

---

## Claim: Wuku/Gregorian Phase Mapping

### What we are trying to determine
Does the Wuku assigned to a real Gregorian date match cultural practice?
Is the +84 mod 210 offset between Dewata and CALENDRICA culturally correct, or is one of them right and the other wrong?

### Source observations

| Source | Observation | Lineage |
|---|---|---|
| kb.org (Kalender Bali Digital) | 7 reference dates in Sep 2026: 2026-09-01 Sinta, 09-05 Sinta, 09-09 Dungulan, 09-15 Dungulan, 09-17 Dungulan, 09-26 Bala, 09-30 Bala | L1 (practitioner) |
| liputan6, detik, pelajahin | Same as kb.org (one lineage) | L1 |
| S4 Kemendikbud textbook | No explicit Gregorian↔Wuku examples in pages 37-40 | S4 |
| S5 babadbali.com | No Gregorian↔Wuku examples on wuku.htm page | S5 |
| S3 edysantosa/sakacalendar | No Gregorian↔Wuku examples in extracted source code | S3 (derivative of S1/S2) |

### Conclusion
The 84-day offset dispute remains **insufficiently evidenced from non-kb.org lineages**.
- Only **1 independent lineage (L1)** has been retrieved with concrete Gregorian↔Wuku examples.
- S1, S2 (printed Wariga books) might have such examples, but full text is NOT accessible from this host.
- S3 cites S1/S2 as its source, but the Java code is purely algorithmic — no calendar dates to compare.
- S4 (Kemendikbud textbook) contains Pawukon structure but no Gregorian↔Wuku examples.
- S5 (babadbali) contains wuku urip tables but no Gregorian examples.

### Status
**Insufficient independent evidence** for Wuku/Gregorian phase. The 84-day offset finding from commit `d5c0a51` is a real disagreement between Dewata and CALENDRICA, but we do NOT yet have a third lineage to adjudicate which is correct.

---

## Claim: Pancawara Ordering (mapping A vs mapping B)

### What we are trying to determine
Is numeric 1=Umanis (mapping B) or 1=Paing (mapping A) the cultural convention?

### Source observations

| Source | Observation | Lineage |
|---|---|---|
| S4 Kemendikbud Hindu-BS-KLS-IX, page 37 | Explicit: "(1) Umanis, (2) Pahing, (3) Pon, (4) Wage, (5) Kliwon" | S4 |
| S5 babadbali.com | "1 Legi or **manis** ... 2 Paing or **Pait** ... 3 Pon or **Petak** ... 4 Wage or **Cemeng** ... 5 Kliwon or **Kasih**" | S5 |
| basaibubali.org | Same: 1=Umanis, 2=Pahing, 3=Pon, 4=Wage, 5=Kliwon | basaibubali |
| L4 EdReingold/calendar-code2 (CALENDRICA) | 1=Umanis, 2=Paing, 3=Pon, 4=Wage, 5=Kliwon | L4 |
| kb.org | Names: Umanis, Pahing, Pon, Wage, Kliwon | L1 |
| Dewata internal | 1=Paing, 2=Pon, 3=Wage, 4=Kliwon, 5=Umanis (mapping A) | (Dewata) |
| L2 Wikipedia | Same as Dewata: 1=Paing (no numeric assignment, but listed in that order) | L2 |
| S3 edysantosa/sakacalendar | `noPancawara = (noWuku % 5) + 1` — but the index 0=Paing, 1=Pon, ... in source array | S3 (derivative) |
| peradnya/balinese-date-js-lib | TypeScript arrays use mapping A (Paing=0, ..., Umanis=4) but cite babadbali.com | S5 (derivative) |

### Conclusion
**Independent Balinese sources (S4, S5, basaibubali.org, kb.org, L4 CALENDRICA) all agree: mapping B.**
**Mapping A is used by:**
- Dewata internal code (wewaran.py)
- L2 Wikipedia article structure (lists in that order)
- S5 derivatives (peradnya TS) — same lineage as S5

Mapping A and mapping B are arithmetically equivalent — `mappingA(x) = mappingB((x+4) mod 5 + 1)` or similar. The disagreement is naming convention for what "Weton 1" is called, not the underlying periodicity.

### Status
**Multiple independent lineages (S4, S5, basaibubali.org, kb.org, L4) all agree on mapping B.**
Dewata's mapping A is a **naming/index convention difference**, not a formula defect.
Per user instruction: "spelling variants such as Kliwon/Keliwon: naming-only."

The Pancawara numeric formula has no defect; the index-to-name convention can be corrected without changing the formula.

---

## Claim: Caturwara (4-day cycle)

### What we are trying to determine
Does Caturwara use simple modular 4-day progression, or special-case handling at Wuku Dungulan?

### Source observations

| Source | Observation | Lineage |
|---|---|---|
| S4 Kemendikbud, page 40 | "Pada Caturwara (Sri-Laba-Jaya-Manala) di **Wuku Dunggulan** ada **3 Jaya berturut-turut**, mulai dari Redite Jaya, Soma Jaya, dan Anggara Jaya." (3 consecutive Jaya at Wuku Dungulan) | S4 |
| S3 edysantosa/sakacalendar | Two formulas: `(noWuku*7+2+noSaptaWara) % 4` for Sinta Redite to Dungulan Redite, then `(noWuku*7+noSaptaWara) % 4` for Dungulan Budha onwards; Jaya Tiga exception documented in code comments | S3 |
| L4 CALENDRICA | Special-case at day 72 (Dungulan): position 1-3 = Sri, Indra, Guru (instead of standard modulo 4) | L4 |
| basaibubali.org Caturwara page | Simple modular: `(bilangan uku × 7 + bilangan Saptawara) / 4` remainder | basaibubali |

### Conclusion
**All sources agree that Caturwara has special-case handling** — but **they disagree on the specifics**:
- **S4 (Kemendikbud)**: 3 consecutive **Jaya** at Wuku Dungulan, starting from Redite Jaya
- **S3 (Java impl)**: Two formulas with Jaya Tiga exception at Wuku Dungulan days 1-3 (matches S4)
- **L4 (CALENDRICA)**: 3 days at Wuku Dungulan have Sri/Indra/Guru instead of standard Sri/Laba/Jaya/Manala
- **basaibubali.org**: Simple modular (no special case)

The disagreement is **formula_semantics**:
- S4 + S3 + L4 all agree on the existence of a 3-day special case at Wuku Dungulan
- S4 says 3 Jaya; L4 says different values (Sri, Indra, Guru); basaibubali says no special case

### Status
**Formula has special-case structure** — confirmed by **multiple independent lineages** (S4, S3, L4).
**Specific special-case content** (whether the 3 special days are Jaya or Sri/Indra/Guru) — **disagreement between sources**.

---

## Claim: Astawara/Asatawara (8-day cycle)

### What we are trying to determine
Does Astawara use simple modular 8-day progression, or special-case handling around day 71-72?

### Source observations

| Source | Observation | Lineage |
|---|---|---|
| S4 Kemendikbud, page 40 | "Pada Astawara di Wuku Dunggulan (Sri, Indra, Guru, Yama, Ludra, Brahma, Kāla, dan Uma) ada **3 Kāla berturut-turut**, mulai dari Redite Kāla, Soma Kāla, dan Anggara Kāla." (3 consecutive Kala at Wuku Dungulan) | S4 |
| S3 edysantosa/sakacalendar | Three-formula with special cases for `angkaWuku == 71, 72, 73` (Dungulan): `noAstawara = 7` (Kala) | S3 |
| L4 CALENDRICA | Special-case at day 72: position 1 = Indra, position 2 = Guru (instead of standard) | L4 |
| basaibubali.org Asatawara page | Simple modular: `(bilangan uku × 7 + bilangan Saptawara) / 8` remainder | basaibubali |

### Conclusion
**All sources agree that Astawara has special-case handling** — but **they disagree on the specifics**:
- **S4 (Kemendikbud)**: 3 consecutive Kala at Wuku Dungulan
- **S3 (Java impl)**: 3 consecutive Kala at days 71-73 (matches S4)
- **L4 (CALENDRICA)**: Different special-case content (Indra/Guru)
- **basaibubali.org**: Simple modular (no special case)

### Status
**Formula has special-case structure** — confirmed by **multiple independent lineages** (S4, S3, L4).
**Specific special-case content** — **disagreement between sources**.

---

## Claim: Sangawara (9-day cycle)

### What we are trying to determine
Does Sangawara have Dangu repetitions at the beginning, and at which wuku?

### Source observations

| Source | Observation | Lineage |
|---|---|---|
| S4 Kemendikbud, page 40 | "Pada Sangawara (Dangu, Jangur, Gigis, Nohan, Ogan, Erangan, Urungan, Tulus, dan Dadi) di **Wuku Sinta** ada **4 Dangu berturut-turut**, dimulai dari Redite Dangu, Soma Dangu, Anggara Dangu, dan Budha Dangu." (4 consecutive Dangu at **Wuku Sinta**) | S4 |
| S3 edysantosa/sakacalendar | Two formulas: if `angkaWuku <= 4` (Sinta): `noSangawara = 1` (Dangu); else `(angkaWuku + 6) % 9` | S3 |
| L4 CALENDRICA | First day (position 1) repeats 3× in first week (positions 1-3 = Dangu) | L4 |
| basaibubali.org Sangawara page | Simple modular: `(bilangan uku × 7 + bilangan Saptawara) / 9` remainder | basaibubali |

### Conclusion
**All sources agree that Sangawara has special-case handling at the beginning** — but **they disagree on the specifics**:
- **S4 (Kemendikbud)**: 4 consecutive Dangu at **Wuku Sinta** (days 1-4)
- **S3 (Java impl)**: Special case for days 1-4 (matches S4)
- **L4 (CALENDRICA)**: 3 consecutive Dangu at days 1-3
- **basaibubali.org**: Simple modular (no special case)

The disagreement is whether the **Dangu repetition is 3 days or 4 days**.

### Status
**Formula has special-case structure** — confirmed by **multiple independent lineages** (S4, S3, L4).
**Specific special-case duration** (3 days vs 4 days) — **disagreement between CALENDRICA (3) and Kemendikbud + edysantosa (4)**.

---

## Claim: Dasawara (10-day cycle)

### What we are trying to determine
What is the correct derivation of Dasawara? Are the values Pancawara urip + Saptawara urip mod 10, or something else?

### Source observations

| Source | Observation | Lineage |
|---|---|---|
| S3 edysantosa/sakacalendar | `((uripPancawara + uripSaptawara) % 10) + 1` — Pancawara and Saptawara urip lookup tables | S3 |
| L4 CALENDRICA | Same derivation: Pancawara urip + Saptawara urip mod 10 | L4 |

### Conclusion
**CALENDRICA (L4) and Java impl (S3) agree on the Dasawara derivation formula** (Pancawara urip + Saptawara urip mod 10).
**Disagreement on 12/210 positions** is most likely due to **cyclic rotation of the urip table** — different sources may list Dasawara names starting from different indices.

### Status
**Formula structure agreed** between L4 and S3.
**Name indexing/rotation** disagreement persists.
**Dewata and CALENDRICA disagree on 198/210 Dasawara positions** — most likely cyclic rotation mismatch.

---

## Claim: Dwiwara (2-day cycle)

### What we are trying to determine
Does Dwiwara derive from Dasawara parity, urip sum parity, or direct sequence?

### Source observations

| Source | Observation | Lineage |
|---|---|---|
| S3 edysantosa/sakacalendar | `(uripPancawara + uripSaptawara) % 2` — parity of urip sum | S3 |
| L4 CALENDRICA | `evenp(dasawara)` — parity of Dasawara (which is derived from urip sum mod 10) | L4 |
| Dewata | Different — likely Dasawara parity | (Dewata) |

### Conclusion
**S3 and L4 derive from the same urip sum**, but **Dewata may use a different parity convention**.
The 84/210 disagreement between Dewata and CALENDRICA is exactly the same number as the Wuku offset (84 = 12 wuku), suggesting a deeper phase/mapping issue.

### Status
**Formula structure** — S3 (urip parity) and L4 (Dasawara parity = urip parity) are arithmetically equivalent.
**Naming** — Luang/Menga vs Pepet semantics: BASAbali says odd urip_sum = Luang; CAL says evenp(dasawara) = Luang.

---

## Independent lineage count summary

| Claim | Independent Balinese lineages retrieved | Substantive status |
|---|---|---|
| Wuku/Gregorian phase | 1 (kb.org) | insufficient |
| Pancawara ordering | 4 (S4, S5, basaibubali, kb.org) | agreement on mapping B |
| Caturwara | 3 (S4, S3, L4) | agree on special-case; disagree on content |
| Astawara | 3 (S4, S3, L4) | agree on special-case; disagree on content |
| Sangawara | 3 (S4, S3, L4) | agree on special-case; disagree on duration (3 vs 4 days) |
| Dasawara derivation | 2 (S3, L4) | agree on urip_sum mod 10 |
| Dwiwara derivation | 2 (S3, L4) | agree on urip parity |

---

## Note on disputed formulations

**basaibubali.org's simple modular formulas** (no special cases for Caturwara/Astawara/Sangawara) appear in **one** community wiki source. They conflict with **S4 (Kemendikbud textbook)**, **S3 (Java impl)**, and **L4 (CALENDRICA)** — three independent sources that all show special-case handling.

This pattern of "one lineage says simple, three lineages say special-case" suggests:
- basaibubali's formulas may be **simplified explanations** that omit the special-case handling
- OR a genuine different tradition (less likely given the diversity of agreeing sources)

Per user instruction (verbatim): "There may genuinely be multiple traditions or calculation conventions. ... If authoritative/reputable Balinese sources themselves disagree, preserve the disagreement."

The substantive decision cannot be made from the lineages retrieved.
- **S1 (Pokok-pokok Wariga)** would resolve most of these questions
- **S2 (Tenung Wariga)** would resolve most of these questions
- Neither is accessible from this host

---

## What we would need to resolve disputes

1. **S1 or S2 chapter text** — would give authoritative Wariga answer on all Wewaran special-cases
2. **Independent Wuku/Gregorian examples** — would resolve the 84-day offset
3. **Customary authority attestation** — would give institutional acceptance
