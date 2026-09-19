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


# ───────────────────────── front-matter stray-content guard ──────────────────────────
#
# Origin: a harness-leak regression. On 2026-09-19, the assistant harness
# inserted a stray `http://localhost:41185/chat` line into the front-matter
# of wiki/docs/id/rahinan/id-mapping.md at PR #6 (wiki-foundation-20260917).
# The line was not a declared YAML key, but PyYAML happily parsed it as a
# top-level key with value None, which then sat between the `language_variants`
# block and the `id:` subkey. All 13 wiki metadata tests passed over the
# corruption because they only validate declared fields. The line landed
# in the public site and the search index.
#
# Two failures in one: a structural test that ignores stray content
# between declared fields, and an isolation test that never catches
# URL/host-path/markup fragments injected into front-matter. This test
# closes both gaps. Front-matter is a structured YAML document and only
# declared fields (with declared subkeys for dict-valued fields, and
# declared scalar items for list-valued fields) are valid content. URL,
# host-path, and markdown-link-fragment content is allowed only inside
# the `source_citations` list (paths/quote text can legitimately cite
# external artefacts) and inside the `customary_review_status.note` field
# (which may reference external attestations). Anywhere else, these
# patterns indicate harness output that leaked into the document.
ALLOWED_TOP_LEVEL_KEYS = {
    "canonical_term",
    "canonical_slug",
    "category",
    "language_variants",
    "alternative_spellings",
    "short_definition",
    "detailed_explanation",
    "dewata_specific_meaning",
    "affects",
    "examples",
    "related_terms",
    "source_citations",
    "evidence_status",
    "dispute_ids",
    "customary_review_status",
    "translation_review_status",
    "ruleset_version_relevance",
    "last_reviewed",
    "reviewer",
    "status",
}

# dict-valued fields and the keys permitted inside them.
ALLOWED_SUBKEYS_BY_TOP_LEVEL = {
    "language_variants": {"ban", "id", "en"},
    "translation_review_status": {"ban", "id", "en"},
    "customary_review_status": {"status", "note"},
}

# Top-level fields whose scalar text content is allowed to mention URLs,
# host paths, or markdown-link fragments because they reference external
# evidence or attestations directly. Everything else is forbidden.
FIELDS_ALLOWING_URL_OR_PATH_LIKE_TEXT = {
    "source_citations",   # each list item is a dict with `path` and `quote`
    "customary_review_status",  # `note` may reference attestations
}

# Patterns that, anywhere in front-matter outside the allowed fields,
# indicate leaked harness content. The patterns are deliberately
# specific to the failure mode that produced the localhost line: URLs,
# IP/host:port literals, and Markdown link syntax.
URL_OR_PATH_PATTERNS = [
    re.compile(r"https?://[^\s\"]+"),       # http(s) URLs
    re.compile(r"\b(?:localhost|127\.0\.0\.1|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+\b"),  # host:port or IP:port
    re.compile(r"\[[^\]\n]+\]\([^)\n]+\)"),  # markdown link [text](url)
    re.compile(r"</[a-zA-Z][\w-]*>"),        # closing HTML/XML tag fragment
    re.compile(r"<\s*[a-zA-Z][\w./-]*\s*/?>"),  # opening HTML/XML/self-closing tag
]


def _iter_all_md_with_frontmatter() -> list[Path]:
    """all .md files under wiki/docs/ that begin with --- and have a
    closing ---, regardless of whether they declare a canonical_slug."""
    out = []
    for p in sorted(DOCS.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        end = text.find("\n---\n", 4)
        if end == -1:
            continue
        out.append(p)
    return out


def test_front_matter_has_only_declared_keys_and_subkeys():
    """Every top-level key in every front-matter block must be in
    ALLOWED_TOP_LEVEL_KEYS; every subkey of a dict-valued field must be
    in ALLOWED_SUBKEYS_BY_TOP_LEVEL for that field. Stray keys (which
    the harness leak produced) fail loudly here."""
    failures = []
    for path in _iter_all_md_with_frontmatter():
        text = path.read_text(encoding="utf-8")
        end = text.find("\n---\n", 4)
        try:
            meta = yaml.safe_load(text[4:end])
        except yaml.YAMLError as e:
            failures.append((path.relative_to(DOCS), "YAMLError", str(e)))
            continue
        if not isinstance(meta, dict):
            failures.append((path.relative_to(DOCS), "top-level not a dict", type(meta).__name__))
            continue
        for k in meta.keys():
            if k not in ALLOWED_TOP_LEVEL_KEYS:
                failures.append((path.relative_to(DOCS), "stray top-level key", k))
        for field, allowed_subkeys in ALLOWED_SUBKEYS_BY_TOP_LEVEL.items():
            value = meta.get(field)
            if not isinstance(value, dict):
                continue
            for sub in value.keys():
                if sub not in allowed_subkeys:
                    failures.append((path.relative_to(DOCS), f"stray subkey under {field}", sub))
        # source_citations entries are dicts; they have a constrained shape too.
        sc = meta.get("source_citations")
        if isinstance(sc, list):
            for entry in sc:
                if not isinstance(entry, dict):
                    failures.append((path.relative_to(DOCS), "source_citations entry not a dict", str(entry)[:60]))
                    continue
                if "path" not in entry:
                    failures.append((path.relative_to(DOCS), "source_citations entry missing path", list(entry.keys())))
    assert not failures, (
        "front-matter has undeclared keys or stray content:\n"
        + "\n".join(f"  {p}: {kind} = {val!r}" for p, kind, val in failures)
    )


def test_front_matter_has_no_url_path_or_markup_outside_declared_fields():
    """URL, host:port, IP:port, and markdown-link-fragment patterns are
    forbidden in front-matter except inside `source_citations` (which
    holds evidence citations that legitimately include paths and quote
    text) and inside `customary_review_status.note` (which may reference
    attestations). Anywhere else is harness leak or stray editor content.

    Two checks run in series. First: walk the parsed YAML structure and
    flag any url/path/markup pattern in a scalar value whose field
    path is not in the allowlist. This catches content that parses
    cleanly into a real field but shouldn't be there. Second: walk the
    raw front-matter bytes and flag the same patterns anywhere in the
    block, regardless of parse outcome. This catches the failure mode
    in which a stray line breaks YAML parsing entirely (PyYAML refuses
    to parse, so the structured walk would silently skip); mkdocs-material
    still renders the raw front-matter as visible text in that case, so
    the harness leak becomes a visible defect on the public site."""
    failures = []

    for path in _iter_all_md_with_frontmatter():
        text = path.read_text(encoding="utf-8")
        end = text.find("\n---\n", 4)
        fm_block = text[4:end]
        try:
            meta = yaml.safe_load(fm_block)
            parsed_ok = True
        except yaml.YAMLError:
            meta = None
            parsed_ok = False

        # check (a): parsed structure, when parsing succeeded.
        if parsed_ok and isinstance(meta, dict):
            def walk(obj, path_here):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        walk(v, path_here + [str(k)])
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        if isinstance(v, dict):
                            for k, v2 in v.items():
                                walk(v2, path_here + [f"[{i}].{k}"])
                        else:
                            walk(v, path_here + [f"[{i}]"])
                elif isinstance(obj, str):
                    if any(a in FIELDS_ALLOWING_URL_OR_PATH_LIKE_TEXT for a in path_here):
                        return
                    for pat in URL_OR_PATH_PATTERNS:
                        if pat.search(obj):
                            failures.append((
                                path.relative_to(DOCS),
                                ".".join(path_here),
                                obj[:120],
                            ))
                            return
            walk(meta, [])

        # check (b): raw front-matter bytes, regardless of parse outcome.
        # We exempt the lines that declare an allowed field whose value
        # may legitimately contain paths/urls (source_citations items,
        # customary_review_status.note). Other lines that match any
        # pattern fail.
        lines = fm_block.split("\n")
        for line_no, line in enumerate(lines, start=1):
            # skip blank lines, top-level field names that are themselves
            # allowed keys, and the allowed-list literal
            stripped = line.strip()
            if not stripped:
                continue
            # is this a top-level field declaration? key names from the
            # allowlist + colon = an allowed declaration line
            top_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:", stripped)
            if top_match and top_match.group(1) in ALLOWED_TOP_LEVEL_KEYS:
                continue
            # is this a subkey declaration inside an allowed dict field
            # (we know the field context from indentation, but for
            # simplicity we just check the subkey-name pattern)
            sub_match = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*)\s*:", stripped)
            if sub_match:
                # any subkey declared in the allowlist is fine; the
                # field's allowlist status will be evaluated by check (a)
                subkey_name = sub_match.group(1)
                if subkey_name in {"ban", "id", "en", "status", "note", "path", "role", "quote"}:
                    continue
            # is this a YAML list item marker? skip "  - " lines.
            if re.match(r"^\s+-\s", stripped):
                continue
            # any remaining non-empty line: scan for patterns
            for pat in URL_OR_PATH_PATTERNS:
                if pat.search(stripped):
                    failures.append((
                        path.relative_to(DOCS),
                        f"raw-line:{line_no}",
                        stripped[:120],
                    ))
                    break

    assert not failures, (
        "front-matter contains url/host-path/markup-fragment content outside "
        "the declared fields that allow it (source_citations, "
        "customary_review_status):\n"
        + "\n".join(f"  {p}  field={f}  value={v!r}" for p, f, v in failures)
    )
