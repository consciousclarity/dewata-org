# Wiki foundation — architectural separation, content policy, and draft repo

This directory is the repository-first foundation for `wiki.dewata.org`.
The wiki is **only** a knowledge base. It is not a source of calendar
authority. Three commitments keep that line clear.

## 1. Architectural separation (the wiki is not a calendar)

| surface | role | mutable in this PR? |
|---|---|---|
| `wiki.dewata.org` (this directory, when deployed) | explanatory knowledge base for humans | **this PR** writes the source |
| `protocol.dewata.org` | formal protocol and normative specifications | no |
| `api.dewata.org` | executable API contracts (`/dsp/v0.1/calendar/...`) | no |
| `phase-1/conformance/STATUS.json` | primary technical record of corpora | no |
| `phase-1/docs/runbook/CHANGELOG.md`, `RULESET_VERSIONING.md`, `SIGNOFF.md` | policy records | no |
| `phase-1/docs/audit/*.md` | audit records | no |

The wiki **summarises and links to** the above. It is not a parallel
source of authority. Each wiki page is required to cite a real
repository file (the "source citation" metadata field). A wiki page
without a verifiable citation is not promoted into the index.

## 2. Content policy — explicit (do not soften)

The wiki uses these status values exactly:

- `verified_source` — the supporting repository file is present,
  fetched, and the citation matches the page content.
- `eligible_reference` — the corpus or source carries
  `reference_eligibility: ELIGIBLE` in `phase-1/conformance/STATUS.json`
  *or* the document is otherwise the cited repository policy file.
- `implementation_definition` — the page describes the behaviour of
  the dewata calendar engine code in this repository, as of the
  recorded ruleset version. Status applies to the *engine*, not to
  customary correctness.
- `customary_attestation_required` — the page describes a Balinese
  customary object whose customary meaning must be attested by a
  customary authority before this wiki page can drop the badge.
  See `wiki/docs/governance/sigoff.md` in this directory.
- `disputed` — a `disputes.json` entry is cited and the page must
  show that dispute id and link the repository record.
- `unresolved` — the page describes an open question with no current
  implementation or source.
- `deprecated` — see `phase-1/docs/runbook/CHANGELOG.md`.
- `informational` — explanatory material with no claim on ruleset or
  customary correctness (e.g. navigation pages).

The wiki **forbids** the following phrases anywhere in `wiki/docs/`:

- "ground truth"
- "canonical cultural truth"
- "approved" (in the sense of customary approval — see the exception
  for *ruleset* approval, which uses the term "candidate ruleset"
  and references `RULESET_VERSIONING.md`)
- "definitive"
- "settled" (in the customary sense — see exception for *evidence*
  "settled" records in `phase-1/conformance/STATUS.json`)

This rule is enforced by `wiki/tests/test_no_authority_phrases.py`.

## 3. Languages

- Bahasa Bali — `ban/` — primary. Spellings come from
  `phase-1/src/dewatacalendar/i18n.py` and only those. Where
  canonical Balinese text is not in that table, the page is
  shipped **with the Indonesian or English variant only**, and the
  page header carries `translation_status: pending_customary_review`.
  We do not invent Balinese.
- Bahasa Indonesia — `id/` — secondary. Spellings come from the
  existing `README_ID.md` and `phase-1/src/dewatacalendar/i18n.py`
  Indonesian labels.
- English — `en/` — explanatory / academic. Never appears in any
  user-facing UI. Spellings follow the citations' original
  Romanisation where they exist (e.g. "Coma" / "Soma" are preserved
  per the dispute record rather than coerced).

URL routes:

```
/ban/<canonical-slug>/          (Basa Bali)
/id/<canonical-slug>/           (Bahasa Indonesia)
/en/<canonical-slug>/           (English)
/ban/governance/<...>/           (non-term pages, in Basa Bali)
/id/governance/<...>/           (same in Indonesian)
/en/governance/<...>/           (same in English)
```

Cross-language links: each term page carries a footer block of
three links — `🇧🇦 [ban]/[slug] · 🇮🇩 [id]/[slug] · 🇬🇧 [en]/[slug]` —
so a reader of any language can find the other two.

## 4. Definition record structure (machine-checked)

A term page is a Markdown file with a single YAML front-matter
block carrying this schema (all fields required, all enum values
literal):

```yaml
---
canonical_term: "..."           # the human-readable canonical name in Basa Bali
canonical_slug: "..."           # URL-safe, kebab-case, unique across the wiki
category: calendar              # one of the 5 categories in §5 of the brief
language_variants:
  ban: "..."
  id: "..."
  en: "..."
alternative_spellings:
  - "..."
  - "..."
short_definition: "..."         # <= 240 chars
detailed_explanation: >-         # multi-paragraph, unlimited
  ...
dewata_specific_meaning: "..."  # how dewata uses the term, distinct from general meaning
affects: [calculation, governance, evidence, display-only]   # cross-product subset; "display-only" is exclusive with the others
examples:
  - "..."
related_terms: [...]            # slugs only
source_citations:               # each citation is a repo path or an external URL with a fetched-quote hash
  - path: "phase-1/src/dewatacalendar/saka.py"
    role: "implementation"
  - path: "phase-1/conformance/STATUS.json"
    role: "policy"
evidence_status: implementation_definition
dispute_ids: []                 # 'DISPUTE-...' IDs from phase-1/docs/runbook/disputes.json, when relevant
customary_review_status: pending_customary_review
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
ruleset_version_relevance: "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"
last_reviewed: 2026-09-17
reviewer: "[[ai-trail]]/wiki-foundation-20260917"
status: verified_source         # top-level status, see §2 of this doc
---

```

The required-metadata rule is enforced by
`wiki/tests/test_required_metadata.py`.

## 5. Initial information architecture

Sections at `wiki/docs/<lang>/...`:

- **Calendar foundations** — Pawukon, Wuku, 210-day cycle, epoch/anchor,
  phase offset, Saka, Sasih, Nampih Sasih, Pengalantaka, Gregorian
  date, inclusive date range, ruleset, calendar engine, calendar
  conversion, Wewaran (Ekawara through Dasawara), Urip, Jejepan.
- **Rahinan and observances** — Rahinan, Purnama, Tilem, Tumpek,
  Kajeng Kliwon, Anggara Kasih, Buda Kliwon, Buda Cemeng, plus every
  rahinan id the current engine actually emits (12 ids as of
  2026-09-16).
- **Customary and institutional terms** — adat, desa adat, desa
  dinas, banjar, pura, pemangku, bendesa, klian adat, pecalang,
  customary authority, customary sign-off, jurisdiction,
  attestation.
- **Evidence and governance** — evidence, provenance, corpus,
  conformance corpus, verification status, reference eligibility,
  eligible claim, implementation observation, dispute, blocking
  dispute, resolution, accepted rule, candidate ruleset, ruleset
  promotion, cultural review, bibliographic review, raw comparison,
  normalised comparison, phase normalisation.
- **Dewata platform** — Dewata, DSP, public API, API endpoint,
  ruleset version, computed / registered / predicted / verified,
  visibility tier (public / banjar visibility / desa-adat visibility
  / restricted / private), mirror, signed snapshot, release manifest,
  checksum / SHA-256, JSON, JSONL, immutable artifact, candidate
  release, production release.

Each section has an `index.md` listing the term pages and their
status. The root `index.md` is the A-Z index.

## 6. Source policy

- Citation discipline: every term page must cite at least one
  repository file or an external source. No invented citations.
- Distinguish in the prose: quotation (verbatim, with citation),
  paraphrase (also cited), implementation behaviour (cite the
  implementation commit / hash), inference (call it out as inference).
- Do not copy restricted or unlicensed source text; cite the
  page or quote a clearly-marked snippet.
- Do not treat a code constant (e.g. `RULESET_VERSION`) as
  customary authority. Code constants are `implementation_definition`,
  never `customary_authority`.
- All existing repository disputes must be preserved in the wiki:
  see `wiki/docs/<lang>/disputes.html` (auto-generated from
  `phase-1/docs/runbook/disputes.json`). The wiki never *resolves*
  a dispute.

## 7. Source register

Every term page's `source_citations` is also dumped into
`wiki/build-artifacts/source-register.json` by
`scripts/build_source_register.py`. The register lists every
citation across all term pages, deduplicated, with a count of
pages referencing each citation. Use:

```
python -m wiki.scripts.build_source_register
```

Output: `wiki/build-artifacts/source-register.json`.

## 8. Static site rendering

