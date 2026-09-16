---
status: informational
translation_review_status:
  id: needs_review
  en: needs_review
  ban: needs_review
last_reviewed: 2026-09-17
---

# Contributing to this wiki

This wiki shares the contribution model of the dewata.org
project.

## Who contributes

| audience | acceptable contribution surface | forbidden artefact |
|---|---|---|
| Banjar / Pura / individuals | `contributing.md` describes channel-based piodalan records | wiki edits |
| Technical contributors | PRs against this repository (see below) | direct edits to the live site |
| Akademisi | PRs against the corpus / dataset snapshot directory | wiki edits bypassing customary review |

The wiki does not accept submissions through the static site
itself. If you have material that should live on the wiki, the
right path is to open a PR against the repository. The PR review
must surface customary sign-off where the contribution touches
Balinese-language content.

## Conventional commit markers

The wiki shares the conventional-commit convention used by the
rest of the repository:

| scope | commit-type | example |
|---|---|---|
| `wiki(term)` new term page | `feat(wiki): add <slug>` | `feat(wiki): add banjar term` |
| `wiki(content)` content edit only | `docs(wiki): update piodalan entry` | |
| `wiki(build)` static site pipeline | `chore(wiki): pin mkdocs 1.6.1` | |
| `wiki(evidence)` add a citation pointer | `docs(wiki): cite <path>` | |

A PR cannot land if any of the automated checks fail:

- metadata schema validation,
- canonical-slug kebab-case rule,
- required translation-review-status fields,
- prohibited authority-bearing phrases,
- broken internal links (`mkdocs build --strict`).

## How customary sign-off interacts with the wiki

The wiki surfaces `translation_review_status.ban =
pending_customary_review` for every Bahasa Bali page until a
customary review documents the canonical spelling against an
existing repository record (`README_BAL.md` or
`phase-1/src/dewatacalendar/i18n.py`).

To advance the status, a customary reviewer signs a record in
`phase-1/docs/runbook/SIGNOFF.md` that ties the spelling to a
specific page slug, then a non-customary PR updates the page's
metadata to the new status.

**Customary review does not happen via wiki comments.** It
happens via the documented sign-off process. The wiki role is to
make that process visible — not to bypass it.

## What a good contribution looks like

A PR titled `feat(wiki): add <slug>` should include:

1. one Markdown file per language (`docs/ban/<slug>.md`,
   `docs/id/<slug>.md`, `docs/en/<slug>.md`) with the required
   metadata (see `README.md` §4) and a `canonical_slug` that
   matches between languages;
2. at least one real citation in `source_citations` pointing at
   an existing repository file;
3. an entry in the relevant section's `index.md` (or a new
   section if the term doesn't fit an existing one);
4. no `disputed` status unless the page references an existing
   dispute id in `phase-1/docs/runbook/disputes.json`;
5. for Bahasa Bali: spelling **only** from
   `phase-1/src/dewatacalendar/i18n.py` or `README_BAL.md`. Any
   spelling outside that set must carry
   `language_variants.ban.status: pending_customary_review`.

The PR description should state which customary author reviewed
(if applicable) and which repository files were consulted as
sources. Pure paraphrase or pure inference is allowed; both
should be flagged in `source_citations[].role` and in body prose.

## Local preview

```bash
mkdocs serve --config-file wiki/mkdocs.yml
# default: http://127.0.0.1:8000
```

The Makefile in `wiki/Makefile` provides shortcuts: `make venv`,
`make install`, `make build`, `make strict-build`, `make check`,
`make artifacts`, and `make clean`.

## Where the wiki *doesn't* go

The wiki does not replace:

- `phase-1/docs/runbook/SIGNOFF.md` (customary sign-off),
- `phase-1/docs/runbook/CHANGELOG.md` (changelog),
- `phase-1/conformance/STATUS.json` (corpus authority),
- `phase-1/docs/runbook/disputes.json` (open disputes).

These are the source-of-truth documents. The wiki is the
explanatory **wrapper** around them. **Always edit the source-of-truth
first; the wiki follows.**
