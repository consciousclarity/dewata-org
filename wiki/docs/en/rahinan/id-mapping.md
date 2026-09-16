---
canonical_term: id-mapping
canonical_slug: id-mapping
category: rahinan
language_variants:
  ban:
    status: pending_customary_review
    spelling: "(no verified Bahasa Bali spelling)"
  id:
    status: implementation_definition
    spelling: id-mapping
  en:
    status: implementation_definition
    spelling: id-mapping
alternative_spellings:
  - id-mapping
  - engine id to human name mapping
short_definition: Mapping from the 12 engine rahinan ids to human day names.
detailed_explanation: |
  The engine `phase-1/src/dewatacalendar/rahinan.py` emits the
  following ids; each id is normally associated with one human
  day name per Eiseman 1989.
dewata_specific_meaning: >
  The table below is sourced directly from the engine
  implementation. It is **not** a free translation; it is a record
  that will be expanded once customary review is complete.
affects:
  - calculation
examples:
  - the engine emits `id="tumpek_landep"` for Saniscara + Keliwon.
related_terms:
  - buda-wage
  - buda-kliwon
  - saniscara-umanis
  - tumpek-landep
  - purnama
  - tilem
source_citations:
  - path: phase-1/src/dewatacalendar/rahinan.py
    role: implementation
evidence_status: implementation_definition
dispute_ids: []
customary_review_status: pending_customary_review
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"
last_reviewed: 2026-09-17
reviewer: "[[ai-trail]]/wiki-foundation-20260917"
status: implementation_definition
---

# Engine-id to human-name mapping

| engine id | trigger | common Eiseman name |
|---|---|---|
| `buda_wage` | Buda + Wage | Buda Wage |
| `buda_kliwon` | Buda + Keliwon | Buda Kliwon |
| `saniscara_umanis` | Saniscara + Umanis | Tumpek Kandang |
| `tumpek_landep` | Saniscara + Keliwon | Tumpek Landep |
| `anggara_kliwon` | Anggara + Keliwon | Anggara Kasih (engine label) |
| `redite_paing` | Redite + Paing | Tumpek Uduh |
| `purnama` | `saka.is_purnama` | Purnama (full moon) |
| `tilem` | `saka.is_tilem` | Tilem (new moon) |
| `saraswati` | Wuku 21 + Saniscara | Hari Raya Saraswati |
| `galungan` | Wuku 11 + Buda + Keliwon | Hari Raya Galungan |
| `kuningan` | Wuku 12 + Saniscara + Keliwon | Hari Raya Kuningan |
| `nyepi` | Sasih 9 + Tilem + Tithi 1 | Hari Raya Nyepi |

The `common name` column here is the engine's own `label` value;
Eiseman's rendering may differ. See
[phase-1/src/dewatacalendar/i18n.py](https://github.com/consciousclarity/dewata-org/blob/main/phase-1/src/dewatacalendar/i18n.py)
for the canonical Bahasa Bali and Indonesian spellings for some of
these.