- Renderer: MkDocs + Material theme.
- Configuration: `wiki/mkdocs.yml`.
- Pinned dependencies: `wiki/requirements.txt`. Reproducible install:
  `python -m venv /tmp/wiki-venv && source … && pip install -r requirements.txt`
  produces a venv that builds the same site byte-for-byte (within
  MkDocs Material's documented non-determinism surface).
- Build command: `mkdocs build --config-file wiki/mkdocs.yml --site-dir wiki/site --strict`.
- Preview command: `mkdocs serve --config-file wiki/mkdocs.yml`.

The static renderer is local. The deployment plan is a separate
document at `wiki/DEPLOYMENT_PLAN.md` and is **not executed** by
this PR.

## 9. Build mode and accessibility

- Mobile-first responsive layout (Material default).
- Search ships via `mkdocs-material[search]` plugin (offline index,
  no third-party tracking).
- No analytics. No scripts loaded from third parties. No
  CDN-loaded fonts or trackers.
- No database. No server-side application. The static build
  output is sufficient as a deploy target.

## 10. What is *not* in this PR

- DNS records at Cloudflare for `wiki.dewata.org`.
- Caddyfile changes.
- systemd unit changes.
- A custom MkDocs Material build that adds telemetry. (We use
  the upstream theme without modification.)
- A non-trivial set of term entries for terms *not yet* in scope
  per §5. They are added in follow-up PRs once their source policy
  is satisfied.

## 11. Summary — what this PR adds to the repository

- `wiki/mkdocs.yml` — site config.
- `wiki/requirements.txt` — pinned dependencies.
- `wiki/Makefile` — local-build convenience.
- `wiki/docs/` — three-language content tree.
- `wiki/tests/` — automated checks (the 8 requirements in §8 of
  the work-package brief).
- `wiki/scripts/` — source-register and coverage builds.
- `wiki/DEPLOYMENT_PLAN.md` — a separate, unexecuted deployment
  plan for `wiki.dewata.org`.

End of policy. Build instructions below.

```
python -m venv /tmp/wiki-venv
/tmp/wiki-venv/bin/pip install --upgrade pip
/tmp/wiki-venv/bin/pip install -r wiki/requirements.txt
/tmp/wiki-venv/bin/python -m mkdocs build --config-file wiki/mkdocs.yml --site-dir wiki/site --strict
/tmp/wiki-venv/bin/python -m pytest wiki/tests -q
```

## 12. What is in this draft of the wiki

This section lists what ships in this draft PR. It is generated
from `wiki/build-artifacts/coverage.json` and a directory listing.

```
wiki/
├── README.md                    # this file (architecture + policy)
├── DEPLOYMENT_PLAN.md           # unexecuted deployment plan for wiki.dewata.org
├── mkdocs.yml                   # generated by scripts/build_mkdocs_config.py
├── requirements.txt             # mkdocs 1.6.1, mkdocs-material 9.5.49, pyyaml 6.0.1, pygments 2.19.2
├── Makefile                     # venv / install / build / check / clean targets
├── docs/                        # the content tree
│   ├── index.md                 # wiki home (one per repo, English)
│   ├── about.md                 # what the wiki is and is not
│   ├── contributing.md          # PR and sign-off workflow
│   ├── id/                      # 100 Indonesian term pages + section indexes
│   ├── en/                      # 101 English term pages + section indexes
│   └── ban/                     # 101 Bahasa Bali navigation stubs (status: pending_customary_review)
├── scripts/
│   ├── emit_bahasa_bali_indexes.py
│   ├── emit_term_pages.py
│   ├── build_mkdocs_config.py
│   ├── build_source_register.py
│   ├── build_coverage_report.py
├── tests/
│   ├── test_metadata.py         # the 8 automated checks from §8 of the brief
│   └── test_build_reproducibility.py
└── build-artifacts/             # generated; both committed to the repo for review
    ├── coverage.json
    └── source-register.json
```

### Term-page coverage (this draft)

| category | term pages |
|---|---|
| Calendar foundations | 16 (Pawukon, Wuku, 210-day-cycle, epoch-anchor, phase-offset, Saka, Sasih, Nampih-Sasih, Pengalantaka, Gregorian-date, inclusive-date-range, Ruleset, calendar-engine, calendar-conversion, Wewaran, plus 12 Wewaran sub-cycle pages for Ekawara through Urip + Jejepan) |
| Rahinan and observances | 21 (every rahinan id emitted by the engine, plus the human-day names: Rahinan, Purnama, Tilem, Tumpek, Kajeng-Kliwon, Anggara-Kasih, Buda-Kliwon, Buda-Cemeng, plus an id-mapping reference page) |
| Customary and institutional terms | 13 |
| Evidence and governance | 18 |
| Dewata platform | 24 |

Each term page exists at the same canonical slug in three
languages, except Bahasa Bali pages which ship as navigation stubs
pending customary review.

### Built artefacts (regenerated by `make artifacts`)

- `wiki/build-artifacts/coverage.json` — machine-readable tally of
  page_count, by_language, by_status, by_category, by
  translation_review_status, and unresolved pages.
- `wiki/build-artifacts/source-register.json` — list of every
  citation path cited across the wiki, deduplicated, with usage
  count.

### What is deliberately NOT in this draft

- Bahasa Bali term-page bodies. The Bahasa Bali pages are
  navigation stubs; the customary review is the prerequisite for
  carrying Bahasa Bali spelled text.
- The `wiki.dewata.org` Caddy route, DNS record, Cloudflare
  configuration, and production deployment. See
  `DEPLOYMENT_PLAN.md` for the plan; no part of it is executed by
  this PR.
