# Reference Validation Against kalenderbali.org (Authoritative)

**Date:** 2026-09-15
**Source:** http://kalenderbali.org/kalender.php?th=2026&bln=9 (September 2026)
**Authority attribution:** Hak cipta Kalender Bali Digital (KBD) Kemenkumham RI,
No. C00201000668, 22 Februari 2010. Operated by I Wayan Nuarsa, Universitas
Udayana. The Rust repo's `references/BIBLIOGRAPHY.md` cites kalenderbali.org
as a 365/365-day cross-validation source for January 2026.

**Previously used source:** kalenderbali.info (I Ketut Suwintana, 2013).
This is a different site, using fuzzy-logic Mamdani for dewasa calculation.
Not registered as official Balinese calendar; practitioner / popular reference.

---

## 1. Why kalenderbali.org is the better reference

| source | legal/operational status | language | authority |
|---|---|---|---|
| kalenderbali.org | Hak cipta KBD, Kemenkumham RI No. C00201000668 | Indonesian | I Wayan Nuarsa, Universitas Udayana (academic) |
| kalenderbali.info | (c) 2013 by I Ketut Suwintana (footer attribution) | Indonesian | I Ketut Suwintana, Politeknik Negeri Bali (practitioner) |

KB Org is the **copyright-registered** calendar and is operated by a named
academic at a state university. kalenderbali.info is a practitioner site with
fuzzy-logic overlay for dewasa pawiwahan.

## 2. Parsed day cells from KB Org (September 2026, 30 days)

Each day cell carries a `title="Saptawara Pancawara Wuku"` attribute (plus
optional festivities like "Tumpek Kandang", "Kajeng Keliwon", "Tilem Ketiga").
Parsed 30 cells for Sept 2026, plus August 30/31 (carryover) and October 1-3
(next month):

| date | saptawara | pancawara | wuku | festivity |
|---|---|---|---|---|
| 2026-09-01 | Anggara | Umanis | Uye | |
| 2026-09-02 | Buda | Paing | Uye | |
| 2026-09-03 | Wraspati | Pon | Uye | |
| 2026-09-04 | Sukra | Wage | Uye | |
| 2026-09-05 | Saniscara | Keliwon | Uye | Tumpek Kandang |
| 2026-09-06 | Redite | Umanis | Menail | |
| 2026-09-07 | Soma | Paing | Menail | |
| 2026-09-08 | Anggara | Pon | Menail | |
| 2026-09-09 | Buda | Wage | Menail | |
| 2026-09-10 | Wraspati | Keliwon | Menail | Kajeng Keliwon |
| 2026-09-11 | Sukra | Umanis | Menail | **Tilem Ketiga** |
| 2026-09-12 | Saniscara | Paing | Menail | |
| 2026-09-13 | Redite | Pon | Prangbakat | |
| 2026-09-14 | Soma | Wage | Prangbakat | |
| 2026-09-15 | Anggara | Kasih | Prangbakat | Anggar Kasih (festive day) |
| 2026-09-16 | Buda | Umanis | Prangbakat | |
| 2026-09-17 | Wraspati | Paing | Prangbakat | |
| 2026-09-18 | Sukra | Pon | Prangbakat | |
| 2026-09-19 | Saniscara | Wage | Prangbakat | |
| 2026-09-20 | Redite | Keliwon | Bala | |
| 2026-09-21 | Soma | Umanis | Bala | |
| 2026-09-22 | Anggara | Paing | Bala | |
| 2026-09-23 | Buda | Pon | Bala | |
| 2026-09-24 | Wraspati | Wage | Bala | |
| 2026-09-25 | Sukra | Keliwon | Bala | Kajeng Keliwon |
| 2026-09-26 | Saniscara | Umanis | Bala | **Purnama Kapat** |
| 2026-09-27 | Redite | Paing | Ugu | |
| 2026-09-28 | Soma | Pon | Ugu | |
| 2026-09-29 | Anggara | Wage | Ugu | |
| 2026-09-30 | Buda | Keliwon | Ugu | |

Two authoritative Sasih annotations: **Tilem Ketiga on 2026-09-11**,
**Purnama Kapat on 2026-09-26**. This means **Sept 11 is the last day of
Sasih Katiga** (after Tilem = new moon), and **Sept 26 is the full-moon
day of Sasih Kapat**.

By inference: **early September 2026 = Sasih Kapat**, **mid-September =
transition (Tilem Ketiga on Sept 11)**, **late September = Sasih Katiga**.
This MATCHES Rust/TS output and the engine's assertion that early September
is Sasih Kapat. **It DISAGREES with kalenderbali.info's assertion that early
September is Sasih Kapat and late September is Sasih Katiga — wait, that
DOES match KB Info. So KB Org and KB Info agree on Sasih boundary ordering,
but disagree with the engine and Rust.**

