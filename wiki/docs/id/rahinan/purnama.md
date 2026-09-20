---
canonical_term: purnama
canonical_slug: purnama
category: rahinan
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: purnama
  en:
    status: implementation_definition
    spelling: purnama
alternative_spellings:
- purnama
short_definition: Permukaan engine yang belum diimplementasikan (istilah nyata, komputasi dihapus).
detailed_explanation: (definition body intentionally short — see source citations;
  expansion requires customary sign-off or new evidence)
dewata_specific_meaning: definition carried from the source citations; this page does
  not introduce new authority
affects:
- calculation
examples: []
related_terms: []
source_citations:
- path: phase-1/src/dewatacalendar/saka.py
  role: implementation
evidence_status: implementation_definition
dispute_ids:
- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION
customary_review_status:
  status: pending_customary_review
  note: >-
    Permukaan yang belum diimplementasikan. Engine sebelumnya
    memancarkan id rahinan `purnama` yang dikaitkan pada
    `saka.is_purnama`, yaitu boolean yang diturunkan dari
    `lunar_tithi in (14, 15)` — jendela aritmatika, bukan komputasi
    astronomis. Flag, kolom `lunar_tithi` yang menjadi
    dependensinya, dan id rahinan `purnama` semuanya dihapus pada
    strip 2026-09-20 untuk kolom yang belum diimplementasikan.
    Istilah *purnama* nyata; engine tidak menghitungnya.
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
last_reviewed: '2026-09-20'
reviewer: '[[ai-trail]]/strip-saka-unimplemented-fields-20260920'
status: implementation_definition
---

# Purnama

**Permukaan yang belum diimplementasikan.** Engine saat ini tidak
menghitung Purnama. Implementasi sebelumnya memancarkan id rahinan
`purnama` yang dikaitkan pada `saka.is_purnama`, yaitu boolean yang
diturunkan dari `lunar_tithi in (14, 15)` — jendela aritmatika, bukan
komputasi astronomis. Flag, kolom `lunar_tithi` yang menjadi
dependensinya, dan id rahinan `purnama` semuanya dihapus pada strip
2026-09-20 untuk kolom yang belum diimplementasikan.

Istilahnya sendiri nyata dan tetap merupakan konsep yang valid untuk
kalender lunisolar Bali; hanya saja bukan merupakan bagian dari output
engine saat ini. Memulihkannya membutuhkan sumber terbitan yang eligible
yang tidak dimiliki repositori, ditambah resolusi dari tiga sengketa
`sasih_index_drift` terbuka:

- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION

