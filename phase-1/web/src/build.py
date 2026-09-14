from __future__ import annotations

import re

"""build the Balinese Cultural Index static site.

usage:
    python -m web.build [--src phase-1/web/src] [--out phase-1/web/dist]

produces a fully static, no-build-no-JS bundle of HTML pages with
text substituted from the i18n bundles (Balinese primary, with
Indonesian and English fallbacks).
"""

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class LocaleString:
    bal: str
    id: str
    en: str


@dataclass
class PageSpec:
    slug: str
    template: str
    title_key: str
    body_keys: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()


_LOADER_TXT = """\
loading Balinese content…
"""


def _load_locale(locale_dir: Path) -> dict[str, LocaleString]:
    """parse `*.json` per locale into a dict keyed by i18n key."""
    out: dict[str, LocaleString] = {}
    files = sorted(locale_dir.glob("*.json"))
    bal_data = json.loads((files[0]).read_text(encoding="utf-8")) if files else {}
    for f in files[1:]:
        en_data = json.loads(f.read_text(encoding="utf-8"))
        for key in en_data:
            out[key] = LocaleString(
                bal=bal_data.get(key, key),
                id=bal_data.get(key, key) if f.stem == "id" else bal_data.get(key, key),
                en=en_data[key],
            )
    return out


def _render_template(tpl_path: Path, ctx: dict[str, object]) -> str:
    """tiny template engine: {{var}} substitution + {% if var %}…{% endif %}
    conditional blocks.  no loops, no expressions — keep it minimal.
    """
    text = tpl_path.read_text(encoding="utf-8")
    # resolve {% if key %}…{% endif %} blocks first.  we re-scan after each
    # substitution because replacements may grow/shrink the string.
    while True:
        m = re.search(r"\{% if ([a-zA-Z_][\w\.]*) %\}(.*?)\{% endif %\}", text, re.DOTALL)
        if not m:
            break
        key = m.group(1)
        block = m.group(2)
        cond = bool(ctx.get(key, False))
        text = text[: m.start()] + (block if cond else "") + text[m.end():]
    # substitute {{var}} placeholders (only known keys, to keep regression low).
    for key, val in ctx.items():
        text = text.replace("{{" + key + "}}", "" if val is None else str(val))
    return text


def build(src: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    # 1) locales
    locale_dir = src / "locales"
    locales = _load_locale(locale_dir)
    out_locales = out / "assets" / "locales"
    out_locales.mkdir(parents=True, exist_ok=True)
    for key, ls in locales.items():
        out_locales.joinpath(f"{key}.json").write_text(
            json.dumps({"bal": ls.bal, "id": ls.id, "en": ls.en}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    # 2) pages
    pages_dir = src / "pages"
    built = 0
    if pages_dir.exists():
        for page_file in sorted(pages_dir.glob("*.yaml")):
            import yaml
            spec_dict = yaml.safe_load(page_file.read_text(encoding="utf-8"))
            slug = spec_dict.get("slug") or page_file.stem
            template = spec_dict.get("template", "page.html.j2")
            title_key = spec_dict.get("title_key", slug)
            label = spec_dict.get("label", "provisional")
            computed = spec_dict.get("computed", [])
            registered = spec_dict.get("registered", [])
            predictions = spec_dict.get("predictions", [])
            verified = spec_dict.get("verified", [])
            # chrome strings get the balinese version primarily
            chrome_keys = [
                "chrome.brand",
                "chrome.meta.description",
                "chrome.nav.home",
                "chrome.lang.label",
                "chrome.lang.bal",
                "chrome.lang.id",
                "chrome.lang.en",
                "chrome.provenance.label",
                "chrome.provenance.computed",
                "chrome.provenance.registered",
                "chrome.provenance.predicted",
                "chrome.provenance.verified",
                "chrome.footer.lang",
                "chrome.footer.policy",
                "chrome.footer.negatives",
                "chrome.footer.about",
                "chrome.footer.transparency",
            ]
            chrome = {}
            for ck in chrome_keys:
                # strip "chrome." prefix and surface just the leaf name
                name = ck.split(".", 1)[1]   # ["chrome", "name"]
                ls = locales.get(ck, LocaleString("", "", ""))
                # for nested keys like "chrome.footer.lang" the second
                # split produces ["footer", "lang"]; the template uses
                # {{footer_lang}} so we join with underscore.
                name = name.replace(".", "_")
                chrome[name] = ls.bal
            # status banners for scaffold pages
            ud_note = spec_dict.get("under_development_note", "").strip()
            cr_note = spec_dict.get("cultural_review_note", "").strip()
            ctx = {
                "title": _p(locales.get(title_key, LocaleString("", "", "")).bal, title_key),
                "label": label,
                "computed_list": "\n".join(f"<li>{i18n_or(i, locales)}</li>" for i in computed),
                "registered_list": "\n".join(f"<li>{i18n_or(i, locales)}</li>" for i in registered),
                "predictions_list": "\n".join(f"<li>{i18n_or(i, locales)}</li>" for i in predictions),
                "verified_list": "\n".join(f"<li>{i18n_or(i, locales)}</li>" for i in verified),
                "under_development": bool(spec_dict.get("under_development", False)),
                "cultural_review_pending": bool(spec_dict.get("cultural_review_pending", False)),
                "under_development_note": ud_note.replace("\n", "<br>") if ud_note else "",
                "cultural_review_note": cr_note.replace("\n", "<br>") if cr_note else "",
                **chrome,
            }
            html = _render_template(src / "templates" / template, ctx)
            out.joinpath(f"{slug}.html").write_text(html, encoding="utf-8")
            built += 1
    # 3) assets (skip .gitkeep placeholders)
    assets = src / "assets"
    if assets.exists():
        for asset in assets.rglob("*"):
            if not asset.is_file():
                continue
            if asset.name == ".gitkeep":
                continue
            target = out / "assets" / asset.relative_to(assets)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, target)
    # 4) copy bundled locales into out/assets too (for runtime fetch)
    if locales:
        for key, ls in locales.items():
            out.joinpath("assets", "locales", f"{key}.json").write_text(
                json.dumps({"bal": ls.bal, "id": ls.id, "en": ls.en}, ensure_ascii=False),
                encoding="utf-8",
            )
    return built


def i18n_or(item: object, locales: dict[str, LocaleString]) -> str:
    """resolve a content item to its balinese string, fallback english.

    `item` may be a plain string, or a dict {"bal":..., "id":..., "en":...},
    or a `key` referencing the locale bundle.
    """
    if isinstance(item, str):
        return locales.get(item, LocaleString(item, item, item)).bal or item
    if isinstance(item, dict):
        if "bal" in item:
            return str(item["bal"])
        if "en" in item:
            return str(item["en"])
    return str(item)


def _p(text: str, fallback: str) -> str:
    return text or fallback


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m web.build")
    p.add_argument("--src", default="phase-1/web/src")
    p.add_argument("--out", default="phase-1/web/dist")
    args = p.parse_args(argv)
    src = Path(args.src).resolve()
    out = Path(args.out).resolve()
    if not src.exists():
        print(f"src not found: {src}", file=sys.stderr)
        return 1
    n = build(src, out)
    print(f"built {n} pages; output: {out}")
    return 0


__all__ = ["build", "main", "LocaleString"]


if __name__ == "__main__":
    sys.exit(main())
