# Ruleset Changelog

> indonesian-language changelog. every ruleset bump appends a section here.

## v0.1 — `pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0` (13 September 2026)

rilis awal. mencakup:

  - **pawukon**: 30 wuku, 210-day cycle, 10 concurrent weeks (5/6/7 synchronous, 4/8/9 derived with urip).
  - **saka (bali)**: 12 sasih + nampih Desta/Sadha (year mod 3), pangunalatri 63-day. epoch 1979-03-29 = Saka 1901.
  - **wewaran**: 10 concurrent cycles (Eka-Dasa Wara), dengan urip-10 arithmetic.
  - **rahinan**: 11 hari penting yang dihitung (Buda Wage, Buda Kliwon, Saniscara Umanis, Tumpek Landep, Anggara Kasih, Redite Paing, Purnama, Tilem, Saraswati, Galungan, Kuningan, Nyepi).
  - **conformance corpus**: 75,608 vectors (47,847 pawukon, 19,993 saka/wewaran/rahinan/integration).

rujukan akademik:
  - Dershowitz & Reingold, *Calendrical Calculations*, ch. 11 (Pawukon).
  - Cunningham 1994, *Balinese Calendar: a Pre-Dating Guide* (epoch convention).
  - Igarashi 1999, *Balinese Calendar Chronology and the Lunisolar Adjustment*.

customary sign-off:
  - pending. belum ada customary authority yang menandatangani untuk v0.1.
  - belum ada dispute yang sudah di-resolve.

catatan: 3 cross-validation disagreements tercatat di `disputes.json`. semuanya `pending` dan berkategori `epoch_offset` atau `rule_drift`. belum ada yang di-resolve.


## docs correction — v0.1.0 (14 September 2026)

corrected three stale claims in `RELEASE_v0.1.0.md`:

- test count: was `43 tests pass in 3.14s`, now `23 passed, 4 skipped`
  (corpus-loading tests skip when `phase-1/conformance/*.json` is not
  present; corpus generator is documented at `tests/gen_corpus.py`).
- CI workflow claim removed (no `.github/workflows/test.yml`
  has been committed).
- public deployment claim updated: `api.dewata.org` is live behind
  the `dewata-vps` Cloudflare-managed tunnel; calendar endpoints
  respond. Other surface hosts (`bci.`, `protocol.`, `datasets.`,
  `<id>.<kab>.`) are planned, not routed.
