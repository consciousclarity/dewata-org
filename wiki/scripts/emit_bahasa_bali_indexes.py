"""emit a Bahasa Bali section index that points only at the other
languages' navigable content. As per the wiki policy, the Bahasa
Bali section carries pending_customary_review status and does
not invent Balinese text."""

from pathlib import Path
import os

ROOT = Path("/home/alex/workspace/wiki-foundation/wiki/docs/ban")
TEMPLATE = """---
status: informational
translation_review_status:
  ban: pending_customary_review
  id: needs_review
  en: needs_review
last_reviewed: 2026-09-17
---

# {title}

> **Statusé basa Bali: `pending_customary_review`.** Riwayatan puniki nénten
> kaicihang ring basa Bali. banten saking widang antuk basa Indonesia miwah
> basa Inggris ring [{englink}]({englink}) miwah [{idlink}]({idlink}).

puniki baan ulahan antuk widang antuk basa Bali wénten kaucup ring
{tables}
"""

# Items each tied to (slug, indonesian-text)
SECTIONS = {
    "calendar": (
        "Bagian Kalender",
        ["Pawukon", "Wuku", "Siklus 210 dina", "Epoch/anchor", "Phase offset",
         "Saka", "Sasih", "Nampih Sasih", "Pengalantaka",
         "Tanggal Gregorian", "Rentang tanggal inklusif",
         "Ruleset", "Mesin kalender", "Konversi kalender",
         "Wewaran", "Ekawara", "Dwiwara", "Triwara", "Caturwara",
         "Pancawara", "Sadwara", "Saptawara", "Astawara", "Sangawara",
         "Dasawara", "Urip", "Jejepan"],
        "/id/calendar/", "/en/calendar/",
    ),
    "governance": (
        "Bagian Tata Kelola Adat",
        ["adat", "desa adat", "desa dinas", "banjar", "pura",
         "pemangku", "bendesa", "klian adat", "pecalang",
         "customary authority", "customary sign-off", "jurisdiction",
         "attestation"],
        "/id/governance/", "/en/governance/",
    ),
    "evidence": (
        "Bagian Bukti miwah Tata Kelola",
        ["evidence", "provenance", "corpus", "conformance corpus",
         "verification status", "reference eligibility", "eligible claim",
         "implementation observation", "dispute", "blocking dispute",
         "resolution", "accepted rule", "candidate ruleset",
         "ruleset promotion", "cultural review", "bibliographic review",
         "raw comparison", "normalised comparison", "phase normalisation"],
        "/id/evidence/", "/en/evidence/",
    ),
    "platform": (
        "Bagian Platform dewata",
        ["Dewata", "DSP", "public API", "API endpoint",
         "ruleset version", "computed", "registered", "predicted",
         "verified", "visibility tier", "public", "banjar visibility",
         "desa-adat visibility", "restricted", "private", "mirror",
         "signed snapshot", "release manifest", "checksum / SHA-256",
         "JSON", "JSONL", "immutable artifact", "candidate release",
         "production release"],
        "/id/platform/", "/en/platform/",
    ),
    "a-z": (
        "Daftar A–Z (penghubung)",
        ["See /id/a-z/ miwah /en/a-z/ antuk kruna kruna lengkap"],
        "/id/a-z/", "/en/a-z/",
    ),
    "rahinan": (
        "Bagian Rahinan miwah Pikoban",
        ["Rahinan", "Purnama", "Tilem", "Tumpek", "Kajeng Kliwon",
         "Anggara Kasih", "Buda Kliwon", "Buda Cemeng",
         # 12 ids implemented in rahinan.py
         "buda_wage", "buda_kliwon", "saniscara_umanis", "tumpek_landep",
         "anggara_kliwon", "redite_paing", "purnama", "tilem",
         "saraswati", "galungan", "kuningan", "nyepi"],
        "/id/rahinan/", "/en/rahinan/",
    ),
}


def main():
    for key, (title, terms, idlink, englink) in SECTIONS.items():
        out_dir = ROOT / key
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "index.md"
        lines = []
        for t in terms:
            lines.append(f"- {t}")
        tables_block = "\n".join(lines)
        out.write_text(TEMPLATE.format(
            title=title,
            idlink=idlink,
            englink=englink,
            tables=tables_block,
        ))
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
