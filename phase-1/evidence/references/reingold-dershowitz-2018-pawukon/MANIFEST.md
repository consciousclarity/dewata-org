# Evidence package manifest

**Citation key:** `reingold-dershowitz-2018-balinese-pawukon`

## contents

| artifact | sha256 | size | role |
|---|---|---|---|
| `bibliographic-metadata.md` | (regenerated on edit; current sha not committed) | ~15KB | human-readable bibliographic record for Cambridge 2018 Ultimate Edition + CALENDRICA 4.0 metadata |
| `claim-register.md` | (regenerated on edit) | ~25KB | claim-scoped verification register for prose chapter + CALENDRICA |
| `dewata-vs-calendrica-comparison.md` | (regenerated on edit) | ~10KB | read-only comparison of Dewata vs CALENDRICA 4.0 on 14 test dates |
| `cambridge-chapter-page-ultimate-edition.html` | `74eca7048b9b97b55ea56ea50f168815ec8b11b12454b4c84336571ea271ec3c` | 744403 bytes | publisher abstract page (bibliographic record, no chapter body) |
| `crossref-chapter-metadata.json` | `7e58d80075a46964385bcd103989aa4abd40d8387a0035f8d6137e9af681e9a0` | 1113 bytes | CrossRef REST API metadata for chapter DOI |
| `openlibrary-edition-ultimate-2018.json` | `9a158a51562eb7f49e06039b4fd9150f9c198d6e702de6b41330e65c07330b1b` | 748 bytes | Open Library edition record (isbn_13, publish_date 2018) |
| `openlibrary-work-calendrical.json` | `800904d42c179a51fc06582a23faf17f0953832be65bbc5bd4c20c1d654e0fee` | 519 bytes | Open Library work record (authors list) |
| `calendrica-source/METADATA.json` | (regenerated on edit) | ~2KB | CALENDRICA 4.0 source metadata (URL, hash, license, sample data refs) |
| `calendrica-source/COPYRIGHT_DERSHOWITZ_RHEINGOLD.txt` | `d34115459b34df91fdd60134384e2f427d29e483a6991b11c2cea42df237412c` | 4237 bytes | CALENDRICA 4.0 LICENSE file |
| `calendrica-source/dates4.csv` | `49ba8658fe1208e67589a1b4e61b70cddbd42b134c37272bccddd06cc32602ff` | 4114 bytes | CALENDRICA 4.0 sample data (Appendix C of the book) |

The CALENDRICA 4.0 Common Lisp source file itself is **NOT** included —
its LICENSE clause 1 prohibits redistribution. The source's SHA-256 is
recorded in `calendrica-source/METADATA.json`:
`5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb`.

access date for all artifacts: **2026-09-15**.

## status

- **scholarly chapter (Cambridge 2018 Ultimate Edition, ch 12):**
  - bibliographic existence: **VERIFIED** (three independent sources agree)
  - substantive calendrical claims: **NOT YET VERIFIED** — chapter text inaccessible from this host
  - scope: Pawukon / Wewaran only — Saka/Sasih/pengalantaka/nampih are explicitly out of scope for this source until chapter text confirms it covers them
- **first-party implementation (CALENDRICA 4.0):**
  - source authenticated: **VERIFIED** (retrieved from rengel-de/calixir; commit SHA recorded)
  - runtime verified: **YES** (SBCL 2.2.9; 10 sample rows from `dates4.csv` matched CALENDRICA runtime output)
  - 13 claims extracted, see `claim-register.md`
  - 11/13 claims engine-verified (CALC-012 kajeng_keliwon and CALC-013 tumpek exist in source but not yet run)
  - 5/13 claims DISPUTED with Dewata: epoch anchor (CALC-001), asatawara formula (CALC-008), caturwara formula (CALC-009), sangawara formula (CALC-010), dasawara urip_5 table (CALC-011)

## copyright

The seven archived JSON/HTML/MD artifacts are bibliographic metadata only.
They are short and consist of metadata records, not the body of the book.
They may be safely committed to a public repository.

The body of the chapter is **not** archived here because:
- the chapter is copyrighted by Cambridge University Press
- it is not accessible from this host (paywall + JS-rendered shell)
- it is not permitted for redistribution without a license

The CALENDRICA 4.0 source file is **not** committed (license clause 1).
The CALENDRICA 4.0 LICENSE file **is** committed (it is the author's
license grant, intended to be redistributed with the code, and necessary
to communicate the licensing terms).
The CALENDRICA 4.0 sample data file (`dates4.csv`) **is** committed
because the LICENSE itself directs users to the sample values in
Appendix C of the book — the CSV file is the canonical digital form of
those Appendix C values.

If the chapter text is later acquired under a license that permits
redistribution, the chapter-text artifact will be stored separately
under the canonical evidence root, not as part of this public package.
Per the governance-owner instruction: the repository must remain
independently auditable without becoming an unauthorized book mirror.

## interpretation under PROTOCOL v1.0 §2.6

This package supports the following evidence-chain elements:

| evidence chain element | status | source basis |
|---|---|---|
| `verification_status: VERIFIED` for bibliographic existence (chapter) | YES | three independent bibliographic sources (Cambridge, CrossRef, Open Library) |
| `verification_status: VERIFIED` for CALENDRICA source authentication | YES | repository URL, commit SHA, file SHA-256, runtime verification |
| `reference_eligibility: ELIGIBLE` for scholarly chapter algorithmic claims | NO | chapter text inaccessible |
| `reference_eligibility: ELIGIBLE` for CALENDRICA-derived algorithmic claims | YES for the 11 verified claims; NO for CALC-012/013 until runtime comparison; NO for the 5 disputed claims until resolution |

The `STATUS.json` corpus-evidence-status registry entries for this source
will be created separately, with claim-scoped eligibility — not at the
package level. Per the ratification instructions: VERIFIED+ELIGIBLE is
claim-scoped, not source-scoped.
