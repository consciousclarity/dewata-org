---
canonical_term: calendar-engine
canonical_slug: calendar-engine
category: calendar
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: calendar-engine
  en:
    status: implementation_definition
    spelling: calendar-engine
alternative_spellings:
- calendar-engine
short_definition: 'Engine layers: pawukon → saka → wewaran → rahinan → compose_day.
  Each layer is modular and must not reference a higher layer.'
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
- path: phase-1/src/dewatacalendar/api.py
  role: implementation
- path: phase-1/src/dewatacalendar/pawukon.py
  role: implementation
- path: phase-1/src/dewatacalendar/saka.py
  role: implementation
- path: phase-1/src/dewatacalendar/wewaran.py
  role: implementation
- path: phase-1/src/dewatacalendar/rahinan.py
  role: implementation
evidence_status: implementation_definition
dispute_ids: []
customary_review_status: pending_customary_review
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
last_reviewed: '2026-09-17'
reviewer: '[[ai-trail]]/wiki-foundation-20260917'
status: implementation_definition
---

# Calendar Engine

Engine layers: pawukon → saka → wewaran → rahinan → compose_day. Each layer is modular and must not reference a higher layer.


