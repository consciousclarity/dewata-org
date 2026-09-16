---
status: informational
translation_review_status:
  id: needs_review
  en: needs_review
  ban: needs_review
last_reviewed: 2026-09-17
---

# Wiki dewata.org (knowledge base)

Welcome. This wiki is a **companion** to the dewata.org project. It
explains terminology, the engine's behaviour, and how to read the
dispute and evidence records. The wiki is **descriptive**: it links
to existing repository documents and does not introduce new
authority.

## Languages

The wiki is structured so that every term page exists in three
languages at the same canonical slug:

- Bahasa Indonesia (`id/`) — the canonical secondary reference.
- English (`en/`) — explanatory / academic third reference.
- Bahasa Bali (`ban/`) — the primary surface, but `pending_customary_review`.

If a Balinese spelling has not been verified through the engine's
`phase-1/src/dewatacalendar/i18n.py` table, the Bahasa Bali page
ships as a navigation stub with status `pending_customary_review`.

## Sections

- [Kalender bali (id)](id/calendar/index.md) ·
  [Calendar foundations (en)](en/calendar/index.md)
- [Rahinan dan observansi (id)](id/rahinan/index.md) ·
  [Rahinan and observances (en)](en/rahinan/index.md)
- [Tata kelola adat (id)](id/governance/index.md) ·
  [Customary and institutional terms (en)](en/governance/index.md)
- [Bukti dan tata kelola (id)](id/evidence/index.md) ·
  [Evidence and governance (en)](en/evidence/index.md)
- [Platform dewata (id)](id/platform/index.md) ·
  [Dewata platform (en)](en/platform/index.md)

## Limits of the wiki

- The wiki is not a source of calendar authority. It summarises and
  links to existing files in the repository.
- The wiki does not claim customary authority for any Balinese
  translation or ceremonial meaning. See
  [`SIGNOFF.md`](https://github.com/consciousclarity/dewata-org/blob/main/phase-1/docs/runbook/SIGNOFF.md)
  for the customary sign-off workflow.
- The wiki does not contain tourism-oriented language. The dewata
  project records custom and customary ceremony; it is **not** a
  travel guide.

## Related repository pages

- [`README_EN.md`](https://github.com/consciousclarity/dewata-org/blob/main/README_EN.md)
- [`README_ID.md`](https://github.com/consciousclarity/dewata-org/blob/main/README_ID.md)
- [`README_BAL.md`](https://github.com/consciousclarity/dewata-org/blob/main/README_BAL.md)
- [`ARCHITECTURE.md`](https://github.com/consciousclarity/dewata-org/blob/main/ARCHITECTURE.md)
- [`docs/PROTOCOL.md`](https://github.com/consciousclarity/dewata-org/blob/main/docs/PROTOCOL.md)
