# Balinese Wariga Source Evidence — MANIFEST

Compiled: 2026-09-15.
Updated: 2026-09-16 (corrective pass: license clarification + /tmp-refs
documentation policy + lineage terminology).

This manifest records the canonical evidence record for each source
in this evidence package. For external sources, the canonical
evidence record consists of the source URL, retrieval/access date,
SHA-256 of retrieved bytes, byte size, redistribution status, and
the committed minimum quotation or metadata where legally
appropriate. Transient retrieval copies at `/tmp/refs/` are
noncanonical and are not part of permanent evidence storage.

## in-tree evidence artifacts (committed to this evidence package)

| file | purpose | size | last_modified |
|---|---|---|---|
| `bibliographic-records.md` | Catalog of source records | — | 2026-09-16 |
| `claim-register.md` | Claim-by-claim matrix | — | 2026-09-15 |
| `source-provenance-graph.md` | Lineage graph | — | 2026-09-15 |
| `source-access-notes.md` | Retrieval methodology | — | 2026-09-15 |
| `kemendikbud-hindu-bs-kls-ix/minimum-evidence-quotes.md` | Kemendikbud textbook minimum-evidence quotes + license status | 4251 | 2026-09-16 |
| `kemendikbud-hindu-bs-kls-ix/pages-37-40-extracted.txt` (stub) | Superseded stub — replaced by `minimum-evidence-quotes.md` | historical | — |
| `edysantosa-sakacalendar/extracted-functions.txt` | Java Pawukon/Wewaran functions + Jaya Tiga docs (function-level extraction) | 5940 | 2026-09-15 |

## external source records (canonical evidence = URL + hash + access date + minimum quotation)

| source | canonical URL | access date | byte size | SHA-256 | redistribution status | committed evidence |
|---|---|---|---|---|---|---|
| S1. Pokok-pokok Wariga (I.B. Suparta Ardhana, 2006, Paramita Surabaya, ISBN-10 979722242X, LCCN 2007308755) | Open Library OL5988117W bibliographic record | 2026-09-15 | n/a | n/a (book not retrieved) | NOT redistributed — copyright held by Paramita; chapter text not accessible from this host (ebook_access=no_ebook) | bibliographic metadata only |
| S2. Tenung Wariga (I.B. Putra Manik Aryana, 2009, Bali Aga Denpasar) | Open Library search returned numFound=0; cited in S3 source code | 2026-09-15 | n/a | n/a (book not retrieved) | NOT redistributed — copyright held by Bali Aga; chapter text not accessible from this host | bibliographic metadata only |
| S3. edysantosa/sakacalendar (Java implementation, LGPL-2.1) | https://github.com/edysantosa/sakacalendar/tree/21ff347c0431cb12e02296f76077aa40525da9e0 (pinned; NOT mutable master) | 2026-09-16 | 119709 | `dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579` | Derivative open-source implementation citing S1/S2 (NOT an independent evidentiary lineage from those books). Function-level excerpt from LGPL-2.1-licensed upstream source; upstream author attribution and license retained in this evidence package. Full file NOT in public repo; LGPL-2.1 LICENSE text retained in `edysantosa-sakacalendar/LICENSE.LGPL-2.1`. | `edysantosa-sakacalendar/extracted-functions.txt` (function bodies only) + `edysantosa-sakacalendar/LICENSE.LGPL-2.1` |
| S4. Kemendikbud Hindu-BS-KLS-IX (2022, Indonesian Ministry of Education, ISBN-13 978-602-244-367-4 full volume / 978-602-244-715-3 volume 3) | https://static-sc.cloudapp.web.id/content/pdf/bukuteks/kurikulum21/Hindu-BS-KLS-IX.pdf | 2026-09-15 | 20157376 | `0ac38bf5e59c3ef755d3296894a3d865da43c0945c92b3ed4d1e19457b9fe429` | Publicly retrievable but explicit redistribution permission NOT identified (standard Indonesian government copyright assertion on PDF page 2; NOT Creative Commons). Only minimum quotations necessary for evidentiary claims are retained. | `minimum-evidence-quotes.md` (4251 bytes) |
| S5. babadbali.com (cultural reference site) | https://www.babadbali.com/pewarigaan/pancawara.htm and https://www.babadbali.com/pewarigaan/wuku.htm | 2026-09-15 | 10340 / 20983 | `a2958109770f38e448cbbf2b5624231ecac520152c1cb868668b66f1054c3adb` (pancawara) / `3a970cf779236dda3d40800db1e66829e60d936eabaa231b43b4f010fb710af9` (wuku) | External source — pages retrievable; full HTML NOT in this public repo. SHA-256 fingerprints recorded in STATUS.json reason field. | SHA-256 + brief quoted observations in claim-register.md |

