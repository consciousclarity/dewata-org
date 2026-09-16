---
status: informational
translation_review_status:
  id: needs_review
  en: needs_review
last_reviewed: 2026-09-17
---

# Calendar foundations

This section describes the Balinese calendar engine **as implemented**
in `phase-1/src/dewatacalendar/`. Per-page status is
`implementation_definition` unless noted otherwise.

## Contents

### Pawukon — the 210-day cycle

- [Pawukon](/en/calendar/pawukon.md) — 35 weeks × 6 days = 210 days.
- [Wuku](/en/calendar/wuku.md) — list of 30 wuku from the engine's i18n table.
- [210-day cycle](/en/calendar/210-day-cycle.md) — offset, epoch, phase.
- [Epoch / anchor](/en/calendar/epoch-anchor.md) —
  `pawukon.position_in_cycle == 1` on `1981-08-23` (Gregorian).
- [Phase offset](/en/calendar/phase-offset.md) — constant phase offset
  between the implementation and the referential sources.

### Saka (Bali)

- [Saka](/en/calendar/saka.md) — year, lunar months, nampih.
- [Sasih](/en/calendar/sasih.md) — 12 sasih, **`sasih_idx` is 1..12**.
- [Nampih Sasih](/en/calendar/nampih-sasih.md) — Desta / Sadha intercalation.
- [Pengalantaka](/en/calendar/pangunalatri.md) — 63-day cycle.

### Conversion

- [Gregorian date](/en/calendar/gregorian-date.md) — supported year range.
- [Inclusive date range](/en/calendar/inclusive-date-range.md) —
  inclusive `start/end` semantics from the public API.
- [Ruleset](/en/calendar/ruleset.md) — `pawukon-v0.4.1+saka-bali-v0.2.3+…`.
- [Calendar engine](/en/calendar/calendar-engine.md) — Python module layers.
- [Calendar conversion](/en/calendar/calendar-conversion.md).

### Wewaran

See [Wewaran](/en/calendar/wewaran.md) for an overview. Sub-pages per
cycle:

- [Ekawara](/en/calendar/wewaran/ekawara.md)
- [Dwiwara](/en/calendar/wewaran/dwiwara.md)
- [Triwara](/en/calendar/wewaran/triwara.md)
- [Caturwara](/en/calendar/wewaran/caturwara.md)
- [Pancawara](/en/calendar/wewaran/pancawara.md)
- [Sadwara](/en/calendar/wewaran/sadwara.md)
- [Saptawara](/en/calendar/wewaran/saptawara.md)
- [Astawara](/en/calendar/wewaran/astawara.md)
- [Sangawara](/en/calendar/wewaran/sangawara.md)
- [Dasawara](/en/calendar/wewaran/dasawara.md)
- [Urip](/en/calendar/wewaran/urip.md)
- [Jejepan](/en/calendar/wewaran/jejepan.md)
