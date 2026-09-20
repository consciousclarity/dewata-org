---
canonical_term: nyepi
canonical_slug: nyepi
category: rahinan
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: nyepi
  en:
    status: implementation_definition
    spelling: nyepi
alternative_spellings:
- nyepi
short_definition: Permukaan engine yang belum diimplementasikan (istilah nyata, predikat tidak pernah terpicu).
detailed_explanation: (definition body intentionally short — see source citations;
  expansion requires customary sign-off or new evidence)
dewata_specific_meaning: definition carried from the source citations; this page does
  not introduce new authority
affects:
- calculation
examples: []
related_terms: []
source_citations:
- path: phase-1/src/dewatacalendar/rahinan.py
  role: implementation
  quote: id 'nyepi'
- path: phase-1/src/dewatacalendar/i18n.py
  role: implementation
  quote: RAHINAN_I18N
evidence_status: implementation_definition
dispute_ids:
- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION
customary_review_status:
  status: pending_customary_review
  note: >-
    Permukaan yang belum diimplementasikan. Predikat sebelumnya
    adalah `saka.sasih_idx == 9 and saka.is_tilem and saka.lunar_tithi == 1`,
    yang secara praktis tidak pernah terpicu terhadap indeks sasih
    yang belum divalidasi dan kolom lunar yang dihapus; oleh karena
    itu merupakan cabang unreachable dan tidak memancarkan rahinan
    apapun pada tanggal manapun dalam rentang yang didukung.
    Predikat dan kolom-kolom yang mendasarinya (`saka.is_tilem`,
    `saka.lunar_tithi`) dihapus pada strip 2026-09-20 untuk kolom
    yang belum diimplementasikan, dan id rahinan `nyepi` tidak
    lagi dipancarkan oleh engine.
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
last_reviewed: '2026-09-20'
reviewer: '[[ai-trail]]/strip-saka-unimplemented-fields-20260920'
status: implementation_definition
---

# Nyepi

**Permukaan yang belum diimplementasikan.** Engine saat ini tidak
memancarkan Hari Raya Nyepi. Predikat sebelumnya adalah
`saka.sasih_idx == 9 and saka.is_tilem and saka.lunar_tithi == 1`,
yang secara praktis tidak pernah terpicu terhadap indeks sasih yang
belum divalidasi dan kolom lunar yang dihapus: oleh karena itu
merupakan cabang unreachable dan tidak memancarkan rahinan apapun
pada tanggal manapun dalam rentang yang didukung. Predikat dan
kolom-kolom yang mendasarinya (`saka.is_tilem`, `saka.lunar_tithi`)
dihapus pada strip 2026-09-20 untuk kolom yang belum
diimplementasikan, dan id rahinan `nyepi` tidak lagi dipancarkan oleh
engine.

Nyepi nyata dan tetap merupakan konsep yang valid untuk kalender
lunisolar Bali; engine hanya tidak menghitungnya. Predikat yang
benar tidak dapat ditulis sampai kalender lunisolar nyata
diimplementasikan dan tiga sengketa `sasih_index_drift` terbuka
diselesaikan:

- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION

