---
canonical_term: id-mapping
canonical_slug: id-mapping
category: rahinan
language_variants:
  ban:
    status: pending_customary_review
    spelling: "(no verified Bahasa Bali spelling)"
http://localhost:41185/chat
  id:
    status: implementation_definition
    spelling: id-mapping
  en:
    status: implementation_definition
    spelling: id-mapping
short_definition: Pemetaan dari 12 id rahinan engine ke nama hari manusia.
detailed_explanation: |
  Engine `phase-1/src/dewatacalendar/rahinan.py` memancarkan
  id-id berikut; tiap id biasa diasosiasikan dengan satu nama
  hari manusia sesuai rujukan Eiseman 1989.
dewata_specific_meaning: >
  Daftar di bawah ini berasal langsung dari implementasi
  `phase-1/src/dewatacalendar/rahinan.py`. Itu **bukan** terjemahan
  bebas; ia adalah catatan yang akan diperluas setelah tinjauan
  kebiasaan selesai.
affects:
  - calculation
examples:
  - engine emits `id="tumpek_landep"` untuk Saniscara + Keliwon.
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

# Pemetaan id engine ke nama manusia

| id engine | pencetus | nama Eiseman yang umum |
|---|---|---|
| `buda_wage` | Buda + Wage | Buda Wage |
| `buda_kliwon` | Buda + Keliwon | Buda Kliwon |
| `saniscara_umanis` | Saniscara + Umanis | Tumpek Kandang |
| `tumpek_landep` | Saniscara + Keliwon | Tumpek Landep |
| `anggara_kliwon` | Anggara + Keliwon | Anggara Kasih (label engine) |
| `redite_paing` | Redite + Paing | Tumpek Uduh |
| `purnama` | `saka.is_purnama` | Purnama (full moon) |
| `tilem` | `saka.is_tilem` | Tilem (new moon) |
| `saraswati` | Wuku 21 + Saniscara | Hari Raya Saraswati |
| `galungan` | Wuku 11 + Buda + Keliwon | Hari Raya Galungan |
| `kuningan` | Wuku 12 + Saniscara + Keliwon | Hari Raya Kuningan |
| `nyepi` | Sasih 9 + Tilem + Tithi 1 | Hari Raya Nyepi |

Label kotak `nama manusia` di sini adalah default `label` yang
dipancarkan engine pada tiap rahinan sesuai pemetaan internal;
nama Eiseman mungkin berbeda. lihat
[phase-1/src/dewatacalendar/i18n.py](https://github.com/consciousclarity/dewata-org/blob/main/phase-1/src/dewatacalendar/i18n.py) untuk ejaan
Bahasa Bali dan Indonesia resmi untuk beberapa di antaranya.
