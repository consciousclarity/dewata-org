---
canonical_term: nampih-sasih
canonical_slug: nampih-sasih
category: calendar
language_variants:
  ban:
    status: pending_customary_review
    spelling: (no verified Bahasa Bali spelling)
    note: Bahasa Bali spelling is not in phase-1/src/dewatacalendar/i18n.py or README_BAL.md
      for this term; id/en body carries the meaning
  id:
    status: implementation_definition
    spelling: nampih-sasih
  en:
    status: implementation_definition
    spelling: nampih-sasih
alternative_spellings:
- nampih-sasih
short_definition: Bali Saka intercalation. The declared Tilem Kapitu rule is not
  implemented; the engine uses an uncited saka_year % 3 test.
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
- path: phase-1/src/dewatacalendar/saka.py
  role: implementation
- path: phase-1/src/dewatacalendar/rulesets.py
  role: ruleset
  quote: nampih_declared_rule_implemented=False
evidence_status: implementation_definition
dispute_ids:
- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET
customary_review_status: pending_customary_review
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
last_reviewed: '2026-09-20'
reviewer: '[[ai-trail]]/nampih-rule-metadata-20260920'
status: implementation_definition
---

# Nampih Sasih

**Declared rule not implemented.** The ruleset declares Bali Saka
intercalation as preventing Tilem Kapitu from falling in Gregorian
December. The engine does not implement that rule. It applies a single
uncited test instead — `saka_year % 3 == 0` yields a nampih Desta year
of 13 sasih and 395 days, and every other year is 12 sasih and 365
days. Since the 2026-09-20 strip removed tilem from the engine, the
declared Tilem Kapitu predicate can no longer be evaluated at all.

`phase-1/docs/audit/GAP_ANALYSIS_v1.0_2026-09-15.md` Finding 3 records
this gap as blocking for `saka_sasih`, Phase 0 and ruleset promotion,
and notes that the engine does not model the 1993–2003 nampih regimes
that the Peradnya, Rust and TypeScript implementations gate on:

- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET


