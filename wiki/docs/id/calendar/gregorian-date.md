---
canonical_term: gregorian-date
canonical_slug: gregorian-date
category: calendar
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: gregorian-date
  en:
    status: implementation_definition
    spelling: gregorian-date
alternative_spellings:
- gregorian-date
short_definition: Tanggal Gregorian didukung oleh engine untuk tahun 1..9999 (pawukon)
  dan ≥1979 (saka).
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
  quote: compose_day accepts datetime.date
- path: phase-1/src/dewatacalendar/exceptions.py
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

# Gregorian Date

Tanggal Gregorian didukung oleh engine untuk tahun 1..9999 (pawukon) dan ≥1979 (saka).


