---
status: informational
translation_review_status:
  id: needs_review
  en: needs_review
  ban: pending_customary_review
last_reviewed: 2026-09-17
---

# Bagian Rahinan dan Pikoban (observansi)

Bagian ini menjelaskan jenis-jenis hari peringatan yang diterbitkan
oleh `phase-1/src/dewatacalendar/rahinan.py`. Perhatikan bahwa engine
saat ini mengimplementasikan **12 id rahinan** (lihat indeks di
bawah) — bukan 24 hari Eiseman. Lihat
[phase-1/src/dewatacalendar/rahinan.py](https://github.com/consciousclarity/dewata-org/blob/main/phase-1/src/dewatacalendar/rahinan.py)
untuk implementasi saat ini.

## Daftar istilah

| istilah | kategori | status |
|---|---|---|
| [Rahinan](/id/rahinan/rahinan.md) | konsep | verified_source |
| [Purnama](/id/rahinan/purnama.md) | bulan purnama | implementation_definition |
| [Tilem](/id/rahinan/tilem.md) | bulan mati | implementation_definition |
| [Tumpek](/id/rahinan/tumpek.md) | siklus saptawara-pancawara | implementation_definition |
| [Kajeng Kliwon](/id/rahinan/kajeng-kliwon.md) | siklus | implementation_definition |
| [Anggara Kasih](/id/rahinan/anggara-kasih.md) | siklus | implementation_definition |
| [Buda Kliwon](/id/rahinan/buda-kliwon.md) | siklus | implementation_definition |
| [Buda Cemeng](/id/rahinan/buda-cemeng.md) | siklus | informational |
| [buda_wage](/id/rahinan/buda-wage.md) | id engine | implementation_definition |
| [buda_kliwon](/id/rahinan/buda-kliwon-id.md) | id engine | implementation_definition |
| [saniscara_umanis](/id/rahinan/saniscara-umanis.md) | id engine | implementation_definition |
| [tumpek_landep](/id/rahinan/tumpek-landep.md) | id engine | implementation_definition |
| [anggara_kliwon](/id/rahinan/anggara-kliwon.md) | id engine | implementation_definition |
| [redite_paing](/id/rahinan/redite-paing.md) | id engine | implementation_definition |
| [purnama (id)](/id/rahinan/purnama-id.md) | id engine | implementation_definition |
| [tilem (id)](/id/rahinan/tilem-id.md) | id engine | implementation_definition |
| [saraswati](/id/rahinan/saraswati.md) | id engine | implementation_definition |
| [galungan](/id/rahinan/galungan.md) | id engine | implementation_definition |
| [kuningan](/id/rahinan/kuningan.md) | id engine | implementation_definition |
| [nyepi](/id/rahinan/nyepi.md) | id engine | implementation_definition |

Catatan: halaman `buda_kliwon` (siklus manusia) dan
`buda_kliwon-id` (id engine) merujuk ke entri berbeda karena satu
adalah nama hari libur dan satu lagi adalah identifier string.
Lihat [tabel pemetaan](/id/rahinan/id-mapping.md) untuk
pemetaan semua 12 id ke nama hari.

Lebih lanjut: [Mesin kalender](/id/calendar/calendar-engine.md),
[Status aturan](/id/calendar/ruleset.md).
