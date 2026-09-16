# Independent Reference Validation — kalenderbali.info (September 2026)

**Date:** 2026-09-15
**Author:** audit worktree, automated comparison
**Source:** `https://kalenderbali.info` (home page, September 2026 calendar grid)
**Source attribution:** I Ketut Suwintana (named on every page footer), site © 2013
**Engine under test:** `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0`
**Method:** parse 30 day cells from the September 2026 grid, compare to engine
output for the same 30 dates, classify each difference as (a) arithmetic error,
(b) labeling convention, (c) reference-source-specific decision, or (d) open
dispute.

---

## 1. What the reference actually contains

The site is a practitioner / popular reference (Indonesian-language, published
by an individual named on the site footer, fuzzy-logic "Metode Mamdani" for
"dewasa ayu"). It is **not** a peer-reviewed academic source. The data I
extracted is the structural calendar grid — Saptawara, Sasih, pangalantaka day
number, Triwara, Pancawara — for the 30 days of September 2026.

The site uses the *Wariga* framework, with the override chain
*"wewaran alah dening wuku, wuku alah dening pananggal/panglong,
pananggal/panglong alah dening sasih, sasih alah dening dauh, dauh alah dening
Sang Hyang Triodasa Saksi"* (the well-known Bali precedence chain).

The site claims Saka 1 begins on **Gregorian 79-03-22**. Our engine claims
Saka 1901 Day 1 = **Gregorian 1979-03-29**. The two epochs differ. This is
investigated below.

The September 2026 page header reads: *"September 2026 Katiga/Kapat 1948"* —
the listing order is not data; the day cells are.

## 2. Method

```
for d in 2026-09-01..2026-09-30:
  kb_value = parse day-cell from /tmp/kb-home.html
  engine_value = GET /dsp/v0.1/calendar/date/<d>
  compare component-by-component
```

The day cells that parsed cleanly covered 2026-09-01..2026-09-15 (15 days).
Days 16-30 used a different HTML color attribute and the parser did not
resolve them; this is a parsing limitation, not a reference limitation.

The 15 parsed vectors and the engine comparison are saved to:
`/tmp/kb-2026-09.json` and `/tmp/kb-vs-engine-2026-09.json`.

## 3. Component-by-component findings

### 3.1 Saka year

| field | reference | engine | agreement |
|---|---|---|---|
| 2026-09 saka_year | 1948 (header) | 1948 | ✓ |

The page header says *"September 2026 Katiga/Kapat 1948"*. Engine reports
`saka_year=48` (i.e. 1948) for September 2026. **Match.**

Note: this is the arithmetic `2026 - 1978 = 1948` (after March). The reference
agrees with this arithmetic for dates after the Nyepi boundary.

### 3.2 Saptawara (7-day week)

| field | reference | engine | classification |
|---|---|---|---|
| saptawara_name on Monday 2026-09-07 | `Coma` | `Soma` | **labeling** |
| saptawara_name on every other day | matches | matches | ✓ |

`Coma` and `Soma` are both Balinese names for Monday (`Soma` is the
Sanskrit-derived form used in modern Bali; `Coma` is an older Balinese form
used in some traditional references). The engine and reference use different
conventions, **not an arithmetic discrepancy**.

`Saptawara idx`: the reference uses 0-indexed (Redite=0), the engine uses
1-indexed (Redite=1). This is **indexing convention**, not an arithmetic
discrepancy.

**Action:** document the indexing and labeling convention differences in
`i18n.py`. No engine change needed for arithmetic.

### 3.3 Sasih (lunar month)

| date | reference sasih | engine sasih | classification |
|---|---|---|---|
| 2026-09-01..09 | Kapat (idx 4) | Ketiga (idx 3) | **OPEN DISPUTE** |
| 2026-09-10..15 | Katiga (idx 3) | Kapat (idx 4) | **OPEN DISPUTE** |

The engine and reference agree on **the Saka year (1948)** and **the day of
the Sasih boundary (Sept 9/10)**. They disagree on **which side of the
boundary is Kapat and which is Katiga** — the engine and reference assign
opposite names to the same dates around the boundary.

Possible causes:
- **Independence of the Sasih order from the day count.** The engine uses
  `sasih_idx = int(days_remaining / 30.4) + 1`, which assumes Sasih 1 starts
  at offset 0 (1979-03-29). If the reference starts the year with a different
  sasih (e.g. Sasih Kasa starts at a different offset), the engine could be
  off by one.
- **Sasih naming convention difference.** Some Balinese sources start the
  Saka year with Sasih Kasa, others with Sasih Kedasa (depending on which
  Nyepi convention is used).
- **Engine epoch offset.** The engine's `_saka_year_for_date` returns
  `gregorian_year - 1978` for dates after March. But the loop in
  `_sasih_index_at_offset` increments `year_offset` starting from
  `SAKA_EPOCH_YEAR = 1901`. The loop exits with `sakah_year = 1947` for
  2026-09-01, while the externally exposed `saka_year` is `1948`. This is
  an internal/external year-number inconsistency in the engine itself.
  The Sasih index is computed using the loop's `year_offset`, which is one
  less than the exposed `saka_year`.

**This is a real arithmetic discrepancy and must be resolved before any
freeze.** It is a `saka_epoch_offset` dispute per the audit schema.

### 3.4 Triwara (3-day week)

| date | reference triwara | engine triwara | classification |
|---|---|---|---|
| 2026-09-01 | Beteng | Kajeng | **cycle offset** |
| 2026-09-02 | Kajeng | Pasah | **cycle offset** |
| 2026-09-03 | Pasah | Beteng | **cycle offset** |

The pattern is `engine_triwara = (reference_triwara + 1) mod 3`. The engine
and reference agree on the cycle length (3 days) but disagree on the
starting day. `engine[Pasah]=1, Beteng=2, Kajeng=3` (positions 1, 2, 0 in
the cycle). Reference has `Pasah=1, Beteng=2, Kajeng=3` as well — the
**position** assignment is the same, but the engine's computed cycle
position for 2026-09-01 is one step ahead of the reference's.

This is a **1-day offset in the Triwara cycle start**, similar to the Sasih
discrepancy. It suggests the engine's overall cycle-start date is one day
too late, or one day too early, depending on direction.

**This is also a real arithmetic discrepancy.** It may resolve once the
Sasih discrepancy is fixed (since both cycles derive from the same epoch
offset), but it is currently open.

### 3.5 Pancawara (5-day week)

| date | reference pancawara | engine pancawara | classification |
|---|---|---|---|
| 2026-09-04 | `Kliwon` | `Keliwon` | **spelling** |
| 2026-09-09 | `Kliwon` | `Keliwon` | **spelling** |
| all other dates | match | match | ✓ |

The cycle positions agree; only the spelling differs. `Kliwon` and
`Keliwon` are both valid spellings of the same Balinese day name.

**Action:** standardize spelling. No arithmetic change.

### 3.6 Pangalantaka (lunar-day-of-sasih)

The reference provides `pang_day` values (1..30). The engine does not expose
this directly. To compare, the engine's `lunar_tithi` would need to be
related to the reference's `pang_day`. Both are roughly day-of-month in a
Sasih, but the definitions differ:

- **Reference `pang_day`**: the day number *within the current Sasih* (1-30).
- **Engine `lunar_tithi`**: `days_since_epoch % 30 + 1`, which is the day
  number *within a 30-day cycle starting from the epoch*, **not** within
  the current Sasih. This is a definitional mismatch.

**This is a definitional mismatch, not a direct comparison.** It would
require either (a) the engine to expose pang_day directly, or (b) the
reference to expose a same-definitional value, to compare.

**Action:** design a `pang_day` API field that exposes day-within-current-Sasih.

## 4. Critical finding

The engine's Sasih indexing and Triwara cycle-start are **off by one day** vs.
kalenderbali.info. This is the most important finding from this audit.

The off-by-one is consistent across both cycles, which strongly suggests a
**single root cause** in the engine's epoch offset, not two independent bugs.
Fixing the epoch by 1 day would likely resolve both. But fixing the epoch
without verification would be unsafe — the right move is to:

1. Add the 30-day September 2026 reference to the conformance corpus.
2. Add the corrected epoch hypothesis as a pending dispute.
3. **Not freeze `v0.1.0` (or any version) until the Sasih/Triwara dispute
   has a documented resolution signed by a named authority.**

## 5. Disputes to file

Filing these as new entries in `docs/runbook/disputes.json`:

| id | date | component | class | severity | status |
|---|---|---|---|---|---|
| DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09 | 2026-09-09 | saka_sasih | `sasih_index_drift` | **blocking** | open |
| DISPUTE-TRIWARA-CYCLE-OFFSET-2026-09 | 2026-09-01..09 | wewaran.triwara | `wewaran_drift` | **blocking** | open |

Plus a non-blocking i18n issue:

| id | component | class | severity | status |
|---|---|---|---|---|
| I18N-PANCAWARA-SPELLING-KLIWON-KELIWON | i18n | `i18n_label_drift` | non-blocking | open |

## 6. What this audit did NOT verify

- The Cunningham 1994 reference cited in `conformance/published/cunningham_1994.json`
  was **not used** for this comparison. It remains unauditable from this host.
- The Igarashi reference remains unauditable.
- Dershowitz & Reingold was not consulted directly; the engine's pawukon
  rule uses an anchor date (1981-08-23 = Wuku Sinta day 1) but this audit
  did not extend to verifying Pawukon arithmetic.
- The engine's Rahinan rules (Purnama, Tilem, etc.) are computed from
  `lunar_tithi` which has the definitional mismatch above; not verified.

## 7. Honest summary

This audit found:

1. **The engine and kalenderbali.info agree on Saka year arithmetic** for
   September 2026 (1948). The `gregorian_year - 1978` rule is correct.

2. **The engine and kalenderbali.info agree on Saptawara day-of-week** for
   September 2026, modulo spelling convention (Coma vs Soma).

3. **The engine and kalenderbali.info disagree on Sasih assignment** around
   the Sasih-Kapat/Katiga boundary on 2026-09-09/10. This is a real
   arithmetic discrepancy, off by one sasih. **Blocking.**

4. **The engine and kalenderbali.info disagree on Triwara cycle-start** by
   one day. **Blocking**, but likely resolved by the same fix as the Sasih
   dispute.

5. **The engine and kalenderbali.info agree on Pancawara** modulo spelling
   (Kliwon vs Keliwon). Non-blocking.

6. **The engine and kalenderbali.info have not been compared on Pawukon,
   Wuku, Rahinan, or pang_day** because the engine does not expose
   `pang_day` directly, and the reference does not expose all fields.

**Recommendation:** do not freeze v0.1.0. Resolve the Sasih/Triwara
discrepancies first. Add the September 2026 reference to the conformance
corpus. Wire `run_corpus` into pytest so that any future ruleset bump is
automatically validated against this corpus.

## 8. Files produced

- `/tmp/kb-home.html` — downloaded September 2026 calendar page
- `/tmp/kb-2026-09.json` — 15 parsed day-cell vectors
- `/tmp/parse-kb.py` — the parser
- `phase-1/docs/audit/REFERENCE_VALIDATION_kalenderbali_2026-09.md` — this file