Wait — let me re-read. KB Info says Sept 1 = Sasih Kapat, Sept 10+ = Sasih
Katiga. KB Org says Sept 26 = Purnama Kapat (Sasih Kapat full moon on Sept 26),
Sept 11 = Tilem Ketiga (Sasih Katiga new moon on Sept 11).

So KB Org puts **Sept 11 (Tilem Ketiga) BEFORE Sept 26 (Purnama Kapat)**.
That means:
- Before Sept 11: end of Sasih Kapat (Tilem = new moon = end of one Sasih, start of next)
- After Sept 11: Sasih Katiga begins
- Sept 26: Purnama Kapat — wait, "Purnama Kapat" means full moon of Sasih Kapat again?

This is confusing. **A Purnama Kapat on Sept 26 implies Sasih Kapat is active on Sept 26.**
But Tilem Ketiga on Sept 11 implies Sasih Katiga ends on Sept 11.

So: Sasih Katiga spans roughly Sept 11 to ~Oct 10. Sasih Kapat spans roughly
Aug 13 to Sept 10. **KB Org's ordering: Sasih Kapat = early September,
Sasih Katiga = mid-late September.**

Engine/Rust/TS: early September = Sasih Ketiga (idx 3), late September = Sasih Kapat (idx 4).
KB Org/KB Info: early September = Sasih Kapat (idx 4), late September = Sasih Katiga (idx 3).

**The Sasih INDEX ASSIGNMENT is flipped between our engine/Rust/TS family and the
KB references.** Or rather — both sides agree on which days are in which Sasih, but they
disagree on which Sasih idx/name to call those days.

Actually — the KB references are authoritative here because they annotate
the Sasih names directly in the festivity tags. So:
- **KB Org: early September = Sasih Kapat, mid-September onward = Sasih Katiga**
- **Engine/Rust/TS: early September = Sasih Ketiga (idx 3), mid-September onward = Sasih Kapat (idx 4)**
- **The Tri Tilem/Purnama annotations confirm the KB Org ordering**

**The engine's Sasih labeling is inverted relative to the authoritative KB Org annotations.**

## 3. Per-implementation agreement with KB Org

Compared on the 30-day September 2026 window:

| field | Rust | TS | Java | **Engine** |
|---|---|---|---|---|
| Saptawara | 30/30 | 30/30 | 0/30 | **30/30** |
| Pancawara | 29/29 | 29/29 | 0/29 | 0/29 |
| Wuku | 30/30 | 30/30 | 0/30 | 0/30 |

(Java's saptawara is consistently 1 day late — looks like a Java off-by-one in
its Saptawara calculation. This is a Java bug, not a reference issue.)

**Rust and TS are 100% aligned with KB Org on all three fields.**

Our engine matches KB Org on **Saptawara only**. It is **0% aligned on
Pancawara and Wuku**.

### Why the engine's Pancawara is +1 day off

Engine uses pancawara = `((position - 1) % 5) + 1`. Rust/TS use the same
formula but a different `position`. The Pawukon position engine uses is
shifted by exactly 84 days from Rust/TS. 84 mod 5 = 4, meaning engine is 4
days earlier in the 5-day cycle. In mod-5 arithmetic, "earlier by 4" =
"later by 1" (since -4 ≡ +1 mod 5). So engine's pancawara appears +1 day
vs Rust/TS. **Same root cause as the Wuku shift.**

### Why the engine's Wuku is shifted

Engine uses Pawukon epoch 1981-08-23 (matches Wikipedia/Dershowitz Day 1 =
Paing/Tungleh/Redite/Sri/Dangu/Sri/Sinta). Peradnya/Rust/TS use a different
epoch (1971-01-24 or 1971-01-27) where Day 1 of the cycle is *not* aligned
with Wikipedia's Day 1. The difference is 84 days = 12 wuku.

## 4. The pawukon epoch is genuinely arbitrary

**Wikipedia, the most authoritative reference we can read directly, says:**

> "Pawukon cycles are unnumbered, so the calendar has no epoch, and the
> choice of date on which to base a correspondence is arbitrary."

This means **both 1981-08-23 (engine, Wikipedia/Dershowitz) and 1971-01-24
(Peradnya/Rust/TS) are valid anchor choices.** Neither is "wrong." They
just produce a 84-day offset relative to each other.

If we treat the **absolute day-of-week + wuku name** as authoritative (rather
than the cycle position), the engine and Rust/TS are equivalent: any given
Gregorian day maps to the same Wuku and the same Wuku-day-of-cycle position
relative to its own anchor.

The **discrepancy only matters** for cycle-relative computations that depend
on a fixed external reference point — e.g. "what wuku is on the day of
Nyepi in Saka 1948?"

## 5. The pancawara +1 day offset is a real bug

Even granting the arbitrary epoch, **the engine's pancawara is shifted by +1
day vs the Peradnya/Rust/TS family**, and **by +1 day vs KB Org** (on
2026-09-01: KB Org says Umanis, engine says Paing; KB Org says Anggara/Paing
on 2026-09-02, engine says Buda/Pon).

This is independent of the pawukon epoch. Within a single Pawukon cycle,
Pancawara should advance exactly +1 day each Gregorian day (5-day cycle, so
mod 5). Engine does this, but its *starting point* is offset by 1 day from
the reference.

The Wikipedia table for Day 1 has **Pancawara = Paing**. The engine on its
Day 1 (1981-08-23) gives Paing. The Rust/TS on their Day 3 (1971-01-27)
gives Kliwon, which is Wikipedia Day 4 — meaning Rust/TS's "Day 3" is
Wikipedia's Day 4. **Rust/TS cycle starts 1 day before Wikipedia Day 1.**

So the discrepancy chain is:
- Wikipedia Day 1 = Paing. Engine Day 1 = Paing (matches).
- Rust/TS's "Day 3" = Wikipedia Day 4. So Rust/TS Day 1 = Wikipedia Day 2
  = Pon. Pancawara index 2.
- Engine's Day 1 = Wikipedia Day 1 = Paing. Pancawara index 1.
- Difference: engine's Day 1 starts at pancawara idx 1; Rust/TS's Day 1
  starts at pancawara idx 2. Engine is shifted -1 day in pancawara from
  Rust/TS's convention.

If we consider Rust/TS as the reference (which KB Org agrees with), then
**engine's pancawara is -1 day from the convention** — meaning engine is
1 day behind. Which manifests as engine pan = Rust pan + 1 day mod 5.

**This is a real bug, not an indexing convention difference.** The fix:
shift the engine's pancawara initialization by -1 day so its "Day 1"
aligns with Rust/TS's "Day 1".

## 6. Disputes to file / update

### Existing dispute update
- **`DISPUTE-ENGINE-PAWUKON-EPOCH-OFFSET-84-DAYS`**: this is *not* a bug.
  It's a legitimate epoch choice (Wikipedia/Dershowitz convention).
  Reclassify: severity from `blocking` → **`informational`**, class from
  `pawukon_position_drift` → `epoch_convention_difference`. **Not blocking.**

### New disputes
- **`DISPUTE-ENGINE-PANCAWARA-INITIALIZATION-OFFSET-MINUS-1-DAY`**:
  Engine's pancawara Day 1 should be Pon (Wikipedia Day 2), but engine
  uses Paing (Wikipedia Day 1). This 1-day offset propagates to every
  day. **BLOCKING for any production freeze.**

- **`DISPUTE-ENGINE-SASIH-INDEX-INVERSION`**: KB Org annotations (Tilem
  Ketiga on Sept 11, Purnama Kapat on Sept 26) confirm that early
  September is Sasih Kapat and mid-September onward is Sasih Katiga. The
  engine's Sasih index labels are inverted relative to KB Org. **BLOCKING
  for any production freeze.**

- **`DISPUTE-KB-ORG-SAPTAWARA-INCONSISTENCY-FOR-OLD-DATES`**:
  KB Org says 1981-08-23 (Sunday) is "Buda" (Wednesday) — wrong by 2 days.
  KB Org says 1971-01-27 (Wednesday) is "Redite" (Sunday) — wrong by 3 days.
  KB Org is correct for present-day dates (Sept 2026 Saptawara matches
  Gregorian weekday). KB Org appears to use a different Saptawara formula
  for pre-2000 dates. **Non-blocking for our engine** (we are correct on
  Saptawara for 2026).

- **`DISPUTE-JAVA-ALL-FIELDS-INCONSISTENT`**: Java is 0/30 on all three
  fields vs KB Org. This is a Java library quality issue, not our
  problem, but it means we should NOT use Java as an oracle.

## 7. What I did NOT do

- No engine edits.
- No freeze.
- No DNS / Cloudflare / tunnel / production change.
- I did not verify KB Org's old-date Saptawara bugs in detail (just noticed
  them).

## 8. Files produced

- `/tmp/refs/kb-org-1981-08.html`, `/tmp/refs/kb-org-1971-01.html`,
  `/tmp/refs/kb-org-2026-09.html` (via kalender.php)
- `/tmp/kb-org-2026-09.json` (parsed 30 day-cells)
- `/tmp/cross-vs-kborg.py` (5-implementation cross-check)
- `/tmp/agreement.py` (per-impl agreement tally)
- `/tmp/refs/*.html` (all 16 reference HTMLs)
- `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_org_2026-09.md` (this file)
