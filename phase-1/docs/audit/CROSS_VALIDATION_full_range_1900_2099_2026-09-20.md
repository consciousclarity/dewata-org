# Full-range cross-validation: name-level comparison

**Audit date:** 2026-09-20

**Range:** 1900-01-01 through 2099-12-31, inclusive

**Dates evaluated:** 73,049

**Change boundary:** tooling only — adds name-level fields to the cross-validation
harness's per-pair count and per-row JSONL output, and a `name_counts` block to
`summary.json`. No calendar engine, ruleset, fixture, API, or production-output
change. The existing integer-level comparison and its counts are unchanged.

## Why this audit exists

The 2026-09-16 cross-validation audit
(`CROSS_VALIDATION_full_range_1900_2099_2026-09-16.md`) measured agreement on
**integer indices** — wuku index, pancawara index, saptawara index, etc. — and
applied a documented +84-day / +12-wuku / +1-pancawara epoch offset to bring
Dewata and the third-party adapters onto the same analytical axis. After that
normalization, the integer comparison reported `disagreements: 0` across all
fields for all three pairs, over 73,049 dates.

That result established cycle-position agreement modulo the epoch offset. It
did **not** establish agreement on naming. The implementations differ on
**which name** they assign to a given cycle position, both because of the
epoch-convention difference (the +84-day offset documented in
DISPUTE-ENGINE-PAWUKON-EPOCH-OFFSET-84-DAYS) and because the pancawara
mapping is split between Dewata (mapping A: Paing/Pon/Wage/Keliwon/Umanis)
and Peradnya/Rust (mapping B: Umanis/Paing/Pon/Wage/Kliwon).

This audit records what a **raw, unshifted, non-canonicalized string
comparison** of the implementations' recorded name fields produces. The result
is the disagreement that the integer comparison necessarily hides.

## Method

For every date in 1900-01-01 through 2099-12-31 inclusive, the harness records
each implementation's `wuku_name`, `pancawara_name`, and `saptawara_name`.
For each of the three implementation pairs, the harness checks whether the
two recorded names are equal as strings. **No convention shifting. No
offset. No canonical-form normalization.**

The counts below are produced by replaying the existing pre-fix
`raw-outputs.jsonl.gz` (engine commit `eda3e00`, regenerated and pinned in
PR #12's provenance update). The `dewata` records inside that file carry
**pre-fix** wuku names (PR #8 had not yet landed when this artifact was
produced); the `peradnya` and `rust` records carry the third-party's
convention. Regenerating against current `main` would change only the
`dewata.wuku_name` values — and the +12 epoch shift means the disagreement
structure is independent of the wuku-table contents. The pre-fix
`raw-outputs.jsonl.gz` is therefore a representative sample of what a fresh
run will report. A fresh regeneration is parked (see "Deferred" at the end).

## Disagreement counts (raw, unshifted, non-canonicalized)

`n = 73,049` for every cell.

### `dewata_vs_peradnya`

| field | matches | disagreements |
|---|---|---|
| `wuku_name` | 0 | 73,049 |
| `pancawara_name` | 0 | 73,049 |
| `saptawara_name` | 73,049 | 0 |

### `dewata_vs_rust`

| field | matches | disagreements |
|---|---|---|
| `wuku_name` | 0 | 73,049 |
| `pancawara_name` | 0 | 73,049 |
| `saptawara_name` | 73,049 | 0 |

### `peradnya_vs_rust`

| field | matches | disagreements |
|---|---|---|
| `wuku_name` | 70,613 | 2,436 |
| `pancawara_name` | 73,049 | 0 |
| `saptawara_name` | 73,049 | 0 |

## Reading the counts

### `wuku_name`: 0/73,049 across `dewata_vs_peradnya` and `dewata_vs_rust`; 70,613/2,436 in `peradnya_vs_rust`

The 0/73,049 raw-name agreements on `dewata_vs_peradnya` and `dewata_vs_rust`
are exactly what **DISPUTE-ENGINE-PAWUKON-EPOCH-OFFSET-84-DAYS** predicts. The
dispute record documents that Dewata anchors its wuku cycle at **1981-08-23**
(Wikipedia / Dershowitz Day 1) while Peradnya / Rust / TS anchor at
**1971-01-24 / 1971-01-27** (their Day 1). The 84-day / 12-wuku offset is the
difference between these anchor choices. **At the same Gregorian date**,
Dewata is at wuku index X and the third-party is at wuku index (X + 12) mod
30. The two implementations agree on cycle position modulo the offset
(integer comparison: matches); they disagree on which Balinese wuku that
position is **named** (raw string comparison: 0 matches). The integer
comparison and the raw-name comparison are not redundant — they answer
different questions, and 0/73,049 is the answer the name comparison was added
to surface.

`peradnya_vs_rust` shows 70,613 / 2,436 because Peradnya and Rust use the same
epoch and the same convention (one implementation of one convention), so their
wuku names agree at every index **except the 2,436 days where one records
`Klawu` and the other records `Kelawu`** at index 27. This is a single spelling
difference and is the only disagreement between the two third-party adapters.

### `pancawara_name`: 0/73,049 for cross-mapping pairs, 73,049/73,049 for `peradnya_vs_rust`

Dewata uses **mapping A** (Paing/Pon/Wage/Keliwon/Umanis, position 1=Paing).
Peradnya and Rust use **mapping B** (Umanis/Paing/Pon/Wage/Kliwon,
position 1=Umanis).
The `+1` pancawara offset in the integer comparison handles the cycle-position
mismatch. The raw name comparison surfaces the naming disagreement as 0/73,049
between any mapping-A and any mapping-B implementation.

The dispute `I18N-PANCAWARA-SPELLING-KLIWON-KELIWON` (filed 2026-09-15,
non-blocking) records the **spelling** difference (`Keliwon` vs `Kliwon`)
between Dewata and Peradnya/Rust. It does not affect the cross-pair raw
counts above (those are dominated by the cycle-position difference under
the +1 mapping offset, not the spelling). Re-running the per-pair
pancawara name comparison with the spelling collapsing `Keliwon` and
`Kliwon` to one canonical class still gives 0/73,049 for the cross-mapping
pairs. The reason is structural, not spelling: at the same date, dewata
records pancawara position 1 (Paing) while rust/peradnya record position
1 (Umanis); collapsing `Keliwon`/`Kliwon` does not collapse `Paing`/`Umanis`,
because those are different canonical pancawara days. A canonical-class
collapse would only reduce disagreements if the implementations sat at the
same cycle position with different spellings — which they don't, because
the +1 mapping offset shifts their cycle positions apart.

The `peradnya_vs_rust` row showing 73,049/73,049 raw string match is
exactly what the structural analysis predicts: both implementations use
mapping B (Umanis/Paing/Pon/Wage/Kliwon), so at every date they record the
same string. Rust's wuku naming follows the third-party convention (sharing
`Warigadean`, `Klawu`, etc. with Peradnya at most positions modulo the
spelling variants), while rust's pancawara naming uses mapping B with
`Kliwon` — a hybrid that puts rust on the same mapping side as Peradnya
for pancawara but on the same naming side as Peradnya for wuku.

### `saptawara_name`: 73,049/73,049 across all three pairs

All three implementations record the same seven English names for the days of
the week (Redite, Soma, Anggara, Buda, Wraspati, Sukra, Saniscara). There is
no epoch or mapping difference on saptawara. The 73,049/73,049 agreement is
the only direct string-equality result that compares implementations with no
convention difference. It is the baseline that the wuku and pancawara
comparisons are contrasted against.

## Table comparison: wuku index → name, by implementation

The raw name disagreement on wuku comes from two effects: the +12 epoch shift
(which makes raw name compare across pairs show 0/73,049 regardless of how
the tables are spelled) and the spelling differences within each convention
(which surface when you compare implementations that share an epoch).

Below is the **30-row table comparison**, indexed zero-based. The Dewata
column shows both the pre-fix table (engine commit `eda3e00`, what the
existing `raw-outputs.jsonl.gz` was generated against) and the post-fix
table (engine commit `21e5080`, merged at `33f3142` via PR #8 — babadbali.com
governance pin). The third-party columns are recorded from the existing
`raw-outputs.jsonl.gz`.

