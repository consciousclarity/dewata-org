---
status: informational
translation_review_status:
  id: needs_review
  en: needs_review
  ban: needs_review
last_reviewed: 2026-09-17
---

# Wiki dewata.org

Welcome. This wiki is a **companion** to the dewata.org project. It explains
terminology, the engine's behaviour, and how to read the dispute and evidence
records. The wiki is **descriptive**: it links to existing repository documents
and does not introduce new authority.

## What Dewata.org is

Dewata.org records the Balinese calendar — its cycles, observances, and customary
terms — as a verifiable, versioned data system. It is built for:

- **Banjar, Pura, and desa adat** that need machine-readable calendar data
- **Developers building applications** that consume the calendar API
- **Researchers and academics** studying Balinese calendar computation

The project records nyepi, odalan, and other customary observances.
It does **not** record traffic closures, construction schedules, or other
infrastructure information.

The platform has four surfaces:

| Surface | Purpose |
|---------|---------|
| `api.dewata.org` | Executable calendar API |
| `protocol.dewata.org` | Formal protocol specification |
| `bci.dewata.org` | Banjar Cultural Index *(planned)* |
| `wiki.dewata.org` | This knowledge base |

## How the components relate

The **engine** (`phase-1/src/dewatacalendar/`) computes the calendar. The **API**
exposes its output. The **wiki** explains the terms and concepts. The **evidence
workflow** tracks which calendar facts are verified, disputed, or still pending
customary review.

The wiki is not the authority — the repository source files are.

## How to look up a date

1. Use the API (`api.dewata.org`) to get a Gregorian date's Balinese calendar
   position.
2. Read the **Pawukon** and **Saka/Sasih** pages to understand what the result
   means.
3. Look up the specific **Rahinan** (observance) if one is present.
4. Check the term's **evidence status** badge to know whether it is a verified
   source, an implementation definition, or an open dispute.

## Sections

- [Kalender Bali — Calendar foundations](/id/calendar/) ·
  [English](/en/calendar/)
- [Rahinan dan observansi — Rahinan and observances](/id/rahinan/) ·
  [English](/en/rahinan/)
- [Tata kelola adat — Customary and institutional terms](/id/governance/) ·
  [English](/en/governance/)
- [Bukti dan tata kelola — Evidence and governance](/id/evidence/) ·
  [English](/en/evidence/)
- [Platform Dewata — Dewata platform](/id/platform/) ·
  [English](/en/platform/)
- [Wewaran — Day-classification cycles](/id/wewaran/) ·
  [English](/en/wewaran/)

## Languages

Three languages are available at the same canonical slug:

- **Bahasa Indonesia** (`/id/`) — canonical secondary reference.
- **English** (`/en/`) — explanatory / academic reference.
- **Bahasa Bali** (`/ban/`) — primary surface, marked
  `pending_customary_review` until customary sign-off is complete.

If a Bahasa Bali page shows `pending_customary_review`, it means the page
content is not yet written — the Bahasa Indonesia or English page carries the
definition.

## Limits of this wiki

- **Not a source of calendar authority.** It summarises and links to repository
  files. Authority flows from the customary sign-off process in
  `phase-1/docs/runbook/SIGNOFF.md`.
- **Not a record of infrastructure or traffic closures.** The project records
  customary observances (nyepi, odalan, and similar). It does not record
  road closures, construction, or other non-calendar events.
- **Not a corpus.** Academic sources are tracked in
  `phase-1/conformance/STATUS.json` and cited per page.
- **Not a live record of open disputes.** Those live in
  `phase-1/docs/runbook/disputes.json`.

## Related repository pages

- [`README_EN.md`](https://github.com/consciousclarity/dewata-org/blob/main/README_EN.md)
- [`README_ID.md`](https://github.com/consciousclarity/dewata-org/blob/main/README_ID.md)
- [`README_BAL.md`](https://github.com/consciousclarity/dewata-org/blob/main/README_BAL.md)
- [`ARCHITECTURE.md`](https://github.com/consciousclarity/dewata-org/blob/main/ARCHITECTURE.md)
- [`docs/PROTOCOL.md`](https://github.com/consciousclarity/dewata-org/blob/main/docs/PROTOCOL.md)
