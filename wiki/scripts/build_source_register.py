"""build a JSON source-register from the wiki's term pages.

Walks every `*.md` file under `wiki/docs/`, parses the YAML
front-matter, and collects `source_citations` keyed by:
  - path (relative repo path, e.g. 'phase-1/src/dewatacalendar/i18n.py')
  - url (external URL with role + fetched-quote hash when present)

Every term page must carry at least one citation; that requirement
is enforced by `tests/test_required_metadata.py`.

Output: `wiki/build-artifacts/source-register.json`.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARTIFACTS = ROOT / "build-artifacts"
ARTIFACTS.mkdir(exist_ok=True)


def iter_term_pages():
    """yield every Markdown file under wiki/docs/ that carries a YAML
    front-matter block with the required `canonical_slug` key."""
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
        if "canonical_slug" not in meta:
            continue
        yield rel, meta


def main() -> int:
    register = {
        "repo_path_citations": defaultdict(int),
        "url_citations": defaultdict(int),
        "page_count_by_path": defaultdict(int),
        "page_count_by_url": defaultdict(int),
        "pages_without_citations": [],
        "page_count": 0,
    }

    for rel, meta in iter_term_pages():
        register["page_count"] += 1
        cites = meta.get("source_citations") or []
        if not cites:
            register["pages_without_citations"].append(str(rel))
            continue
        for c in cites:
            if isinstance(c, dict):
                if "path" in c:
                    register["repo_path_citations"][c["path"]] += 1
                    register["page_count_by_path"][c["path"]] += 1
                if "url" in c:
                    register["url_citations"][c["url"]] += 1
                    register["page_count_by_url"][c["url"]] += 1

    # defaultdict -> dict
    register["repo_path_citations"] = dict(register["repo_path_citations"])
    register["url_citations"] = dict(register["url_citations"])
    register["page_count_by_path"] = dict(register["page_count_by_path"])
    register["page_count_by_url"] = dict(register["page_count_by_url"])

    out = ARTIFACTS / "source-register.json"
    out.write_text(json.dumps(register, indent=2, sort_keys=True))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