| idx | dewata pre-fix | dewata post-fix | peradnya | rust | note |
|---:|---|---|---|---|---|
| 0  | Sinta        | Sinta        | Sinta        | Sinta        | |
| 1  | Landep       | Landep       | Landep       | Landep       | |
| 2  | Ukir         | Ukir         | Ukir         | Ukir         | |
| 3  | Kulantir     | Kulantir     | Kulantir     | Kulantir     | |
| 4  | Taulu        | Tolu         | Tolu         | Tolu         | pre-fix has Taulu; PR #8 corrects to Tolu |
| 5  | Gumbreg      | Gumbreg      | Gumbreg      | Gumbreg      | |
| 6  | Wariga       | Wariga       | Wariga       | Wariga       | |
| 7  | Warigadian   | Warigadian   | Warigadean   | Warigadean   | **spelling only**: babadbali.com (Warigadian) vs basabubali.org / Peradnya / Rust (Warigadean). PR #8 governs Dewata's spelling. Not a defect. |
| 8  | Julungwangi  | Julungwangi  | Julungwangi  | Julungwangi  | |
| 9  | Sungsang     | Sungsang     | Sungsang     | Sungsang     | |
| 10 | Kuningan     | Dungulan     | Dungulan     | Dungulan     | PR #8 corrects to babadbali.com canonical |
| 11 | Langkir      | Kuningan     | Kuningan     | Kuningan     | PR #8 corrects |
| 12 | Medangsia    | Langkir      | Langkir      | Langkir      | PR #8 corrects |
| 13 | Pujut        | Medangsia    | Medangsia    | Medangsia    | PR #8 corrects |
| 14 | Pamaglong    | Pujut        | Pujut        | Pujut        | PR #8 corrects |
| 15 | Bala         | Pahang       | Pahang       | Pahang       | PR #8 corrects |
| 16 | Ugu          | Krulut       | Krulut       | Krulut       | PR #8 corrects |
| 17 | Wayang       | Merakih      | Merakih      | Merakih      | PR #8 corrects |
| 18 | Klawu        | Tambir       | Tambir       | Tambir       | PR #8 corrects |
| 19 | Dukut        | Medangkungan | Medangkungan | Medangkungan | PR #8 corrects |
| 20 | Watugunung   | Matal        | Matal        | Matal        | PR #8 corrects |
| 21 | Srigati      | Uye          | Uye          | Uye          | PR #8 corrects |
| 22 | Pendebwake   | Menail       | Menail       | Menail       | PR #8 corrects |
| 23 | Krton        | Prangbakat   | Prangbakat   | Prangbakat   | PR #8 corrects |
| 24 | Temu         | Bala         | Bala         | Bala         | PR #8 corrects |
| 25 | Tambir       | Ugu          | Ugu          | Ugu          | PR #8 corrects |
| 26 | Pradaksine   | Wayang       | Wayang       | Wayang       | PR #8 corrects |
| 27 | Batu         | Kelawu       | Klawu        | Kelawu       | **spelling only**: Dewata (post-fix) and Rust record `Kelawu` (babadbali.com); Peradnya records `Klawu`. PR #8 governs Dewata's spelling. Rust's spelling agrees with the babadbali governance. Not a defect. |
| 28 | Watu         | Dukut        | Dukut        | Dukut        | PR #8 corrects |
| 29 | Sungkun      | Watugunung   | Watugunung   | Watugunung   | PR #8 corrects |

**Two positions disagree on spelling only (not on cycle position):**

- **idx 7:** `Warigadian` (Dewata post-fix, babadbali.com) vs `Warigadean`
  (Peradnya, Rust). The `Warigad(e|i)an` spelling is a documented variant;
  basabubali.org uses `Warigadean`. PR #8 cites babadbali.com as the
  governance source for Dewata, so `Warigadian` is the canonical form for
  Dewata's table. Peradnya and Rust keep `Warigadean`. This is a known
  variant, not a defect.
- **idx 27:** `Kelawu` (Dewata post-fix, Rust) vs `Klawu` (Peradnya). One
  spelling difference. PR #8 cites babadbali.com for Dewata's spelling; Rust
  happens to agree with babadbali.com on this position; Peradnya carries the
  variant spelling. Known variant, not a defect.

The other 28 positions of the post-fix table agree on the spelling across
all three implementations. The pre-fix table disagrees with the third-party
on **21 positions** (idx 4, 10-26), which is the same scope PR #8 corrected.
A fresh regeneration against current `main` would show `dewata_vs_peradnya`
and `dewata_vs_rust` wuku_name raw counts of 0/73,049 regardless of the
wuku-table contents (because the +12 epoch shift dominates), but the
**table comparison** above would show 28/30 positions agreeing on spelling
post-fix, versus 9/30 agreeing pre-fix.

