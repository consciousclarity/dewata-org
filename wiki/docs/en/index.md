---
status: informational
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
last_reviewed: 2026-09-17
---

# Dewata.org wiki (home)

> **Translation status.** The Bahasa Bali section currently ships
> as a navigation stub with status `pending_customary_review`. The
> Indonesian and English sections below are the canonical explanation
> surface until a customary review of the Bahasah Bali transliterations
> completes. Full policy: [`wiki/README.md`](../../wiki/README.md) §3
> ("Bahasa Bali — primary").

This wiki explains the terms used in the dewata.org project: the
Balinese calendar engine (Pawukon, Saka, Wewaran, Rahinan), the
customary vocabulary (banjar, pura, desa adat, pemangku), the
evidence and governance workflow (STATUS, dispute, sign-off),
and the platform itself (DSP, API, SHA-256 checksums).

## Principles in one paragraph

- **explanatory, not authoritative.** This wiki restates and links
  to documents that already exist in the repository; it does not
  introduce new authority. The status of this page is
  `informational`.
- **Balinese spellings are taken from
  `phase-1/src/dewatacalendar/i18n.py`.** Words not present in that
  table carry `pending_customary_review` and are not invented.
- **not operational.** This wiki is descriptive. For operational
  guidance, see `phase-1/docs/runbook/`.

## Sections

- [Calendar foundations](/en/calendar/) — Pawukon, Saka, Wewaran,
  Rahinan.
- [Customary and institutional terms](/en/governance/) — Banjar,
  Pura, Desa adat, Pemangku, Bendesa, Klian adat, Pecalang, Sign-off.
- [Evidence and governance](/en/evidence/) — STATUS.json, dispute,
  phase normalisation, reference eligibility.
- [Dewata platform](/en/platform/) — DSP, public API, visibility
  tiers, releases.

## A–Z index

See [`/en/a-z/index.md`](/en/a-z/) for every term with one entry
per category.

Project-level context: [`README_EN.md` at repo root](../../README_EN.md)
and [`ARCHITECTURE.md`](../../ARCHITECTURE.md).