## /tmp/refs/ policy

PROTOCOL v1.0 makes `/tmp/` scratch space only. `/tmp/refs/` is not
durable evidence storage. The files at `/tmp/refs/` (when present)
are transient retrieval copies used during verification. The canonical
evidence record is the committed URL + SHA-256 + access date +
minimum quotation / metadata as listed above.

A transient retrieval copy may have existed during retrieval, but it
is NOT durable evidence storage. This is not a requirement that
`/tmp/refs/` files continue to exist.

## original source artifacts (NOT redistributed)

- `calendrica-source/calendrica-4.0.cl` (Calixir secondary copy): NOT in
  this public repo per the older restrictive license header on the
  Calixir-bundled source. Metadata + SHA-256 fingerprint preserved in
  `calendrica-source/METADATA.json`.
- `babadbali.com` HTML pages: NOT in this public repo (external
  source). SHA-256 fingerprints preserved in STATUS.json reason field.

## copyright status summary

| source | copyright status |
|---|---|
| S1 Pokok-pokok Wariga | Copyright Paramita. NOT redistributed. Bibliographic metadata only. |
| S2 Tenung Wariga | Copyright Bali Aga. NOT redistributed. Bibliographic metadata only. |
| S3 edysantosa/sakacalendar | LGPL-2.1. Function-level excerpt from LGPL-2.1-licensed upstream source; upstream author attribution and license retained in this evidence package. Full file NOT in repo; LICENSE.LGPL-2.1 retained at `edysantosa-sakacalendar/LICENSE.LGPL-2.1`. |
| S4 Kemendikbud textbook | Standard Indonesian government copyright assertion (NOT Creative Commons, NOT open-content). Publicly retrievable but explicit redistribution permission NOT identified. Only minimum quotations retained. |
| S5 babadbali.com | External source. Full HTML NOT in repo. SHA-256 + quoted observations only. |
| `kemendikbud-hindu-bs-kls-ix/pages-37-40-extracted.txt` (stub) | Stub retained for git-history preservation; no copyrighted content beyond what is in `minimum-evidence-quotes.md`. |

## lineage terminology

- **Independent attestation**: S4 (Kemendikbud), S5 (babadbali.com),
  and `basaibubali.org` (community wiki) are independent Balinese
  sources relative to each other.
- **Derivative open-source implementation citing S1/S2**: S3
  (edysantosa/sakacalendar) explicitly cites Pokok-pokok Wariga and
  Tenung Wariga as its source of truth. S3 is NOT an independent
  attestation of S1/S2; agreement between S3 and CALENDRICA is
  algorithmic corroboration between two software implementations
  that both trace to overlapping Wariga traditions, not customary or
  cultural attestation.

## what is NOT verifiable from this host

- S1 (Pokok-pokok Wariga) chapter text — requires institutional library
  access or commercial purchase (~$4.30 USD via Tokopedia)
- S2 (Tenung Wariga) chapter text — same
- Independent Wuku/Gregorian examples from printed Kalender Bali with
  publication provenance
