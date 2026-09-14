"""tests for the bci web build."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WEB_SRC = REPO_ROOT / "phase-1/web/src"
WEB_DIST = REPO_ROOT / "phase-1/web/dist"

# ensure the web.src package is importable when pytest runs from the
# phase-1 rootdir.  the `pythonpath = ["src"]` block in pyproject
# exposes `dewatacalendar` but not the web.src package; add it
# explicitly here.
if str(REPO_ROOT / "phase-1/web") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "phase-1/web"))


@pytest.fixture()
def dist_dir(tmp_path: Path):
    """build into a clean tmp dir per-test."""
    return tmp_path / "dist"


def _build(dist: Path) -> int:
    """rebuild the site into `dist`.  returns page count."""
    if dist.exists():
        shutil.rmtree(dist)
    from src.build import main as build_main
    sys.argv = ["build", "--src", str(WEB_SRC), "--out", str(dist)]
    rc = build_main()
    assert rc == 0, f"build failed with rc={rc}"
    return len(list(dist.glob("*.html")))


class TestWebBuild:

    def test_build_emits_expected_pages(self, dist_dir):
        from pathlib import Path
        n = _build(dist_dir)
        # 4 pages * 3 languages (ban/id/en) + 4 default-alias pages (one per slug)
        assert n == 16, f"expected 16 html files, got {n}"
        # default-alias pages (Balinese primary)
        for slug in ("index", "calendar", "transparency", "about"):
            assert (dist_dir / f"{slug}.html").is_file(), f"missing {slug}.html"
        # per-locale variants
        for lang in ("ban", "id", "en"):
            for slug in ("index", "calendar", "transparency", "about"):
                assert (dist_dir / f"{slug}.{lang}.html").is_file(), \
                    f"missing {slug}.{lang}.html"

    def test_build_emits_css(self, dist_dir):
        _build(dist_dir)
        css = dist_dir / "assets" / "style.css"
        assert css.is_file()

    def test_build_emits_locales(self, dist_dir):
        _build(dist_dir)
        locales = dist_dir / "assets" / "locales"
        files = list(locales.glob("*.json"))
        # every locale key exported
        assert len(files) > 0
        # each file is bal+id+en
        for fp in files[:3]:
            data = json.loads(fp.read_text(encoding="utf-8"))
            assert "ban" in data and "id" in data and "en" in data, \
                f"locale {fp.name} missing ban/id/en keys"

    def test_html_pages_have_no_template_placeholders(self, dist_dir):
        """the rendered html must not contain leftover `{{...}}` tokens."""
        _build(dist_dir)
        for f in (dist_dir.glob("*.html")):
            text = f.read_text(encoding="utf-8")
            leftover = re.findall(r"\{\{[a-zA-Z_.\-]+\}\}", text)
            assert not leftover, f"unrendered template var in {f}: {leftover}"

    def test_html_pages_have_provenance_label_marker(self, dist_dir):
        """every page carries the explicit 'provisional' label."""
        _build(dist_dir)
        for f in (dist_dir.glob("*.html")):
            text = f.read_text(encoding="utf-8")
            assert "provisional" in text, f"missing policy marker in {f}"

    def test_no_commercial_signals_in_html(self, dist_dir):
        """explicit anti-rules: no booking, advertising, directions,
        tourism language, tracking pixels.

        the footer is allowed to *mention* these words in negated
        form ('no booking', 'no directions') — that's exactly what
        the footer says.  we strip negated forms before checking.
        """
        _build(dist_dir)
        banned = ["book", "tour", "tourism", "directions", "advert", "tracking"]
        for f in (dist_dir.glob("*.html")):
            text = f.read_text(encoding="utf-8").lower()
            # strip negated phrases ("no book", "no tour", etc.)
            sanitized = re.sub(
                r"no\s+(booking|advertising|tours?|tourism|tracking|advertisements?|directions?|location[-\s]tracking)",
                " ", text,
            )
            sanitized = re.sub(r"\bdon['']?\s*t\s+(\w+)\b", " ", sanitized)
            for word in banned:
                if re.search(rf"\b{word}\w*", sanitized):
                    pytest.fail(
                        f"{f}: commercial vocabulary '{word}' is not allowed "
                        f"in the bci scaffolding (after negated-phrase stripping)."
                    )

    def test_i18n_keys_balinese_primary(self, dist_dir):
        """the balinese bundle has at least 5 keys."""
        _build(dist_dir)
        # the balinese locale file is named ban.json (ISO 639-2 canonical code)
        ban = json.loads((WEB_SRC / "locales/ban.json").read_text(encoding="utf-8"))
        assert len(ban) >= 5, "balinese locale must have at least 5 keys"
        # english + balinese have matching key sets
        en = json.loads((WEB_SRC / "locales/en.json").read_text(encoding="utf-8"))
        assert set(en) == set(ban), "en vs ban key set must match"
