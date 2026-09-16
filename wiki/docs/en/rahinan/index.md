---
status: informational
translation_review_status:
  en: needs_review
  ban: pending_customary_review
  id: needs_review
last_reviewed: 2026-09-17
---

# Rahinan and observances

This section describes the named observation days the engine emits.
Note that the current engine implements **12 rahinan IDs** (see the
index below) — not the 24 days cited in Eiseman 1989. See
[phase-1/src/dewatacalendar/rahinan.py](https://github.com/consciousclarity/dewata-org/blob/main/phase-1/src/dewatacalendar/rahinan.py)
for the current implementation.

## Index

| term | category | status |
|---|---|---|
| [Rahinan](/en/rahinan/rahinan.md) | concept | verified_source |
| [Purnama](/en/rahinan/purnama.md) | full moon | implementation_definition |
| [Tilem](/en/rahinan/tilem.md) | new moon | implementation_definition |
| [Tumpek](/en/rahinan/tumpek.md) | saptawara-pancawara pattern | implementation_definition |
| [Kajeng Kliwon](/en/rahinan/kajeng-kliwon.md) | pattern | implementation_definition |
| [Anggara Kasih](/en/rahinan/anggara-kasih.md) | pattern | implementation_definition |
| [Buda Kliwon](/en/rahinan/buda-kliwon.md) | pattern | implementation_definition |
| [Buda Cemeng](/en/rahinan/buda-cemeng.md) | pattern | informational |
| [buda_wage](/en/rahinan/buda-wage.md) | engine id | implementation_definition |
| [buda_kliwon](/en/rahinan/buda-kliwon-id.md) | engine id | implementation_definition |
| [saniscara_umanis](/en/rahinan/saniscara-umanis.md) | engine id | implementation_definition |
| [tumpek_landep](/en/rahinan/tumpek-landep.md) | engine id | implementation_definition |
| [anggara_kliwon](/en/rahinan/anggara-kliwon.md) | engine id | implementation_definition |
| [redite_paing](/en/rahinan/redite-paing.md) | engine id | implementation_definition |
| [purnama (id)](/en/rahinan/purnama-id.md) | engine id | implementation_definition |
| [tilem (id)](/en/rahinan/tilem-id.md) | engine id | implementation_definition |
| [saraswati](/en/rahinan/saraswati.md) | engine id | implementation_definition |
| [galungan](/en/rahinan/galungan.md) | engine id | implementation_definition |
| [kuningan](/en/rahinan/kuningan.md) | engine id | implementation_definition |
| [nyepi](/en/rahinan/nyepi.md) | engine id | implementation_definition |

Note that `buda_kliwon` (human name) and `buda_kliwon-id` (engine
identifier) refer to different entries — one is the day-name, one
is the string emitted by the engine. See
[id-mapping table](/en/rahinan/id-mapping.md) for the mapping of
all 12 engine ids to human names.

Further reading: [Calendar engine](/en/calendar/calendar-engine.md),
[Ruleset](/en/calendar/ruleset.md).
