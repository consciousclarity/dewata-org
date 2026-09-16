# Source Access Notes — Balinese Wariga Sources

How each source was retrieved, when, and what evidence was extracted.

---

## S1. Pokok-Pokok Wariga (I.B. Suparta Ardhana, 2006)

**Access method:**
- Open Library work record: https://openlibrary.org/works/OL5988117W.json
- Open Library edition list: https://openlibrary.org/works/OL5988117W/editions.json
- Open Library search: https://openlibrary.org/search.json?title=pokok-pokok+wariga&author=suparta
- Open Library author key: OL1493268A
- Open Library `ebook_access: "no_ebook"` — full text NOT available

**Retrieval date:** 2026-09-15

**What was retrieved:** bibliographic metadata only (title, author, publisher, ISBN-10, LCCN, page count, language, classifications)

**What was NOT retrieved:** chapter text, formula derivations, Wewaran tables

**Independent corroboration:** academic citations (ISI Yogyakarta journal, DOI 10.31091/sw.v3i0.214)

**Verdict:** bibliographic existence **VERIFIED**; substantive claims **NOT VERIFIED** from this host.

---

## S2. Tenung Wariga (I.B. Putra Manik Aryana, 2009)

**Access method:** cited in edysantosa/sakacalendar Java source code (see S3)

**Retrieval date:** 2026-09-15

**What was retrieved:** bibliographic citation (title, author, publisher, year) via S3 reference

**What was NOT retrieved:** chapter text, formula derivations

**Verdict:** bibliographic existence **VERIFIED** via S3 citation; substantive claims **NOT VERIFIED**.

---

## S3. edysantosa/sakacalendar

**Access method:**
- GitHub API repo metadata: https://api.github.com/repos/edysantosa/sakacalendar
- GitHub API tree: https://api.github.com/repos/edysantosa/sakacalendar/git/trees/master?recursive=1
- Raw source: https://raw.githubusercontent.com/edysantosa/sakacalendar/master/src/main/com/edysantosa/sakacalendar/SakaCalendar.java

**Retrieval date:** 2026-09-15

**File SHA-256:** `dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579`

**What was retrieved:** full source code (119709 bytes)

**What was NOT retrieved:** the S1/S2 source books that S3 cites

**Verdict:** source code **VERIFIED**; substantive Wewaran/Pawukon claims **PARTIALLY VERIFIED** (functions visible in code, but original S1/S2 sources not independently accessible).

---

## S4. Kemendikbud Hindu-BS-KLS-IX (2022)

**Access method:**
- Direct PDF: https://static-sc.cloudapp.web.id/content/pdf/bukuteks/kurikulum21/Hindu-BS-KLS-IX.pdf

**Retrieval date:** 2026-09-15 (license clarification: 2026-09-16)

**File SHA-256:** `0ac38bf5e59c3ef755d3296894a3d865da43c0945c92b3ed4d1e19457b9fe429`

**What was retrieved (2026-09-16 update):** minimum-evidence quotes only.
The prior broader pages-37-40 extraction (6508 bytes) has been
replaced by `minimum-evidence-quotes.md` (3867 bytes including
license documentation) containing only:
- Quote 1: Pancawara mapping convention (page 39)
- Quote 2: Pawukon exceptions paragraph (page 40)
- License status quote (page 2)

**What was NOT retrieved:** the underlying Wariga sources cited by the textbook (if any)

**License (verified 2026-09-16 from page 2):**
Verbatim statement on page 2: "Hak Cipta pada Kementerian Pendidikan,
Kebudayaan, Riset, dan Teknologi Republik Indonesia. Dilindungi
Undang-Undang."

This is **standard Indonesian government copyright assertion** — NOT
a Creative Commons license. The book is held by the Indonesian
Ministry of Education, Culture, Research, and Technology. The
Disclaimer on page 2 explains the book is "prepared by the Government
in fulfillment of quality, affordable, equitable educational book
needs" per UU No. 3 Tahun 2017.

**Redistribution rights are NOT explicitly granted.** Per user
instruction 2026-09-16: "If redistribution rights are unclear, keep
metadata/SHA-256/page references/only the minimum quotation necessary
for the evidentiary claim, rather than broad extracted text."

**Verdict:** bibliographic existence **VERIFIED**; substantive Wewaran
claims **VERIFIED** for the minimum-evidence quotes only.

---

## S5. babadbali.com

**Access method:**
- Pancawara page: https://www.babadbali.com/pewarigaan/pancawara.htm
- Wuku page: https://www.babadbali.com/pewarigaan/wuku.htm

**Retrieval date:** 2026-09-15

**File SHA-256 (pancawara.htm):** `a2958109770f38e448cbbf2b5624231ecac520152c1cb868668b66f1054c3adb`

**File SHA-256 (wuku.htm):** `3a970cf779236dda3d40800db1e66829e60d936eabaa231b43b4f010fb710af9`

**What was retrieved:** HTML pages with Pancawara and Wuku content

**Verdict:** bibliographic existence **VERIFIED**; substantive Wewaran/Wuku claims **VERIFIED**.

---

## L1. kb.org (Kalender Bali Digital)

**Access method:** HTTP GET of monthly calendar page (September 2026)

**Retrieval date:** 2026-09-15

**What was retrieved:** 7 reference dates in September 2026 with Saptawara/Pancawara/Wuku

**Verdict:** **VERIFIED** for the specific Gregorian dates queried.

---

## L4. EdReingold/calendar-code2 (CALENDRICA 4.0)

**Access method:** as documented in commit `4d37765`, `6c82001`

**Retrieval date:** 2026-09-15

**Verdict:** **VERIFIED** (see prior commits).

---

## basaibubali.org (community wiki)

**Access method:** HTTP GET of Pancawara, Caturwara, Sangawara, Asatawara, Ekawara pages

**Retrieval date:** 2026-09-15

**What was retrieved:** HTML pages with formula excerpts

**Verdict:** **VERIFIED** for the specific pages queried.

---

## Source dependency observations

- **detik, liputan6, pelajahin** quote kb.org (L1) — not independent
- **Wikipedia mirror, Grokipedia** copy Wikipedia (L2) — not independent
- **peradnya/balinese-date-js-lib** cites babadbali.com (S5) — same lineage as S5
- **S3 edysantosa/sakacalendar** cites S1+S2 — derivative of S1+S2
- **basaibubali.org** is an independent lineage (community wiki)

## Sources we would need but could not retrieve

- S1 Pokok-pokok Wariga full text (printed book, ISBN 979722242X)
- S2 Tenung Wariga full text (printed book, Bali Aga 2009)
- Independent printed Kalender Bali with publication provenance
- Customary authority attestation

Per PROTOCOL v1.0 and user instruction:
> "If only bibliographic metadata is accessible, stop short of substantive verification for that source."
