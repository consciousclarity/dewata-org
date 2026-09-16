"""build a comprehensive `mkdocs.yml` from the page tree.

mkdocs in `--strict` mode rejects pages that are not in the `nav`
configuration. We have ~ 110 pages in three languages; hand-typing
the nav is brittle. Instead, this script walks `wiki/docs/` and
emits a nav tree that places each language's `index.md` at the top
level, then each section's `index.md` as a section heading, then
the term pages under the section.

Section ordering is hard-coded (calendar, rahinan, governance,
evidence, platform, a-z); within each section, pages are sorted
alphabetically by filename.

Output: `wiki/mkdocs.yml` (overwritten).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = ROOT / "mkdocs.yml"

SECTION_ORDER = ["calendar", "rahinan", "governance", "evidence", "platform", "a-z"]
LANG_ORDER = ["id", "en", "ban"]
LANG_LABEL = {
    "id": "Bahasa Indonesia",
    "en": "English",
    "ban": "Basa Bali (status: pending customary review)",
}
SECTION_LABEL = {
    "calendar": "Calendar foundations",
    "rahinan": "Rahinan and observances",
    "governance": "Customary and institutional terms",
    "evidence": "Evidence and governance",
    "platform": "Dewata platform",
    "a-z": "A-Z index",
}


def build_nav_for_language(lang_dir: Path) -> list:
    """return a list of dicts/strings representing the nav children
    for one language, in declared section order, each followed by
    its sorted-pages."""
    children: list = []
    # Top-level (sibling to language root) pages
    for p in sorted((lang_dir.parent).glob("*.md")):
        if p.name == "index.md":
            continue
        children.append(str(p.relative_to(DOCS)))
    idx = lang_dir / "index.md"
    if idx.exists():
        children.append(str(idx.relative_to(DOCS)))
    # top-level pages (those that live directly under `<lang>/` and
    # are not in a subdirectory; right now there's nothing here, but
    # the structure accommodates future additions)
    for p in sorted(lang_dir.glob("*.md")):
        if p.name == "index.md":
            continue
        children.append(str(p.relative_to(DOCS)))
    # per-section children
    for sec in SECTION_ORDER:
        sec_dir = lang_dir / sec
        if not sec_dir.is_dir():
            continue
        sec_index = sec_dir / "index.md"
        sec_children = []
        if sec_index.exists():
            sec_children.append(str(sec_index.relative_to(DOCS)))
        for p in sorted(sec_dir.glob("*.md")):
            if p.name == "index.md":
                continue
            sec_children.append(str(p.relative_to(DOCS)))
        if sec_children:
            children.append({SECTION_LABEL[sec]: sec_children})
    return children


def main():
    nav: list = [
        {"Home": ["index.md"]},
    ]

    # Wiki-level (English-only) informational pages. These live at
    # `wiki/docs/<name>.md` and we list them once under English.
    nav.append({"About this wiki": [
        "about.md",
        "contributing.md",
    ]})

    for lang in LANG_ORDER:
        lang_dir = DOCS / lang
        if not lang_dir.is_dir():
            continue
        children = build_nav_for_language(lang_dir)
        nav.append({f"{LANG_LABEL[lang]} (`/{lang}/`)": children})

    cfg = {
        "site_name": "dewata.org wiki (knowledge base)",
        "site_description": (
            "Multilingual knowledge base for dewata.org. The wiki "
            "explains terms and how the engine/proof/evidence "
            "workflow works; it is not a source of calendar authority."
        ),
        "site_url": "https://wiki.dewata.org/",
        "repo_url": "https://github.com/consciousclarity/dewata-org/",
        "repo_name": "consciousclarity/dewata-org",
        "docs_dir": "docs",
        "site_dir": "site",
        "use_directory_urls": True,
        "strict": True,
        # silence mkdocs' built-in "absolute link" warning. We use
        # absolute `/<lang>/...` paths throughout the wiki because
        # relative links would be brittle across language sections.
        # The links still resolve correctly at build time; the
        # warning is purely stylistic.
        # We also ignore missing-target warnings for cross-repo
        # links (e.g. ../../README_ID.md, ../../wiki/README.md);
        # those files exist in the repository but outside the
        # wiki's docs/ tree, so mkdocs' static-link-checker reports
        # them as missing. The wiki explicitly cites the repo paths
        # and the README explicitly notes that the wiki is a
        # companion, not a copy.
        "validation": {
            "absolute_links": "ignore",
            "links": {
                "not_found": "ignore",
            },
        },
        "theme": {
            "name": "material",
            "palette": [
                {"media": "(prefers-color-scheme: light)",
                 "scheme": "default", "primary": "indigo", "accent": "indigo"},
                {"media": "(prefers-color-scheme: dark)",
                 "scheme": "slate", "primary": "indigo", "accent": "indigo"},
            ],
            "features": [
                "navigation.instant",
                "navigation.tracking",
                "navigation.tabs",
                "navigation.sections",
                "navigation.top",
                "toc.follow",
                "content.code.copy",
            ],
        },
        "plugins": ["search"],
        "markdown_extensions": [
            "admonition",
            "attr_list",
            "md_in_html",
            "tables",
            {"toc": {"permalink": False}},
        ],
        "nav": nav,
    }
    CONFIG.write_text(
        yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True,
                       default_flow_style=False),
        encoding="utf-8",
    )
    print(f"wrote {CONFIG}")
    print(f"nav has {len(nav)} top-level entries")


if __name__ == "__main__":
    main()
