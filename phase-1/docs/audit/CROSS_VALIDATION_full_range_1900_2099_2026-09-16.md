# Full-range Pawukon/Wewaran cross-validation audit

**Audit date:** 2026-09-16

**Range:** 1900-01-01 through 2099-12-31, inclusive

**Dates evaluated:** 73,049

**Change boundary:** evidence and tooling only; no calendar engine, ruleset,
version, fixture, API, or production-output change

## Implementations and provenance

| implementation | immutable identity |
|---|---|
| Dewata | `consciousclarity/dewata-org@25ad44dc8c7f492efb942a8810fdb6efabdfdd18` |
| Peradnya TypeScript 0.4.3 | `peradnya/balinese-date-js-lib@da4193c26cc73c67a3dd82bb3281b27cc4f20dc4` |
| SHA888 Rust 0.3.0 | `SHA888/balinese-calendar@bbc82ff0dc73768a854b2e2183300e7a6c42f259` |

Repository URLs, release-tag objects, retrieval date, licenses, and per-file
SHA-256 values are in
`phase-1/tools/full_range_cross_validation/provenance.json`. The harness checks
those bytes before execution. The exact Rust dependency resolution is preserved
in `rust-Cargo.lock`; Peradnya's upstream lockfile is hash-pinned.

## Method

All three implementations received the same proleptic-Gregorian dates. Raw
native indexes, names, and positions were preserved first. A separate
normalization then represented positions zero-based, normalized the spelling
`Keliwon`/`Kliwon`, and applied exactly +84 days to Dewata's Pawukon phase for
the analytical phase-normalized comparison. Raw observations were never
overwritten.

Comparable fields were Pawukon position, Wuku index, Pancawara, Saptawara,
Triwara, and Sadwara. Wuku labels were preserved in raw output, but equality was
measured by Wuku index because Dewata's current label table is a separate,
unresolved semantic concern. The audit did not compare sunrise boundaries,
Saka/Sasih, Rahinan, Caturwara, Astawara, Sangawara, Dasawara, or cultural
meaning.

## Exact results

Peradnya and Rust agreed in raw form for all six comparable fields on
73,049/73,049 dates, with 0/73,049 disagreements per field.

For both Dewata-vs-Peradnya and Dewata-vs-Rust:

| field | raw matches | raw disagreements | +84-day phase-normalized matches | normalized disagreements |
|---|---:|---:|---:|---:|
| Pawukon position | 0/73,049 | 73,049/73,049 | 73,049/73,049 | 0/73,049 |
| Wuku index | 0/73,049 | 73,049/73,049 | 73,049/73,049 | 0/73,049 |
| Pancawara | 0/73,049 | 73,049/73,049 | 73,049/73,049 | 0/73,049 |
| Saptawara | 73,049/73,049 | 0/73,049 | 73,049/73,049 | 0/73,049 |
| Triwara | 73,049/73,049 | 0/73,049 | 73,049/73,049 | 0/73,049 |
| Sadwara | 73,049/73,049 | 0/73,049 | 73,049/73,049 | 0/73,049 |

The observed offsets were constant over every date:

- `(reference Pawukon position - Dewata position) mod 210 = 84` on
  73,049/73,049 dates.
- `(reference Wuku index - Dewata Wuku index) mod 30 = 12` on
  73,049/73,049 dates.
- `(Dewata Pancawara semantic index - reference index) mod 5 = 1` on
  73,049/73,049 dates.

The Pancawara result is the five-day projection of the same 84-day phase
difference: `84 mod 5 = 4`, equivalently Dewata-minus-reference `= 1 mod 5`.
This computation demonstrates a constant relationship; it does not determine
which convention should govern Dewata.

## Evidence artifacts

- `raw-outputs.jsonl.gz`: all native observations for 73,049 dates
- `phase-normalized-comparisons.jsonl.gz`: separate per-date raw and normalized
  equality flags
- `summary.json`: exact machine-readable counts and offsets
- `SHA256SUMS`: integrity hashes for both compressed datasets, the summary,
  and the provenance record

## Conclusion and limit

The earlier 30-day observation generalizes across the entire requested
200-year range. This is verified implementation behavior, not a cultural
adjudication. Peradnya and Rust are also not independent cultural witnesses:
the Rust implementation explicitly uses Peradnya as a behavioral reference.
No Wuku-epoch or Pancawara dispute is resolved, reclassified, or promoted by
this audit. The prepared authority-validation packet is the next governance
step.
