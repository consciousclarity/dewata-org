"""build a coverage report from the wiki's term pages.

Counts:
  - pages by language (id, en, ban)
  - pages by status (verified_source, implementation_definition, ...)
  - pages by category (calendar, governance, evidence, platform, ...)
  - disputed pages
  - pages with no source citation
  - translation-review-status tally per language

Output: `wiki/build-artifacts/coverage.json` (machine readable)
and emits a summary to stdout.

Used by the test suite to detect coverage regressions.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARTIFACTS = ROOT / "build-artifacts"
ARTIFACTS.mkdir(exist_ok=True)


def iter_term_pages():
    """every page with a YAML front-matter carrying `canonical_slug`
    counts as a term page. We also count the `<lang>/index.md`
    page of each language."""
    for path in sorted(DOCS.rglob("*.md")):
        rel = path.relative_to(DOCS)
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        end = text.find("\n---\n", 4)
        if end == -1:
            continue
        try:
            meta = yaml.safe_load(text[4:end])
        except yaml.YAMLError:
            continue
        if not isinstance(meta, dict):
            continue
        # Term pages have `canonical_slug`. The Bahasa Bali stubs
        # do not (by design — they are navigation pointers, not
        # term records). Count stubs separately under their own
        # status label.
        if "canonical_slug" not in meta:
            continue
        yield rel, meta


def lang_of(rel: Path) -> str:
    parts = rel.parts
    if parts and parts[0] in {"ban", "id", "en"}:
        return parts[0]
    return "(other)"


def _iter_every_page(rel: Path) -> str:
    return str(rel.parts[0]) if rel.parts else "(root)"


def main() -> int:
    by_lang = Counter()
    by_status = Counter()
    by_category = Counter()
    by_translation_review = Counter()  # (lang, status)
    disputed = []
    no_source = []

    # term records (front-matter with `canonical_slug`)
    for rel, meta in iter_term_pages():
        lang = lang_of(rel)
        by_lang[lang] += 1
        if "status" in meta:
            by_status[meta["status"]] += 1
        if "category" in meta:
            by_category[meta["category"]] += 1
        trs = meta.get("translation_review_status") or {}
        if isinstance(trs, dict):
            for k, v in trs.items():
                by_translation_review[(k, v)] += 1
        if meta.get("status") == "disputed":
            disputed.append(str(rel))
        if not (meta.get("source_citations") or []):
            no_source.append(str(rel))

    # Bahasa Bali navigation stubs. These have front-matter with
    # `status: pending_customary_review` but no `canonical_slug`,
    # so they are not term records but they ARE pages we ship.
    stub_count_by_lang = Counter()
    for path in sorted(DOCS.rglob("*.md")):
        rel = path.relative_to(DOCS)
        if rel.parts and rel.parts[0] in {"ban", "id", "en"}:
            lang_dir = rel.parts[0]
        else:
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        end = text.find("\n---\n", 4)
        if end == -1:
            continue
        try:
            meta = yaml.safe_load(text[4:end])
        except yaml.YAMLError:
            continue
        if not isinstance(meta, dict):
            continue
        if "canonical_slug" in meta:
            continue  # already counted above
        if meta.get("status") == "pending_customary_review":
            stub_count_by_lang[lang_dir] += 1
            by_lang[lang_dir] += 1

    summary = {
        "page_count": sum(by_lang.values()),
        "by_language": dict(by_lang),
        "pending_customary_review_stubs_by_language": dict(stub_count_by_lang),
        "by_status": dict(by_status),
        "by_category": dict(by_category),
        "by_translation_review_status": {
            f"{lang}/{status}": count
            for (lang, status), count in by_translation_review.items()
        },
        "disputed_pages": disputed,
        "pages_without_source_citation": no_source,
    }

    out = ARTIFACTS / "coverage.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {out}")
    print(f"page_count = {summary['page_count']}")
    print(f"disputed   = {len(disputed)}")
    print(f"no_source  = {len(no_source)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
