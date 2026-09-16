---
canonical_term: epoch-anchor
canonical_slug: epoch-anchor
category: calendar
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: epoch-anchor
  en:
    status: implementation_definition
    spelling: epoch-anchor
alternative_spellings:
- epoch-anchor
short_definition: The date declared as the cycle anchor for the engine, where position_in_cycle
  == 1.
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
  quote: '"epoch": "1981-08-23"'
- path: phase-1/src/dewatacalendar/pawukon.py
  role: implementation
  quote: pawukon_for_gregorian
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

# Epoch Anchor

The date declared as the cycle anchor for the engine, where position_in_cycle == 1.


