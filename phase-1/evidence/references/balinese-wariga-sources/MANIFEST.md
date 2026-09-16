# MANIFEST — Balinese Wariga Source Package

Compiled: 2026-09-15.

All files in this directory are evidence artifacts retrieved from independent Balinese Wariga sources.
Each row records file SHA-256, size, and retrieval date.

## Files

| File | Purpose | Size (bytes) | SHA-256 | Retrieval date |
|---|---|---|---|---|
| `bibliographic-records.md` | Catalog of source records | — | (markdown, no hash) | 2026-09-15 |
| `claim-register.md` | Claim-by-claim matrix | — | (markdown, no hash) | 2026-09-15 |
| `source-provenance-graph.md` | Lineage graph | — | (markdown, no hash) | 2026-09-15 |
| `source-access-notes.md` | Retrieval methodology | — | (markdown, no hash) | 2026-09-15 |
| `kemendikbud-hindu-bs-kls-ix/pages-37-40-extracted.txt` (stub) | Superseded stub — see `minimum-evidence-quotes.md` | historical |
| `kemendikbud-hindu-bs-kls-ix/minimum-evidence-quotes.md` | Kemendikbud textbook minimum-evidence quotes + license status | 3867 | (no hash on markdown) | 2026-09-16 |
| `edysantosa-sakacalendar/extracted-functions.txt` | Java Pawukon/Wewaran functions + Jaya Tiga docs | 5940 | (no hash on extracted text) | 2026-09-15 |

## Original source artifacts (NOT included in git)

The original source artifacts are held outside this evidence directory for copyright/access reasons.
SHA-256 fingerprints recorded for provenance.

| Source | Artifact | Size (bytes) | SHA-256 | Held at |
|---|---|---|---|---|
| S1 Pokok-Pokok Wariga | not retrieved | — | — | — |
| S2 Tenung Wariga | not retrieved | — | — | — |
| S3 edysantosa/sakacalendar | `SakaCalendar.java` | 119709 | `dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579` | `/tmp/refs/sakacalendar.java` (working copy) |
| S4 Kemendikbud Hindu-BS-KLS-IX | `Hindu-BS-KLS-IX.pdf` | 20157376 | `0ac38bf5e59c3ef755d3296894a3d865da43c0945c92b3ed4d1e19457b9fe429` | `/tmp/refs/hindu-bs-kls-ix.pdf` (working copy) |
| S5a babadbali/pancawara.htm | HTML page | 10340 | `a2958109770f38e448cbbf2b5624231ecac520152c1cb868668b66f1054c3adb` | `/tmp/refs/babadbali-pancawara.html` (working copy) |
| S5b babadbali/wuku.htm | HTML page | 20983 | `3a970cf779236dda3d40800db1e66829e60d936eabaa231b43b4f010fb710af9` | `/tmp/refs/babadbali-wuku.html` (working copy) |

## Copyright status

| Source | Copyright status |
|---|---|
| S1 Pokok-Pokok Wariga | Copyright Paramita. No full text retained in this evidence package. Bibliographic metadata only. |
| S2 Tenung Wariga | Copyright Bali Aga. No full text retained. Bibliographic metadata only. |
| S3 edysantosa/sakacalendar | LGPL-2.1 license. Only extracted function bodies retained (under fair use for analysis/citation). Full file retained only at /tmp/refs/ for runtime verification. |
| S4 Kemendikbud textbook | Indonesian government open-content (free for educational use). Pages 37-40 extracted (text-only quotation, ~6500 chars). Full PDF retained only at /tmp/refs/ for verification. |
| S5 babadbali.com | Copyright holder unknown. HTML pages retained only at /tmp/refs/ for retrieval verification. Substantive claims quoted under fair use. |

## Note on extraction choices

Per PROTOCOL v1.0 and user instruction:
- We do NOT commit copyrighted full-book/chapter material to the public repo
- We DO commit metadata/hashes/citation/short quotations/claim records
- We DO retain working copies at /tmp/refs/ for runtime verification (outside public repo)
- The original PDFs/HTML files are NOT in this git directory
