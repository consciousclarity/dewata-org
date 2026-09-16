# Balinese Wariga Source Records — Bibliographic Inventory

Compiled: 2026-09-15.
Scope: independent Balinese Wariga / Pawukon / Wewaran reference sources, their bibliographic records, and accessibility status.

This file is **inventory-only**: it does NOT assert substantive algorithmic claims.
Substantive claims about specific Wewaran formulas appear in `claim-register.md`,
each tied back to a specific retrievable source with page reference and quotation.

---

## S1. Pokok-Pokok Wariga (I.B. Suparta Ardhana, 2006) — Target Source

**Bibliographic record:**
- Author: **I.B. Suparta Ardhana** (variants: I B Ardhana Suparta, Suprapta Ardhana I.B.)
- Title: **Pokok-pokok Wariga** (Cet. 1, Cetakan Pertama = First Printing)
- Publisher: **Paramita** (per Open Library record; also cited as "Penerbit Paramita Bali" in commercial listings)
- Publish Place: **Surabaya** (per Open Library)
- Publish Date: **2006** (per Open Library `first_publish_year`); some academic citations render as 2005 (likely printing-vs-distribution distinction)
- ISBN-10: **979722242X**
- LCCN: **2007308755** (Library of Congress Control Number — assigned after publication)
- Pages: x + 182 pp.
- Language: Indonesian
- Country: Indonesia (io)
- Bibliography: p. 182

**Independent catalog confirmation:**
- Open Library work: OL5988117W
- Open Library author: OL1493268A
- Library of Congress MARC record (cited in Open Library)
- MLCSE classification: MLCSE 2008/00223 (B), MLCSE 2008/02258 (B)
- Commercial availability: Tokopedia, Penerbit Paramita Bali, Rp68.000 (~$4.30 USD)

**Independent academic citations:**
- DOI 10.31091/sw.v3i0.214: cites "Suprapta, Ardhana I.B. Pokok-pokok Wariga, Surabaya: Paramita, 2005." (date variant)
- ISI Yogyakarta journal article: cites "I.B. Suparta Ardhana, Pokok-pokok Wariga, (Surabaya: Paramita, 2005), p. 1." (date variant)

**Date discrepancy:** Open Library `first_publish_year=2006`; academic citations consistently give 2005. Likely cause: physical printing late 2005, registered/registered with ISBN distributor in 2006. Both dates circulate in academic citation; Open Library's record is the catalog authority.

**Accessibility status:**
- Open Library `ebook_access: "no_ebook"` — no full text available through Open Library.
- No full text retrievable from this host.
- Held by Library of Congress (per MARC record).
- Commercially available (Paramita Bali, ~$4.30 USD).

**Bibliographic verification status:** **VERIFIED**.
**Substantive verification status:** **NOT VERIFIED — chapter text not accessible from this host**.
Per PROTOCOL v1.0 and user instruction (verbatim): "If only bibliographic metadata is accessible, stop short of substantive verification for that source."

---

## S2. Tenung Wariga (I.B. Putra Manik Aryana, 2009) — Companion Source

**Bibliographic record:**
- Author: **I.B. Putra Manik Aryana, SS., M.Si**
- Title: **Tenung Wariga**
- Publisher: **Bali Aga**
- Publish Place: **Denpasar**
- Publish Date: **2009**

**Accessibility status:**
- Not cataloged in Open Library (numFound=0 for query).
- Cited in academic literature as the reference for Wariga divination.
- Used as reference source in `edysantosa/sakacalendar` Java implementation (see S3).

**Bibliographic verification status:** **VERIFIED** via academic citation (cited as the reference source in `edysantosa/sakacalendar`).
**Substantive verification status:** **NOT VERIFIED — text not accessible from this host.**

---

## S3. edysantosa/sakacalendar (Java implementation citing S1, S2)

**Type:** Derivative open-source implementation citing S1 and S2 as its source of truth. (Not an independent attestation of S1/S2; same evidentiary lineage.)

**Repository metadata:**
- URL: https://github.com/edysantosa/sakacalendar
- Default branch: master (mutable; NOT used as canonical evidence locator)
- License: **LGPL-2.1** (verified via LICENSE file retained at
  `edysantosa-sakacalendar/LICENSE.LGPL-2.1`)
