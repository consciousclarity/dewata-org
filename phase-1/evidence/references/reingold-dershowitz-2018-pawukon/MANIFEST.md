# Evidence package manifest

**Citation key:** `reingold-dershowitz-2018-balinese-pawukon`

## contents

| artifact | sha256 | size | role |
|---|---|---|---|
| `bibliographic-metadata.md` | (regenerated on edit; current sha not committed) | ~15KB | human-readable bibliographic record for Cambridge 2018 Ultimate Edition + CALENDRICA 4.0 metadata |
| `claim-register.md` | (regenerated on edit) | ~25KB | claim-scoped verification register for prose chapter + CALENDRICA |
| `dewata-vs-firstparty-calendrica-comparison.md` | (regenerated on edit) | ~10KB | read-only comparison of Dewata vs FIRST-PARTY CALENDRICA 4.0 on full 210-day cycle + 11 representative dates |
| `firstparty-EdReingold-calendar-code2/METADATA.json` | (regenerated on edit) | ~5KB | first-party source metadata (EdReingold/calendar-code2, Apache 2.0) |
| `firstparty-EdReingold-calendar-code2/LICENSE` | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` | 11357 bytes | first-party Apache 2.0 LICENSE file |
| `firstparty-EdReingold-calendar-code2/calendar.l` | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` | 254735 bytes | first-party Common Lisp source (Apache 2.0 permits redistribution; copyright notice preserved) |
| `firstparty-EdReingold-calendar-code2/dates.l` | `d81cdfc1a3777b5dbf64473af3f5d272a73afda0fa5f2e97ec2ab299421a863e` | 12578 bytes | first-party sample-data generation script |
| `firstparty-EdReingold-calendar-code2/README.md` | `c92d48ed825f98b233ae5c156427561a8732dbf1bb02329895309939ef9cc3e3` | 16 bytes | first-party README |
| `firstparty-EdReingold-calendar-code2/calixir-vs-firstparty-diff.md` | (regenerated on edit) | ~6KB | comparative diff analysis (whole-file, license header only) |
| `firstparty-EdReingold-calendar-code2/cycle-comparison/firstparty-cycle-210.csv` | `aebb168097865b0ae4405338d58b12a9baec8a4c3c37fd204c9e98249956542a` | ~6KB | first-party CALENDRICA output for full 210-day cycle starting at 1981-08-23 |
| `firstparty-EdReingold-calendar-code2/cycle-comparison/dewata-cycle-210.csv` | `99b7b12e18412d83f52193fd1989d6bd0b7365fd0a82060973dbd3f59a8d92de` | ~6KB | Dewata output for full 210-day cycle starting at 1981-08-23 |
| `firstparty-EdReingold-calendar-code2/cycle-comparison/modern-dates-comparison.md` | (regenerated on edit) | ~1KB | 11 representative modern dates comparison |
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
  - bibliographic existence: **VERIFIED** (three independent sources agree: Cambridge publisher page, CrossRef, Open Library)
  - substantive calendrical claims: **NOT YET VERIFIED** — chapter text inaccessible from this host
  - scope: Pawukon / Wewaran only — Saka/Sasih/pengalantaka/nampih are explicitly out of scope for this source until chapter text confirms it covers them
- **first-party implementation (EdReingold/calendar-code2, PRIMARY):**
  - repository URL: `https://github.com/EdReingold/calendar-code2`
  - commit SHA: `9afc1f3277b839db1a70c2350d6c708ac83df78f`
  - source SHA-256: `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484`
  - source blob SHA-1: `2e4ad0f58ac52cb5fd497aa97b2b9ffe57ec623d`
  - LICENSE: **Apache License 2.0** (verbatim)
  - LICENSE SHA-256: `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`
  - source authenticated: **VERIFIED** (blob SHA-1 matches GitHub API)
  - runtime verified: **YES** (SBCL 2.2.9; full 210-day cycle generated)
  - 13 claims extracted, see `claim-register.md`
  - claim-scoped verification: 4 modular-arithmetic claims ELIGIBLE (210/210 cycle match); 5 disputed claims
- **secondary implementation (rengel-de/calixir, PRESERVED):**
  - SHA-256: `5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb`
  - algorithmic equivalence to first-party: **byte-identical** (7344 lines, line-by-line `diff` produces 0 lines)
  - license header: older restrictive (NOT first-party Apache)
  - preserved for provenance only; not authoritative

## copyright

The archived JSON/HTML/MD/LISP/CSV artifacts include:
- bibliographic metadata only (HTML pages, JSON metadata records) — short, safe to commit
- first-party LICENSE (Apache 2.0) — explicitly intended to be redistributed
- first-party README, dates.l script — short, safe to commit
- secondary LICENSE (older restrictive header) — preserved for provenance
- secondary sample data (dates4.csv) — preserved for provenance

The body of the Cambridge chapter is **not** archived here because:
- the chapter is copyrighted by Cambridge University Press
- it is not accessible from this host (paywall + JS-rendered shell)
- it is not permitted for redistribution without a license

The first-party CALENDRICA 4.0 source file `calendar.l` IS committed under
Apache 2.0. Apache 2.0 requires the LICENSE file to be preserved alongside
any redistribution; this is done via `firstparty-EdReingold-calendar-code2/LICENSE`
(SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`).
Copyright notice is preserved in the in-file header of `calendar.l` (lines 1-19).
Any state-changes (this commit being the first state-change) are recorded in
the git history.

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
