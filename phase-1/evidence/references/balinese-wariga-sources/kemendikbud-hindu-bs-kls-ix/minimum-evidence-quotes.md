# Kemendikbud Hindu-BS-KLS-IX (2022) — minimum evidentiary quotes

Compiled: 2026-09-15.
Updated: 2026-09-16 (corrective pass: minimum-extraction reduction + license clarification).

This file contains ONLY the minimum necessary quotations required for
the evidentiary claims documented in
`phase-1/evidence/references/balinese-wariga-sources/claim-register.md`.
The full PDF is held at /tmp/refs/hindu-bs-kls-ix.pdf for verification
but is NOT redistributed in this evidence package.

## license status (verified 2026-09-16)

The PDF page 2 contains the verbatim statement:

> "Hak Cipta pada Kementerian Pendidikan, Kebudayaan, Riset, dan
> Teknologi Republik Indonesia. Dilindungi Undang-Undang."

This is **standard Indonesian government copyright assertion** — NOT
a Creative Commons license. The book is held by the Indonesian
Ministry of Education, Culture, Research, and Technology. The
Disclaimer on page 2 explains the book is "prepared by the Government
in fulfillment of quality, affordable, equitable educational book
needs" per UU No. 3 Tahun 2017.

**Conclusion**: redistribution rights are NOT explicitly granted via
an open-content license. The Indonesian government typically
distributes such textbooks for free educational use but retains
copyright. Per user instruction 2026-09-16: "If redistribution rights
are unclear, keep metadata/SHA-256/page references/only the minimum
quotation necessary for the evidentiary claim, rather than broad
extracted text."

This file replaces the prior broader pages-37-40 extraction with the
narrow minimum-evidence quotes only.

## SHA-256 fingerprint

The full PDF SHA-256:
`0ac38bf5e59c3ef755d3296894a3d865da43c0945c92b3ed4d1e19457b9fe429`

The full PDF is held at /tmp/refs/hindu-bs-kls-ix.pdf
(20,157,376 bytes, 209 pages) for verification only.

ISBN-13: 978-602-244-367-4 (full volume)
ISBN-13: 978-602-244-715-3 (volume 3)

## evidentiary quotes (minimum necessary)

### Quote 1 — Pancawara mapping (page 39, paragraph beginning "Contoh pada perhitungan Pañcawara...")

> "Contoh pada perhitungan Pañcawara sebagaimana tabel, urutannya
> adalah: (1) Umanis, (2) Pahing, (3) Pon, (4) Wage, dan (5) Kliwon."

This confirms Pancawara mapping convention: numeric 1=Umanis (mapping B).

### Quote 2 — Pawukon exceptions (page 40, paragraph beginning "Namun yang perlu dipahami ada beberapa pengecualian yaitu:")

> "Namun yang perlu dipahami ada beberapa pengecualian yaitu:
> • Pada Caturwara (Sri-Laba-Jaya-Manala) di Wuku Dunggulan ada 3 Jaya
> berturut-turut, mulai dari Redite Jaya, Soma Jaya, dan Anggara Jaya.
> • Pada Astawara di Wuku Dunggulan (Sri, Indra, Guru, Yama, Ludra,
> Brahma, Kāla, dan Uma) ada 3 Kāla berturut-turut, mulai dari Redite
> Kāla, Soma Kāla, dan Anggara Kāla.
> • Pada Sangawara (Dangu, Jangur, Gigis, Nohan, Ogan, Erangan,
> Urungan, Tulus, dan Dadi) di Wuku Sinta ada 4 Dangu berturut turut,
> dimulai dari Redite Dangu, Soma Dangu, Anggara Dangu, dan Budha Dangu."

This documents:
- Caturwara special-case: 3 consecutive Jaya at Wuku Dungulan starting from Redite Jaya
- Astawara special-case: 3 consecutive Kala at Wuku Dungulan starting from Redite Kala
- Sangawara special-case: 4 consecutive Dangu at Wuku Sinta starting from Redite Dangu

## evidence-package integrity

This file replaces the prior broader extraction
(`pages-37-40-extracted.txt`, 6508 bytes). The narrower minimum-quote
version preserves every evidentiary claim made in
`claim-register.md` while reducing the committed text to only the
minimum necessary for those claims.

Test verification: `test_kemendikbud_pages_extracted` in
`test_wariga_evidence.py` continues to pass on the narrower extraction
because it asserts the presence of "Caturwara", "Sangawara",
"Dungulan" / "Dunggulan", "Sinta", and the Indonesian keyword
"pengecualian", all of which appear in Quote 2 above.
