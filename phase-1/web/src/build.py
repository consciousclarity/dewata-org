from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LocaleString:
    ban: str
    id: str
    en: str


@dataclass
class PageSpec:
    slug: str
    template: str
    title_key: str


def _load_locale(locale_dir: Path) -> dict[str, LocaleString]:
    """parse `*.json` per locale into a dict keyed by i18n key.

    We support the canonical ISO 639-2 codes: ban (Balinese), id
    (Indonesian), en (English).  Older files that used `bal` are
    tolerated by mapping them to `ban`."""
    out: dict[str, LocaleString] = {}
    files = sorted(locale_dir.glob("*.json"))
    # Normalize bal -> ban
    by_lang = {}
    for f in files:
        lang = f.stem
        if lang == "bal":
            lang = "ban"
        by_lang[lang] = json.loads(f.read_text(encoding="utf-8"))
    ban_data = by_lang.get("ban", {})
    id_data = by_lang.get("id", {})
    en_data = by_lang.get("en", {})
    # union of all keys
    keys = set(ban_data) | set(id_data) | set(en_data)
    for key in keys:
        out[key] = LocaleString(
            ban=ban_data.get(key, id_data.get(key, en_data.get(key, key))),
            id=id_data.get(key, ban_data.get(key, en_data.get(key, key))),
            en=en_data.get(key, ban_data.get(key, id_data.get(key, key))),
        )
    return out


def _render_template(tpl_path: Path, ctx: dict[str, object]) -> str:
    """tiny template engine: {{var}} substitution + {% if var %}…{% endif %}
    conditional blocks.  no loops, no expressions — keep it minimal.
    """
    text = tpl_path.read_text(encoding="utf-8")
    while True:
        m = re.search(r"\{% if ([a-zA-Z_][\w\.]*) %\}(.*?)\{% endif %\}", text, re.DOTALL)
        if not m:
            break
        key = m.group(1)
        block = m.group(2)
        cond = bool(ctx.get(key, False))
        text = text[: m.start()] + (block if cond else "") + text[m.end():]
    for key, val in ctx.items():
        text = text.replace("{{" + key + "}}", "" if val is None else str(val))
    return text


def _chrome_for_locale(locales: dict[str, LocaleString], lang: str) -> dict[str, str]:
    """build the chrome dict for a given target language (ban/id/en).

    chrome_keys use the same flat naming as before (the template expects
    e.g. {{brand}}, {{nav_home}}, etc.)."""
    chrome_keys = [
        ("chrome.brand", "brand"),
        ("chrome.meta.description", "meta_description"),
        ("chrome.nav.home", "nav_home"),
        ("chrome.nav.calendar", "nav_calendar"),
        ("chrome.nav.about", "nav_about"),
        ("chrome.nav.transparency", "nav_transparency"),
        ("chrome.lang.label", "lang_label"),
        ("chrome.lang.ban", "lang_ban"),
        ("chrome.lang.id", "lang_id"),
        ("chrome.lang.en", "lang_en"),
        ("chrome.provenance.label", "provenance_label"),
        ("chrome.provenance.computed", "provenance_computed"),
        ("chrome.provenance.registered", "provenance_registered"),
        ("chrome.provenance.predicted", "provenance_predicted"),
        ("chrome.provenance.verified", "provenance_verified"),
        ("chrome.footer.lang", "footer_lang"),
        ("chrome.footer.policy", "footer_policy"),
        ("chrome.footer.negatives", "footer_negatives"),
        ("chrome.footer.about", "footer_about"),
        ("chrome.footer.transparency", "footer_transparency"),
    ]
    out = {}
    for src_key, dst_key in chrome_keys:
        ls = locales.get(src_key, LocaleString("", "", ""))
        out[dst_key] = getattr(ls, lang) or ""
    return out


def _label_for_page(locales: dict[str, LocaleString], lang: str, page_title_key: str) -> str:
    ls = locales.get(page_title_key, LocaleString("", "", ""))
    return getattr(ls, lang) or page_title_key


