---
status: informational
translation_review_status:
  id: needs_review
  en: needs_review
  ban: needs_review
last_reviewed: 2026-09-17
---

# About this wiki

## Scope

This wiki describes terminology and concepts in the dewata.org
project: the Balinese calendar engine, the evidence and dispute
workflow, the protocol and platform, and the customary /
institutional vocabulary.

The wiki is **not**:

- a replacement for the engine's API contract (that lives in
  `/dsp/v0.1/calendar/...` and is defined by `phase-1/src/dewatacalendar/dsp.py`),
- a chronological catalogue of customary practice (that is the
  role of the upcoming Banjar Cultural Index, `bci.dewata.org`),
- a tourism guide (the dewata project explicitly is not one — see
  `README_EN.md`),
- a source of calendar authority. **Authority flows from the
  customary sign-off process documented in
  `phase-1/docs/runbook/SIGNOFF.md`. The wiki surfaces and links
  to that process; it does not replace it.**

## What the wiki does

1. Lists the canonical names of the calendar's cycles (Pawukon
   and its 30 wuku, Saka and its 12 sasih, Wewaran with its 10
   concurrent cycles, Rahinan as currently emitted by the engine).
2. Explains the two-axis evidence model used in
   `phase-1/conformance/STATUS.json` (verification status ×
   reference eligibility) and how that model participates in
   ruleset promotion.
3. Surfaces the open disputes catalogued in
   `phase-1/docs/runbook/disputes.json`.
4. Names the release machinery (ruleset version, manifest,
   mirror, signed snapshot, immutable artefact).
5. Documents the platform's public surfaces
   (`api.dewata.org` for the executable API; `protocol.dewata.org`
   for the formal protocol; `bci.dewata.org` for the Banjar
   Cultural Index; `wiki.dewata.org` for this knowledge base).

## What the wiki requires from the reader

- The reader must understand that **three languages are intentional
  defaults**, not a translation pipeline. Bahasa Bali is the
  primary surface but ships with `pending_customary_review`
  status until a customary review of every Bahasa Bali record is
  complete.
- The reader must respect the **status badge** on each term page:
  a badge of `verified_source` is **not** a customary stamp; it is
  a statement about which repository file the page cites.

## Limits

The wiki does not currently support:

- arbitrary user contributions through the static site (we
  accept contributions through PRs against the repository; see
  [`CONTRIBUTING.md`](https://github.com/consciousclarity/dewata-org/blob/main/CONTRIBUTING.md)),
- an editor UI, login, or session,
- a feedback form.

The wiki is a static artefact built with MkDocs + Material and
pinned dependencies. We deliberately keep it read-only and
auditable.

## Revision cadence

This wiki is updated as part of the dewata.org release cadence
(see `phase-1/docs/runbook/RELEASE_v0.1.0.md` and `RULESET_VERSIONING.md`).
The metadata on every term page includes `last_reviewed` and
`reviewer`. **A page's `last_reviewed` value is the date the page
was added or last edited against the repository.**
