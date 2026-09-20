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
short_definition: Unimplemented engine surface (term is real, predicate was unsatisfiable).
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
    Unimplemented surface. The previous predicate was
    `saka.sasih_idx == 9 and saka.is_tilem and saka.lunar_tithi == 1`,
    which was unsatisfiable in practice against the unvalidated sasih
    index and the removed lunar fields; it was therefore an unreachable
    branch and emitted no rahinan. The predicate and the underlying
    fields were removed in the 2026-09-20 strip of unimplemented
    fields, and the `nyepi` rahinan id is no longer emitted by the
    engine. A correct predicate cannot be written until a real
    lunisolar calendar is implemented and the open sasih_index_drift
    disputes are resolved.
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

**Unimplemented surface.** The engine does not currently emit Hari
Raya Nyepi. The previous predicate was
`saka.sasih_idx == 9 and saka.is_tilem and saka.lunar_tithi == 1`,
which was unsatisfiable in practice against the unvalidated sasih
index and the removed lunar fields: it was therefore an unreachable
branch and emitted no rahinan on any date in the supported range. The
predicate and the underlying fields (`saka.is_tilem`,
`saka.lunar_tithi`) were removed in the 2026-09-20 strip of
unimplemented fields, and the `nyepi` rahinan id is no longer emitted
by the engine.

Nyepi is real and remains a valid concept for the Balinese lunisolar
calendar; the engine simply does not compute it. A correct predicate
cannot be written until a real lunisolar calendar is implemented and
the three open `sasih_index_drift` disputes are resolved:

- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION

