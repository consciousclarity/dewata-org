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
short_definition: Interkalasi Saka Bali. Aturan Tilem Kapitu yang dideklarasikan
  tidak diimplementasikan; engine memakai uji saka_year % 3 yang tidak bersumber.
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

**Aturan yang dideklarasikan tidak diimplementasikan.** Ruleset
mendeklarasikan interkalasi Saka Bali sebagai mencegah Tilem Kapitu
jatuh di Desember Gregorian. Engine tidak mengimplementasikan aturan
itu. Engine memakai satu uji yang tidak bersumber — `saka_year % 3 ==
0` menghasilkan tahun nampih Desta dengan 13 sasih dan 395 hari,
sedangkan tahun lainnya 12 sasih dan 365 hari. Sejak penghapusan
2026-09-20 yang mencabut tilem dari engine, predikat Tilem Kapitu yang
dideklarasikan tidak dapat dievaluasi sama sekali.

`phase-1/docs/audit/GAP_ANALYSIS_v1.0_2026-09-15.md` Temuan 3 mencatat
celah ini sebagai blocking untuk `saka_sasih`, Phase 0 dan promosi
ruleset, serta mencatat bahwa engine tidak memodelkan rezim nampih
1993–2003 yang dipakai implementasi Peradnya, Rust dan TypeScript:

- DISPUTE-SASAH-JAVA-VS-PERADNYA-OFFSET


