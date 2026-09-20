---
canonical_term: tilem
canonical_slug: tilem
category: rahinan
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: tilem
  en:
    status: implementation_definition
    spelling: tilem
alternative_spellings:
- tilem
short_definition: Unimplemented engine surface (term is real, computation removed).
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
    Unimplemented surface. The previous engine emitted a `tilem`
    rahinan id keyed on `saka.is_tilem`, which was a boolean derived
    from `lunar_tithi in (29, 30)` — an arithmetic window, not an
    astronomical computation. The flag, the tithi field it depended
    on, and the rahinan id were all removed in the 2026-09-20 strip
    of unimplemented fields. The term *tilem* is real; the engine
    does not compute it.
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
last_reviewed: '2026-09-20'
reviewer: '[[ai-trail]]/strip-saka-unimplemented-fields-20260920'
status: implementation_definition
---

# Tilem

**Unimplemented surface.** The engine does not currently compute
Tilem. The previous implementation emitted a `tilem` rahinan id keyed
on `saka.is_tilem`, which was a boolean derived from
`lunar_tithi in (29, 30)` — an arithmetic window, not an astronomical
computation. The flag, the `lunar_tithi` field it depended on, and the
`tilem` rahinan id were all removed in the 2026-09-20 strip of
unimplemented fields.

The term itself is real and remains a valid concept for the Balinese
lunisolar calendar; it simply is not part of the engine's current
output. Restoring it requires an eligible published source the
repository does not have, plus resolution of three open
`sasih_index_drift` disputes:

- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION

