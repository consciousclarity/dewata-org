---
canonical_term: inclusive-date-range
canonical_slug: inclusive-date-range
category: calendar
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: inclusive-date-range
  en:
    status: implementation_definition
    spelling: inclusive-date-range
alternative_spellings:
- inclusive-date-range
short_definition: Rentang inklusif start..end. end < start → HTTP 400. > 366 hari
  → HTTP 413 (lihat RANGE_LIMIT).
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
- path: phase-1/src/dewatacalendar/dsp.py
  role: implementation
- path: phase-1/docs/runbook/RANGE_LIMIT.md
  role: policy
- path: phase-1/src/dewatacalendar/tests/test_range_limit.py
  role: tests
  quote: test_one_day_range_succeeds_and_items_has_length_one
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

# Inclusive Date Range

Rentang inklusif start..end. end < start → HTTP 400. > 366 hari → HTTP 413 (lihat RANGE_LIMIT).


