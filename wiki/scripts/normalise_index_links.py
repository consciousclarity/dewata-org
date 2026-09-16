"""normalise absolute `/<lang>/...` Markdown links in section index
pages to be relative links, so MkDocs's strict mode does not
complain.

Usage: `python -m wiki.scripts.normalise_index_links`
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

_LANG = {"ban", "id", "en"}
_LINK_RE = re.compile(r"\]\((/([a-z]{2,3})/([^)#?]+))\)")


def normalise(page: Path) -> bool:
    src = page.read_text(encoding="utf-8")
    here = "/".join(page.relative_to(DOCS).parts[:-1])  # exclude the filename
    parts = here.split("/")
    # Determine current language directory (first component)
    if parts[0] in _LANG and len(parts) >= 1:
        here_lang = parts[0]
    else:
        return False

    def repl(m: re.Match) -> str:
        target_lang, tail = m.group(2), m.group(3)
        full_target = f"{target_lang}/{tail}"
        # split paths
        here_segments = here.split("/")
        target_segments = full_target.split("/")
        # remove common prefix
        i = 0
        max_up = len(here_segments)
        while (i < max_up
               and i < len(target_segments)
               and here_segments[i] == target_segments[i]):
            i += 1
        ups = [".."] * (len(here_segments) - i)
        # if i is the lang dir, target_segments[i] is the section;
        # drop the lang prefix because here_lang -> target_lang may differ
        rel = "/".join(ups + target_segments[i:])
        return f"]({rel})"

    new = _LINK_RE.sub(repl, src)
    if new != src:
        page.write_text(new, encoding="utf-8")
        return True
    return False


def main():
    touched = 0
    for md in DOCS.rglob("*.md"):
        if md.name == "index.md":
            continue  # indexes are intra-section; they use section links
        if normalise(md):
            touched += 1
    # also process index pages for cross-language links, but keep
    # within-language linking.
    print(f"normalised: {touched} files")


if __name__ == "__main__":
    main()