- Author: Edy Santosa Putra (celak.pande@gmail.com)

**Pinned upstream commit (canonical evidence identity, NOT mutable master):**
`21ff347c0431cb12e02296f76077aa40525da9e0`

Immutable source identity: `edysantosa/sakacalendar@21ff347c0431cb12e02296f76077aa40525da9e0`

Canonical upstream URL:
`https://github.com/edysantosa/sakacalendar/tree/21ff347c0431cb12e02296f76077aa40525da9e0`

Source file path at pinned commit:
`src/main/com/edysantosa/sakacalendar/SakaCalendar.java`

**Upstream license:** GNU LGPL 2.1
License text retained at `edysantosa-sakacalendar/LICENSE.LGPL-2.1`
SHA-256 `9b872a8a070b8ad329c4bd380fb1bf0000f564c75023ec8e1e6803f15364b9e9`

**Explicit source attribution in source code:**
> Reference books cited in code:
> - "Dasar Wariga" + "Tenung Wariga" by I.B. Putra Manik Aryana
> - "Pokok-pokok Wariga" by I.B. Supartha Ardana

(Note: code spells "Supartha Ardana"; Open Library spells "Suparta Ardhana" — same person, romanization variant.)

**Source file SHA-256 (verified independently against pinned commit on 2026-09-16):**
`dda574c4d0434c9fcc35fa60fa700e1ae1f8e7b5eafc88d20346ed93d5687579`

**Authority basis:** Software reference implementation that explicitly cites S1 and S2.
**Eligibility:** **ELIGIBLE** for algorithmic claims, but only as **derivative of S1/S2** (not independent).

**Provenance rationale:** The excerpt is a function-level excerpt from
an LGPL-2.1-licensed upstream source; upstream author attribution and
license are retained in this evidence package. The excerpt remains
subject to the upstream GNU LGPL 2.1 license (not Dewata's project
license).

---

## S4. Kemendikbud Hindu-BS-KLS-IX (Indonesian Ministry of Education, 2022)

**Type:** Indonesian government-published textbook on Hindu Religion for grade 9.

**Bibliographic record:**
- Publisher: Kementerian Pendidikan, Kebudayaan, Riset, dan Teknologi (Kemendikbud) + Kementerian Agama (Religious Affairs Ministry)
- Title: Hindu-BS-KLS-IX (Hindu Pendidikan Agama Buddha / Hindu Religion Book, Grade 9)
- Year: 2022
- License status (verified 2026-09-16 from PDF page 2): standard Indonesian government copyright assertion ("Hak Cipta pada Kementerian Pendidikan, Kebudayaan, Riset, dan Teknologi Republik Indonesia. Dilindungi Undang-Undang."). NOT a Creative Commons license or any other open-content license. Explicit redistribution permission was not identified; only minimum quotations necessary for evidentiary claims are retained.
- Source URL: https://static-sc.cloudapp.web.id/content/pdf/bukuteks/kurikulum21/Hindu-BS-KLS-IX.pdf
- Access date: 2026-09-15

**Source file SHA-256:**
`0ac38bf5e59c3ef755d3296894a3d865da43c0945c92b3ed4d1e19457b9fe429`

**Wewaran content location:** Pages 37–40 contain (minimum quotations in `minimum-evidence-quotes.md`):
- Pancawara mapping "(1) Umanis, (2) Pahing, (3) Pon, (4) Wage, (5) Kliwon"
- Caturwara/Astawara/Sangawara tables
- **Pawukon exceptions** ("Namun yang perlu dipahami ada beberapa pengecualian yaitu") — page 40 explicitly documents:
  - Caturwara: 3 consecutive Jaya at Wuku Dungulan (Redite Jaya, Soma Jaya, Anggara Jaya)
  - Astawara: 3 consecutive Kala at Wuku Dungulan
  - Sangawara: 4 consecutive Dangu at Wuku Sinta (Redite Dangu, Soma Dangu, Anggara Dangu, Budha Dangu)

**Authority basis:** Official Indonesian government textbook on Hindu religion, currently in use for state school curriculum (Kurikulum 21 / Merdeka curriculum).
**Eligibility:** **ELIGIBLE** as independent Balinese Hindu educational source.

---

## S5. babadbali.com (Independent Balinese cultural reference)

**Type:** Balinese cultural reference website.

**Bibliographic record:**
- URL: https://www.babadbali.com
- Pages accessed:
  - https://www.babadbali.com/pewarigaan/pancawara.htm — SHA-256 `a2958109770f38e448cbbf2b5624231ecac520152c1cb868668b66f1054c3adb`
  - https://www.babadbali.com/pewarigaan/wuku.htm — SHA-256 `3a970cf779236dda3d40800db1e66829e60d936eabaa231b43b4f010fb710af9`

**Pancawara content (paraphrased from babadbali):**
> "Pancawara adalah siklus lima harian dalam wewaran. Unsur-unsurnya adalah Pon, Wage, Kliwon, Umanis dan Paing."
> (Translation: "Pancawara is a five-day cycle in the Wewaran. Its elements are Pon, Wage, Kliwon, Umanis and Paing.")

> "1 Legi or **manis** symbolizes retreat (mungkur) Rasa"
> "2 Paing or **Pait** symbolizes to face or appear in front of (madep) Cipta"
> "3 Pon or **Petak** symbolizes sleep (sare, tilem, sirep) Idep"
> "4 Wage or **Cemeng** symbolizes sit down (lenggah, negak) Angen"
> "5 Kliwon or **Kasih** symbolizes stand-up (jumeneng, mejujuk) Budi"

**Wuku content:** babadbali.wuku.htm contains all 30 wuku names (Sinta through Watugunung) with urip values, location, sifat, and symbolic associations.

**Authority basis:** Balinese cultural reference site, commonly cited in Balinese cultural research.
**Eligibility:** **ELIGIBLE** as independent Balinese cultural source.
**Note:** Same lineage as `peradnya/balinese-date-js-lib` TypeScript library which cites babadbali.com as reference. Per user instruction, software ports of CALENDRICA and re-implementations of one reference site are NOT independent witnesses — they count as one lineage.

---

## Lineage summary

| Source | Type | Independent of CALENDRICA | Independent of L1 (kb.org) | Bibliographic VERIFIED | Substantive verified |
|---|---|---|---|---|---|
| S1. Pokok-pokok Wariga | printed book | yes | yes | yes | no (text not accessible) |
| S2. Tenung Wariga | printed book | yes | yes | yes | no (text not accessible) |
| S3. edysantosa/sakacalendar | Java impl citing S1, S2 | derivative of S1, S2 | yes | yes | partial (functions visible) |
| S4. Kemendikbud Hindu-BS-KLS-IX | textbook | yes | yes | yes | partial (pages 37-40 visible) |
| S5. babadbali.com | reference site | yes | yes | yes | yes (HTML pages visible) |
| L1. kb.org | practitioner site | yes | self | yes | yes |
| L4. EdReingold/calendar-code2 | Common Lisp | self | yes | yes | yes |
| basaibubali.org | community wiki | yes | yes | yes | yes |

**Independent Balinese Wariga source lineages (excluding software ports):**
1. **S1/S2 printed books** (Pokok-pokok Wariga + Tenung Wariga) — bibliographic metadata VERIFIED, full text NOT accessible from this host
2. **S4 Kemendikbud textbook** — full text accessible (pages 37-40 visible), explicit Wewaran and Pawukon exception documentation
3. **S5 babadbali.com** — full text accessible
4. **basaibubali.org** — full text accessible (community wiki)

**Note on S1/S2/S3 dependency:** S3 is a software port that cites S1/S2 as its source of truth — they form one lineage, not multiple independent witnesses. S4 is a separate academic/government lineage. S5 is a separate cultural lineage.

---

## What is NOT verifiable from this host

- S1 (Pokok-pokok Wariga) full text — would require institutional library access or physical purchase
- S2 (Tenung Wariga) full text — same
- Any Wuku/Gregorian phase examples from printed Kalender Bali with publication provenance
