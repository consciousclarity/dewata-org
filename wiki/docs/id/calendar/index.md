---
status: informational
translation_review_status:
  id: needs_review
  en: needs_review
last_reviewed: 2026-09-17
---

# Bagian Kalender

Subbagian di bagian ini menjelaskan mesin kalender bali **sebagaimana
diimplementasikan** oleh `phase-1/src/dewatacalendar/`. Status setiap
halaman adalah `implementation_definition` kecuali ada catatan lain.

## Daftar isi

### Pawukon — siklus 210 hari

- [Pawukon](/id/calendar/pawukon.md) — siklus 35 minggu × 6 hari = 210 hari.
- [Wuku](/id/calendar/wuku.md) — daftar 30 wuku dan mesin-i18n.
- [Siklus 210 hari](/id/calendar/210-day-cycle.md) — offset, epoch, fase.
- [Epoch/anchor](/id/calendar/epoch-anchor.md) — `pawukon.position_in_cycle == 1`
  pada `1981-08-23` (Gregorian).
- [Phase offset](/id/calendar/phase-offset.md) — konstanta offset fase
  antara implementasi dan sumber referensional.

### Saka (Bali)

- [Saka](/id/calendar/saka.md) — tahun, bulan lunar, nampih.
- [Sasih](/id/calendar/sasih.md) — 12 sasih, **`sasih_idx` adalah 1..12**.
- [Nampih Sasih](/id/calendar/nampih-sasih.md) — interkalasi Desta / Sadha.
- [Pengalantaka](/id/calendar/pangunalatri.md) — siklus 63 hari.

### Konversi

- [Tanggal Gregorian](/id/calendar/gregorian-date.md) — batasan tahun.
- [Rentang tanggal inklusif](/id/calendar/inclusive-date-range.md) —
  perilaku `start/end` inklusif dari API.
- [Ruleset](/id/calendar/ruleset.md) — `pawukon-v0.4.1+saka-bali-v0.2.3+...`.
- [Mesin kalender](/id/calendar/calendar-engine.md) — lapisan-lapisan
  Python.
- [Konversi kalender](/id/calendar/calendar-conversion.md) —

### Wewaran

Lihat [Wewaran](/id/calendar/wewaran.md) untuk pengantar umum.
Subhalaman untuk setiap siklus:

- [Ekawara](/id/calendar/wewaran/ekawara.md)
- [Dwiwara](/id/calendar/wewaran/dwiwara.md)
- [Triwara](/id/calendar/wewaran/triwara.md)
- [Caturwara](/id/calendar/wewaran/caturwara.md)
- [Pancawara](/id/calendar/wewaran/pancawara.md)
- [Sadwara](/id/calendar/wewaran/sadwara.md)
- [Saptawara](/id/calendar/wewaran/saptawara.md)
- [Astawara](/id/calendar/wewaran/astawara.md)
- [Sangawara](/id/calendar/wewaran/sangawara.md)
- [Dasawara](/id/calendar/wewaran/dasawara.md)
- [Urip](/id/calendar/wewaran/urip.md)
- [Jejepan](/id/calendar/wewaran/jejepan.md)