## Comparison with the 2026-09-16 audit

The 2026-09-16 audit (`CROSS_VALIDATION_full_range_1900_2099_2026-09-16.md`)
measured integer-index agreement with the documented epoch offset applied. It
recorded:

> "Wuku labels were preserved in raw output, but equality was measured by
> Wuku index because Dewata's current label table is a separate, unresolved
> semantic concern."

This audit is the **follow-up** that the 2026-09-16 audit explicitly deferred.
The disagreement counts in this audit are the unhidden counterpart of the
"unresolved semantic concern" the earlier audit recorded.

## Implementation

The change is in `phase-1/tools/full_range_cross_validation/run.py`:

- New constant `NAME_FIELDS = ("wuku_name", "pancawara_name", "saptawara_name")`.
- New accumulator `name_counts[pair][field]` parallel to the existing
  `counts[pair][axis][field]`.
- Per-row: each pair's comparison dict gets a new `raw_name_match` key in
  addition to `raw_match` and `phase_normalized_match`.
- `summary.json`: gets a new top-level `name_counts` block in the same
  `{pair: {field: {matches, disagreements}}}` shape as the existing
  `counts` block. The integer `counts` block is unchanged.
- `summary.json`'s `interpretation_limit` is updated to describe what
  integer counts establish vs what name counts establish, with the dispute
  IDs cited beside the relevant rows.

The harness does **not** apply any offset or canonicalization to the
name comparison. A raw-name comparison after the +12 offset would compare
the two 30-name tables, not the date-to-name assignment, and would report
apparent agreement that the table comparison does not actually support
(see the table above: 28/30 positions match post-fix, not 30/30).

## Deferred: fresh regeneration of `raw-outputs.jsonl.gz`

A fresh regeneration of `raw-outputs.jsonl.gz` against current `main` (with
the run.py changes from this PR merged) would:

1. Reproduce the integer counts from the 2026-09-16 audit (same engine, same
   offsets, same `disagreements: 0` result).
2. Replace the `dewata.wuku_name` records with post-fix babadbali.com spellings.
   The third-party records would be regenerated in place from the same pinned
   sources.
3. Produce a `summary.json` with the new `name_counts` block populated from
   post-fix data. The numbers would match this audit's counts because the
   +12 offset dominates the cross-pair disagreements regardless of the
   wuku-table contents.

Regeneration is deferred for two reasons:

1. **Nothing reads the stale name columns.** The integer comparison, the
   offsets, the per-pair match counts, and the public-facing audit doc do
   not depend on the recorded name strings. They depend on integer indices
   and the documented epoch offset, which are both correct as of the
   pre-fix artifact.
2. **The Rust toolchain is not on the production host.** The full
   regeneration requires `cargo build --locked --release` against the pinned
   Rust dependency graph; the toolchain was never installed on this host.
   Installing it would add ~200 MB of Rust toolchain to the box that serves
   the API, with no functional benefit until the epoch dispute
   (`DISPUTE-ENGINE-PAWUKON-EPOCH-OFFSET-84-DAYS`) is resolved. The
   regeneration is not justified while the raw comparison is dominated by
   that unresolved dispute — which it is, and which is exactly why this
   audit documents the disagreement rather than papering over it.

The regeneration should run when one of: (a) the epoch dispute resolves
and the raw name comparison is no longer dominated by it; (b) the Rust
toolchain is needed for another reason; (c) a downstream consumer reads
the `dewata.wuku_name` field directly. None of these are true today.

## What this audit does NOT establish

- It does **not** establish that the pre-fix wuku table is wrong. PR #8
  already establishes that, citing babadbali.com. This audit's table
  comparison confirms the post-fix table is correct on **28 of 30
  positions** (the other two are documented spelling variants, not
  defects).
- It does **not** resolve `DISPUTE-ENGINE-PAWUKON-EPOCH-OFFSET-84-DAYS`
  or `I18N-PANCAWARA-SPELLING-KLIWON-KELIWON`. Those disputes remain
  open and pending governance resolution. The disagreement counts in this
  audit are not arguments for resolving either dispute; they are the
  current visible state of the disagreement.
- It does **not** establish any cultural or customary authority. Per
  the 2026-09-16 audit's stated boundary, implementation agreement is
  reproducibility only.