def build(src: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    locale_dir = src / "locales"
    locales = _load_locale(locale_dir)

    # write per-key JSON bundles (ban/id/en) for any runtime fetch
    out_locales = out / "assets" / "locales"
    out_locales.mkdir(parents=True, exist_ok=True)
    for key, ls in locales.items():
        out_locales.joinpath(f"{key}.json").write_text(
            json.dumps({"ban": ls.ban, "id": ls.id, "en": ls.en}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

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
            ud_note = spec_dict.get("under_development_note", "").strip()
            cr_note = spec_dict.get("cultural_review_note", "").strip()
            under_dev = bool(spec_dict.get("under_development", False))
            cr_pending = bool(spec_dict.get("cultural_review_pending", False))
            links = spec_dict.get("links", [])

            # emit one HTML per (slug, language).  the language code is
            # embedded in the lang attribute and in the file name.
            for lang in ("ban", "id", "en"):
                chrome = _chrome_for_locale(locales, lang)
                ctx = {
                    "title": _label_for_page(locales, lang, title_key),
                    "label": label,
                    "lang": lang,
                    "computed_list": "\n".join(
                        f"<li>{_i18n_item(i, locales, lang)}</li>" for i in computed
                    ),
                    "registered_list": "\n".join(
                        f"<li>{_i18n_item(i, locales, lang)}</li>" for i in registered
                    ),
                    "predictions_list": "\n".join(
                        f"<li>{_i18n_item(i, locales, lang)}</li>" for i in predictions
                    ),
                    "verified_list": "\n".join(
                        f"<li>{_i18n_item(i, locales, lang)}</li>" for i in verified
                    ),
                    "under_development": under_dev,
                    "cultural_review_pending": cr_pending,
                    "under_development_note": ud_note.replace("\n", "<br>") if ud_note else "",
                    "cultural_review_note": cr_note.replace("\n", "<br>") if cr_note else "",
                    "links_html": _render_links(links, lang),
                    "lang_nav": _lang_nav(locales, lang),
                    **chrome,
                }
                html = _render_template(src / "templates" / template, ctx)
                out.joinpath(f"{slug}.{lang}.html").write_text(html, encoding="utf-8")
                built += 1

    # emit the default (ban) page at the canonical URL for each slug
    # so visiting /index.html gets the Basa Bali version by default.
    for page_file in sorted(pages_dir.glob("*.yaml")):
        slug = page_file.stem
        ban_path = out / f"{slug}.ban.html"
        if ban_path.exists():
            (out / f"{slug}.html").write_text(ban_path.read_text(encoding="utf-8"), encoding="utf-8")

    # assets (skip .gitkeep placeholders)
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

    return built


def _lang_nav(locales: dict[str, LocaleString], current: str) -> str:
    """render the i18n nav for the current language.

    Each link goes to a real per-language page URL (not a query param).
    The current language link gets aria-current=page and is rendered as
    a non-link span."""
    out = []
    for code, label_key in (("ban", "chrome.lang.ban"), ("id", "chrome.lang.id"), ("en", "chrome.lang.en")):
        ls = locales.get(label_key, LocaleString("", "", ""))
        label = getattr(ls, code, code)
        if code == current:
            out.append(f'<span class="lang-current" aria-current="page">{label}</span>')
        else:
            out.append(f'<a href="/index.{code}.html" rel="alternate" hreflang="{code}">{label}</a>')
    return "\n".join(out)


def _render_links(links: list, lang: str) -> str:
    """render a list of {label_<lang>, href, caption_<lang>} entries as an HTML UL."""
    if not links:
        return ""
    out = []
    for link in links:
        label = link.get(f"label_{lang}", link.get("label", ""))
        href = link.get("href", "")
        caption = link.get(f"caption_{lang}", "")
        if not label or not href:
            continue
        out.append(f'<li><a href="{href}">{label}</a>{" — " + caption if caption else ""}</li>')
    return "\n".join(out)


def _i18n_item(item: object, locales: dict[str, LocaleString], lang: str) -> str:
    if isinstance(item, str):
        ls = locales.get(item, LocaleString(item, item, item))
        return getattr(ls, lang) or item
    if isinstance(item, dict):
        if lang in item:
            return str(item[lang])
        if "ban" in item:
            return str(item["ban"])
    return str(item)


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
