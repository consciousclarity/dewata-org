"""tests for the wiki foundation.

These tests run against the *source* tree under `wiki/docs/`.
The static-site build (mkdocs) is verified separately by `make build`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DOCS = ROOT / "docs"
ARTIFACTS = ROOT / "build-artifacts"
ARTIFACTS.mkdir(exist_ok=True)


# ───────────────────────────── shared helpers ───────────────────────────


def iter_term_pages() -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(DOCS.rglob("*.md")):
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
        if not isinstance(meta, dict) or "canonical_slug" not in meta:
            continue
        out.append((path, meta))
    return out


@pytest.fixture(scope="module")
def pages():
    return iter_term_pages()


# ───────────────────────────── required metadata ──────────────────────────


REQUIRED_FIELDS = {
    "canonical_term",
    "canonical_slug",
    "category",
    "language_variants",
    "short_definition",
    "detailed_explanation",
    "dewata_specific_meaning",
    "affects",
    "source_citations",
    "evidence_status",
    "customary_review_status",
    "translation_review_status",
    "ruleset_version_relevance",
    "last_reviewed",
    "status",
}

ALLOWED_STATUS = {
    "verified_source",
    "eligible_reference",
    "implementation_definition",
    "customary_attestation_required",
    "disputed",
    "unresolved",
    "deprecated",
    "informational",
}

ALLOWED_CATEGORIES = {
    "calendar",
    "rahinan",
    "governance",
    "evidence",
    "platform",
}

ALLOWED_AFFECTS = {"calculation", "governance", "evidence", "display-only"}


def test_each_term_page_has_required_fields(pages):
    failures = []
    for path, meta in pages:
        missing = REQUIRED_FIELDS - set(meta.keys())
        if missing:
            failures.append((str(path.relative_to(DOCS)), sorted(missing)))
    assert not failures, "missing required metadata:\n" + "\n".join(
        f"  {p}: {m}" for p, m in failures
    )


def test_canonical_slug_is_kebab_case_and_unique(pages):
    seen = {}
    for path, meta in pages:
        slug = meta.get("canonical_slug", "")
        assert re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug), (
            f"{path.relative_to(DOCS)}: non-kebab slug {slug!r}"
        )
        # canonical_slug is the term-name and is shared across
        # the three language files. We assert it is unique per
        # *language* only.
        lang_dir = path.relative_to(DOCS).parts[0]
        keyed = (lang_dir, slug)
        if keyed in seen:
            pytest.fail(
                f"duplicate canonical_slug {slug!r} in language {lang_dir!r}: "
                f"{path.relative_to(DOCS)} and {seen[keyed]}"
            )
        seen[keyed] = str(path.relative_to(DOCS))


def test_status_values_are_in_enum(pages):
    failures = []
    for path, meta in pages:
        s = meta.get("status")
        if s not in ALLOWED_STATUS:
            failures.append((str(path.relative_to(DOCS)), s))
    assert not failures, "unrecognised status values:\n" + "\n".join(
        f"  {p}: {s}" for p, s in failures
    )


def test_categories_are_in_enum(pages):
    failures = []
    for path, meta in pages:
        c = meta.get("category")
        if c not in ALLOWED_CATEGORIES:
            failures.append((str(path.relative_to(DOCS)), c))
    assert not failures, "unrecognised categories:\n" + "\n".join(
        f"  {p}: {c}" for p, c in failures
    )


def test_affects_values_are_in_enum(pages):
    failures = []
    for path, meta in pages:
        a = meta.get("affects") or []
        bad = [x for x in a if x not in ALLOWED_AFFECTS]
        if bad:
            failures.append((str(path.relative_to(DOCS)), bad))
    assert not failures, "affects contains unrecognised values:\n" + "\n".join(
        f"  {p}: {b}" for p, b in failures
    )


# ───────────────────────────── sources ──────────────────────────


def test_every_term_page_cites_at_least_one_source(pages):
    failures = []
    for path, meta in pages:
        if not (meta.get("source_citations") or []):
            failures.append(str(path.relative_to(DOCS)))
    assert not failures, "pages without source citation:\n" + "\n".join(
        f"  {p}" for p in failures
    )


def test_every_cited_path_points_inside_repo(pages):
    failures = []
    for path, meta in pages:
        cites = meta.get("source_citations") or []
        for c in cites:
            if not isinstance(c, dict):
                continue
            if "path" in c:
                # either relative to repo root, or absolute inside /tmp
                # (the audit-clean clones). We ban absolute paths.
                if c["path"].startswith("/"):
                    failures.append((str(path.relative_to(DOCS)), c["path"]))
    assert not failures, "absolute source paths:\n" + "\n".join(
        f"  {p}: {pp}" for p, pp in failures
    )


# ───────────────────────────── disputes ──────────────────────────


def test_disputed_pages_cite_their_dispute_id(pages):
    failures = []
    for path, meta in pages:
        if meta.get("status") != "disputed":
            continue
        # id pattern from phase-1/docs/runbook/disputes.json
        dispute_ids = meta.get("dispute_ids") or []
        if not dispute_ids or not any(
            did.startswith("DISPUTE-") for did in dispute_ids
        ):
            failures.append(str(path.relative_to(DOCS)))
    assert not failures, "disputed pages without a DISPUTE-* id:\n" + "\n".join(
        f"  {p}" for p in failures
    )


# ───────────────────────────── translation review status ──────────────────────────


def test_translation_review_status_is_recorded_for_each_language(pages):
    failures = []
    for path, meta in pages:
        trs = meta.get("translation_review_status") or {}
        if not isinstance(trs, dict):
            failures.append((str(path.relative_to(DOCS)), "missing"))
            continue
        for lang in ("ban", "id", "en"):
            if lang not in trs:
                failures.append((str(path.relative_to(DOCS)), lang))
    assert not failures, (
        "translation_review_status incomplete:\n"
        + "\n".join(f"  {p}: missing {x}" for p, x in failures)
    )


# ───────────────────────────── authority-bearing language ──────────────────────────


FORBIDDEN_PHRASES = [
    "ground truth",
    "canonical cultural truth",
    "definitive",
    "settled (in the customary sense)",
    "approved" + " customary",
]


def test_no_authority_phrases_in_term_pages(pages):
    failures = []
    for path, meta in pages:
        text = path.read_text(encoding="utf-8")
        # the front-matter block does not match a literal phrase the
        # way the body does — we scan the body only.
        end = text.find("\n---\n", 4)
        body = text[end + 5 :] if end != -1 else text
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in body.lower():
                failures.append((str(path.relative_to(DOCS)), phrase))
    assert not failures, "authority-bearing phrases in body:\n" + "\n".join(
        f"  {p}: {ph}" for p, ph in failures
    )


# ───────────────────────────── internal-link integrity ──────────────────────────


def test_no_obvious_broken_internal_links(pages):
    """internal links of the form `](/path/.../)` resolve to a
    file that exists under `wiki/docs/`. We only inspect Markdown
    links that look like relative URLs (skipping http(s):// and
    fragments)."""
    failures = []
    link_re = re.compile(r"\]\((/[^)#?]+)\)")
    for path, meta in pages:
        text = path.read_text(encoding="utf-8")
        # skip the front-matter block
        end = text.find("\n---\n", 4)
        body = text[end + 5 :] if end != -1 else text
        for m in link_re.finditer(body):
            link = m.group(1)
            # Some links point to other-language versions of the same
            # page that may not exist yet. We accept those as soft
            # links (the registered audit cross-language handler
            # decides at build time) only if the language prefix is
            # `ban/`. For id/ and en/, the file MUST exist.
            lang_prefix = link.lstrip("/").split("/", 1)[0]
            if lang_prefix == "ban":
                continue
            target = (DOCS / link.lstrip("/")).resolve()
            # allow anchor-only links
            if not target.exists():
                failures.append((str(path.relative_to(DOCS)), link))
    assert not failures, "broken internal links:\n" + "\n".join(
        f"  {p}: {l}" for p, l in failures
    )


# ───────────────────────────── translation invariants ──────────────────────────


def test_bahasa_bali_spelling_only_from_repo_i18n_table():
    """If a page declares `language_variants.ban.spelling` and
    `language_variants.ban.status` is not `pending_customary_review`,
    the spelling must appear in
    `phase-1/src/dewatacalendar/i18n.py`'s WUKU_I18N / PANCAWARA_I18N /
    SAPTAWARA_I18N / SASIH_I18N / RAHINAN_I18N, or in
    `README_BAL.md`. This is the no-invention invariant."""
    i18n_py = (REPO / "phase-1/src/dewatacalendar/i18n.py").resolve()
    if not i18n_py.exists():
        pytest.skip(f"{i18n_py} not in this checkout")
    text_i18n = i18n_py.read_text(encoding="utf-8")
    readme_bal = (REPO / "README_BAL.md").resolve()
    text_readme = readme_bal.read_text(encoding="utf-8") if readme_bal.exists() else ""

    failures = []
    for path, meta in iter_term_pages():
        variants = meta.get("language_variants") or {}
        ban = variants.get("ban") if isinstance(variants, dict) else None
        if not isinstance(ban, dict):
            continue
        if ban.get("status") == "pending_customary_review":
            continue
        spelling = (ban.get("spelling") or "").strip()
        if not spelling:
            continue
        # Tolerate case-insensitive match on these tables only.
        if (
            spelling not in text_i18n
            and spelling.lower() not in text_i18n.lower()
            and spelling.lower() not in text_readme.lower()
        ):
            failures.append((str(path.relative_to(DOCS)), spelling))
    assert not failures, (
        "Bahasa Bali spellings outside the verified set "
        "(phase-1/src/dewatacalendar/i18n.py, README_BAL.md):\n"
        + "\n".join(f"  {p}: {s}" for p, s in failures)
    )
