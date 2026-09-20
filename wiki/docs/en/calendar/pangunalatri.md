---
canonical_term: pangunalatri
canonical_slug: pangunalatri
category: calendar
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: pangunalatri
  en:
    status: implementation_definition
    spelling: pangunalatri
alternative_spellings:
- pangunalatri
short_definition: Unimplemented engine surface (term is real, computation removed).
detailed_explanation: (definition body intentionally short — see source citations;
  expansion requires customary sign-off or new evidence)
dewata_specific_meaning: definition carried from the source citations; this page does
  not introduce new authority
affects:
- calculation
- display-only
examples: []
related_terms: []
source_citations:
- path: phase-1/src/dewatacalendar/rulesets.py
  role: ruleset
  quote: pangunalatri_days=63
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
    Unimplemented surface. The previous engine emitted an
    `is_pangunalatri` flag on `SakaDate`, but the underlying
    day-dropping calculation was not implemented: `_new_moon_doy` was
    a stub that returned `88` and its docstring described a
    synodic-month computation the body did not perform. The flag and
    `PANGUNALATRI_PERIOD` constant were removed in the 2026-09-20
    strip of unimplemented fields. The term *pangunalatri* is real;
    the engine does not compute it.
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
last_reviewed: '2026-09-20'
reviewer: '[[ai-trail]]/strip-saka-unimplemented-fields-20260920'
status: implementation_definition
---

# Pangunalatri

**Unimplemented surface.** The engine does not currently compute
pangunalatri. The previous implementation emitted an `is_pangunalatri`
flag keyed on a 63-day cycle, but the supporting synodic-month
calculation was a stub (`_new_moon_doy` returned `88` and never called
its own synodic-month formula). Both the flag and the constant
`PANGUNALATRI_PERIOD` were removed in the 2026-09-20 strip of
unimplemented fields.

The term itself is real and remains a valid concept for the Balinese
lunisolar calendar; it simply is not part of the engine's current
output. Restoring it requires an eligible published source the
repository does not have, plus resolution of three open
`sasih_index_drift` disputes:

- DISPUTE-SASAH-KAPAT-KATIGA-BOUNDARY-2026-09
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
- DISPUTE-ENGINE-SASIH-INDEX-INVERSION


