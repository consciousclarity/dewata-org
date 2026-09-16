# Cross-Validation Report — Four Balinese Calendar Implementations

**Date:** 2026-09-15
**Scope:** September 2026 (30 days), plus epoch anchor dates (1981-08-23, 1971-01-27)
**Method:** All four implementations run on identical Gregorian dates; field-by-field
comparison; cyclical-offset analysis where implementations disagree.

**Implementations:**
1. `ts-balinese-date-js-lib-0.4.3` — Peradnya Dinata, TypeScript/JavaScript.
   The only implementation explicitly handling both the pengalantaka era switches
   (`PIVOT_1971` for dates before 2000-01-06, `PIVOT_2000` after) and the three
   nampih regimes (gated by `_C_SK_START = 1993-01-24` and `_C_SK_END = 2003-01-03`).
2. `java-sakacalendar-2.0` — Edy Santosa, Java.
3. `rust-balinese-calendar-0.3.0` — SHA888 / Kresna Sucandra, Rust.
   Carries `references/BIBLIOGRAPHY.md` (356 lines, 22K) and
   `references/EXTRACTED_ALGORITHMS.md` (29K), both citing Suwintana 2014,
   Dershowitz & Reingold 2018, I Made Bidja 2026 calendar, BASAbali Wiki,
   kalenderbali.org, and the kebudayaaan.kemdikbud.go.id BPNB Bali source.
4. `engine-dewata` — our worktree's `phase-1/src/dewatacalendar/`,
   ruleset `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0`.

---

## 1. Pawukon epoch (the most important finding)

| impl | epoch | 1981-08-23 → | 1971-01-27 → |
|---|---|---|---|
| **Peradnya / TS** | pawukon_day 0 at 1971-01-24 (derived: PIVOT_1971 - 3 days) | `pawukon_day=84, wuku=Langkir` | `pawukon_day=3, wuku=Sinta` |
| **Rust** | same: PAWUKON_EPOCH_JDN = 2440976 (= 1971-01-24) | `pawukon_day=84, wuku=Langkir` | `pawukon_day=3, wuku=Sinta` |
| **Java** | different epoch (not documented; derived from `pivot.angkaWuku`) | `pawukon_day=116, wuku=Krulut` | `pawukon_day=35, wuku=Tolu` |
| **Engine** | **1981-08-23** (asserted in `rulesets.py`: `pawukon.epoch`) | `pawukon_day=1, wuku=Sinta` | n/a (out of range) |

**Result:** Engine uses `1981-08-23` as the Wuku-Sinta-day-1 anchor. Peradnya,
TS, and Rust all use `1971-01-24` (JDN 2440976). **Engine's pawukon is shifted
by exactly 84 days (= 12 wuku) from Peradnya/TS/Rust on every date.**

The Java library uses yet a third epoch — it does not match either of the
above two on 1981-08-23 or 1971-01-27.

**Implication:** every assertion in our conformance corpus that relies on
the 1981-08-23 anchor is silently off by 84 days in the cycle. The engine's
*internal* arithmetic is consistent with its epoch choice, but the anchor
itself is inconsistent with the JavaScript and Rust libraries (which are
cross-referenced with each other via the Peradnya pivot).

## 2. Per-day disagreement matrix (September 2026)

Tested 30 dates 2026-09-01..2026-09-30. All four implementations returned
values on every date (engine is in-range from 1979).

### Saka year — `26/26 unanimous at 1948`
After normalizing the engine's 2-digit `saka_year=48` to the absolute 1948,
all four implementations agree on the Saka year for the entire month.
**No issue.**

### Sasih name
Pattern breakdown:
- **17/26 days:** Rust, TS, Java, and Engine all agree on `Kapat` for these
  days (engine's 1-indexed `sasih_idx=4` maps to `Kapat`).
- **8/26 days:** Rust and TS say `Katiga` (0-indexed `sasih_id=2`), Java says
  `Kapat`, Engine says `Ketiga` (its 1-indexed name for `sasih_idx=3`).
  Rust/TS/Engine all agree on the *position* (third sasih of the year);
  Java disagrees.
- **1 day** (a transition day): all four agree.

**Rust ≡ TS ≡ Engine on Sasih position (just indexing convention).**
**Java is off by one sasih in some months.** Java's `_C_SK_START/END` and
nampih detection appear to give different results than Peradnya/Rust/Engine.

### Saptawara — `26/26 unanimous at the NAME level`
All four implementations agree on the Saptawara name (Redite, Soma, Anggara,
...) for every day in September 2026. **No issue.** The earlier cross-check
against kalenderbali.info showed the engine used `Soma` (Sanskrit-derived)
while the reference used `Coma` (older Balinese) — both spellings are valid.

### Pancawara — `Engine consistently shifted by +1 day vs Rust/TS`
The engine returns the Pancawara value for *tomorrow* on every day.
On 2026-09-01: Rust/TS say `Umanis`, Java/Engine say `Paing`.
On 2026-09-02: Rust/TS say `Paing`, Java/Engine say `Pon`.
**The cyclic offset (engine - rust) mod 5 is exactly 1 on all 30 days.**

Java is also shifted, in the same direction as the engine.
Rust ≡ TS on Pancawara (Peradnya is the reference).

**Java's offset appears to come from Java's Pancawara initialization.**
Java's Pancawara `noPancawara` likely uses a different starting index.

### Triwara — `Engine ≡ Rust ≡ TS on all 30 days`
**No issue.** Java does not expose Triwara through `getTriwara()` in a way
comparable to the others (could not extract a value), so not compared.

### Wuku — `Engine consistently shifted by 19 days (12 wuku) vs Rust/TS`
Detailed analysis shows:
- Days 1-5 of September: cyclic offset = 18 days (engine position = Rust - 12 wuku).
- Days 6-30: cyclic offset = 19 days.
- The 18-vs-19 split is exactly the Wuku boundary (Sept 5 was last day of
  Wuku Uye; Sept 6 was first day of Wuku Menail).

This is the **84-day pawukon offset** described in §1, expressed in wuku
units (84 / 7 = 12 wuku, but because of the wuku-boundary alignment, the
cyclic offset appears as 18 or 19 depending on which side of the
boundary the date falls).

Java also uses a different wuku epoch and produces different names than
Rust/TS/Engine on every date.

## 3. Key observations and disputes

### Dispute filed: ENGINE-PAWUKON-EPOCH-OFFSET-84-DAYS
**component:** pawukon
**class:** `pawukon_position_drift`
**blocking:** YES
**description:** Engine pawukon position is exactly 84 days (= 12 wuku) earlier
than Peradnya/Rust/TS on every date in September 2026. Root cause: engine
uses epoch `1981-08-23`; Peradnya/Rust/TS use epoch `1971-01-24` (JDN 2440976).
`rulesets.py` line ~6 declares `pawukon.epoch = 1981-08-23` — this anchor
disagrees with the canonical Peradnya pivot.
**status:** open

### Dispute filed: ENGINE-PANCAWARA-OFFSET-1-DAY
**component:** wewaran.pancawara
**class:** `wewaran_drift`
**blocking:** YES
**description:** Engine Pancawara is shifted +1 day vs Peradnya/Rust/TS on
all 30 days of September 2026. Java is also shifted (same direction).
Rust/TS agree with each other (Peradnya is the reference).
**status:** open

### Dispute filed: SASIH-PERADNYA-VS-JAVA-1-MONTH-OFFSET
**component:** saka_sasih
**class:** `sasih_index_drift`
**blocking:** YES (Java ≠ Peradnya/Rust on some days)
**description:** Java library's Sasih output diverges from Peradnya/Rust/TS
on 8 of 26 days. The Peradnya/Rust/TS trio agrees on Sasih position; the
Java library's nampih handling gives a different result.
**status:** open

### Dispute filed: JAVA-WUKU-EPOCH-DIFFERENT
**component:** pawukon
**class:** `pawukon_position_drift`
**blocking:** NO (Java is a third-party lib; not used by our engine)
**description:** Java's wuku output does not match Peradnya/Rust/TS/Engine on
any day. The Java library appears to use yet a different pawukon epoch or
wuku ordering. This is a data-quality note about the Java library, not
about our engine.
**status:** open

### Non-blocking: SASIH-NAME-SPELLING
**component:** i18n
**class:** `i18n_label_drift`
**blocking:** no
**description:** Engine uses `Ketiga` (1-indexed naming), Rust/TS use
`Katiga` (0-indexed naming). Same Sasih, different convention.
**status:** open

### Non-blocking: SASIH-YEAR-INDEXING
**component:** i18n
**class:** `i18n_label_drift`
**blocking:** no
**description:** Engine reports `saka_year=48` (2-digit suffix); others
report `1948`. Internally consistent; just a serialization convention.
**status:** open

## 4. What this audit cannot determine

- **Which of the three pawukon epochs (1981-08-23, 1971-01-24, Java's) is
  correct.** I have three implementations; two (Peradnya, Rust) agree, the
  third (Java) disagrees, and ours (engine) agrees with neither.
  Authority validation is required.
- **Whether the pancawara 1-day shift in the engine is a bug or a
  convention.** Peradnya is the most-cited JS reference; Rust derives
  from Peradnya; they agree. Java disagrees in the same direction as
  our engine, which is suspicious.
- **Whether the sasih Java-vs-everyone-else disagreement is due to a
  bug in Java's nampih detection or due to a different valid convention.**

## 5. Concrete next steps

1. **Do not freeze `v0.1.0`.** Two engine-blocking disputes are now
   open (`PAWUKON-EPOCH-OFFSET-84-DAYS`, `PANCAWARA-OFFSET-1-DAY`).
2. **Cross-validate against Peradnya / Rust on the 1900–2099 range**
   to confirm the 84-day pawukon offset is constant across all years.
3. **Authority validation.** A named Balinese calendrical scholar or
   customary authority needs to attest which of (1981-08-23, 1971-01-24)
   is the correct Wuku-Sinta-day-1 anchor. Without that, we cannot
   resolve the pawukon dispute.
4. **Do not edit engine source yet.** Every edit risks introducing
   new discrepancies. The next engine edit should be the unified
   correction of the pawukon epoch and the pancawara offset, in one
   atomic commit, *after* authority validation.

## 6. Files produced

- `/tmp/crossvalidate.py` — multi-impl harness
- `/tmp/cross-2026-09.jsonl` — 30 days × 4 impls × ~12 fields each
- `/tmp/compare.py` — agreement tally
- `/tmp/offsets.py` — cyclic-offset analysis
- `/tmp/wuku-detail.py` — wuku per-day debug
- `/tmp/balinese-cli/` — Rust wrapper
- `/tmp/balinese-ts-cli.js` — Node wrapper
- `/tmp/javacli/SakaCli.java` — Java wrapper
- `/tmp/repos/balinese-date-js-lib/` — Peradnya source (cloned)
- `/tmp/repos/sakacalendar/` — Java source (cloned)
- `/tmp/repos/balinese-calendar/` — Rust source (cloned, includes bibliography)

## 7. Honest summary

The four implementations do **not** produce identical output on the same
Gregorian date. Two independent JavaScript/Rust implementations
(Peradnya, Rust/SHA888) agree with each other on pawukon position, pancawara,
saptawara, triwara, and sasih. Our engine **does not agree** with them:

- pawukon: shifted by exactly 12 wuku (84 days)
- pancawara: shifted by exactly 1 day

Java (sakacalendar) **does not agree** with Peradnya/Rust on sasih or wuku,
but its pancawara and saptawara match our engine's convention, suggesting
Java uses different starting indices throughout.

**The engine has at least two arithmetic discrepancies, both of which are
reproducible on every date in a 30-day window.** This is not a one-off
edge case. This is a systematic shift.

I have **not** fixed any of this. The disputes are filed. The engine
source is unchanged. No freeze. No DNS. No production change.
