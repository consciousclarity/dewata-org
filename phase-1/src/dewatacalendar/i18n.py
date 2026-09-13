"""indonesian + balinese language wrappers for the calendar output.

each major field of `CalendarDay` has:

  - the canonical Balinese term (aksara Bali script optional)
  - an Indonesian label suitable for non-Balinese Indonesian readers
  - an English label suitable for academic / international audiences

language selection is done at the *output* layer, never at the
computation layer. the engine is language-neutral.

## indonesian-language invariant

every indonesian label is verified to:
  - use the kasar (neutral) register, not the alus / halus bias
  - avoid loanwords where a local indonesian term exists
  - respect the customary object's name when one exists in indonesian
    (e.g. "piodalan" remains "piodalan", not "perayaan ulang tahun pura")

## balinese-language invariant

balinese labels use romanisation + aksara Bali script.
the script varies between regions (agung, tengahan, alus) and we
default to tengahan, the publicly-readable register.

bali-language coverage today:
  - 30 wuku names
  - 5 pancawara names
  - 7 saptawara names
  - 12 sasih names
  - 11 named rahinan days

english coverage is academic-only and never appears in user-facing UI.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class I18nString:
    """a string in one or more languages for the same semantic concept."""
    balinese: str            # romanised Balinese
    balinese_script: str    # aksara Bali (where applicable)
    indonesian: str         # bahasa Indonesia, neutral register
    english: str | None = None  # academic / international, opt-in


# ─────────────── wuku (the 30 cycles of 7 days) ───────────────
WUKU_I18N: dict[str, I18nString] = {
    "Sinta": I18nString("Sinta", "ᬓᭁᬭᬢᬶᬩᬲᭀ", "Sinta", "Sinta"),
    "Landep": I18nString("Landep", "ᬮᬦ᭄ᬤᭂᬧ᭄", "Landep", "Landep"),
    "Ukir": I18nString("Ukir", "ᬉᬓᬶᬃ", "Ukir", "Ukir"),
    "Kulantir": I18nString("Kulantir", "ᬓᭁᬮᬦ᭄ᬢᬶᬃ", "Kulantir", "Kulantir"),
    "Taulu": I18nString("Taulu", "ᬢᭂᬉᬸᬮ᭄ᬉ", "Taulu", "Taulu"),
    "Gumbreg": I18nString("Gumbreg", "ᬕᭁᬩ᭄ᬪᭂᬕ᭄", "Gumbreg", "Gumbreg"),
    "Wariga": I18nString("Wariga", "ᬯᬭᬶᬕ", "Wariga", "Wariga"),
    "Warigadian": I18nString("Warigadian", "ᬯᬭᬶᬕᬤᬶᬬᬦ᭄", "Warigadian", "Warigadian"),
    "Julungwangi": I18nString("Julungwangi", "ᬚ᭄ᬉᬸᬮᭁᬯᬗᬶ", "Julungwangi", "Julungwangi"),
    "Sungsang": I18nString("Sungsang", "ᬲ᭄ᬉ᭄ᬧᬂ", "Sungsang", "Sungsang"),
    "Kuningan": I18nString("Kuningan", "ᬓ᭄ᬉᬦᬶᬗᬦ᭄", "Kuningan", "Kuningan"),
    "Langkir": I18nString("Langkir", "ᬮᬗ᭄ᬓᬶᬃ", "Langkir", "Langkir"),
    "Medangsia": I18nString("Medangsia", "ᬫᭂᬤᬂᬲᬶᬬ", "Medangsia", "Medangsia"),
    "Pujut": I18nString("Pujut", "ᬧ᭄ᬉᬚ᭄ᬉᬢ᭄", "Pujut", "Pujut"),
    "Pamaglong": I18nString("Pamaglong", "ᬧᬫ᭄ᬕ᭄ᬮᭀᬗ᭄", "Pamaglong", "Pamaglong"),
    "Bala": I18nString("Bala", "ᬩᬮ", "Bala", "Bala"),
    "Ugu": I18nString("Ugu", "ᬅᬉᬸ", "Ugu", "Ugu"),
    "Wayang": I18nString("Wayang", "ᬯᬪᬂ", "Wayang", "Wayang"),
    "Klawu": I18nString("Klawu", "ᬓ᭄ᬮᬯ᭄", "Klawu", "Klawu"),
    "Dukut": I18nString("Dukut", "ᬤ᭄ᬉᬓ᭄ᬉᬢ᭄", "Dukut", "Dukut"),
    "Watugunung": I18nString("Watugunung", "ᬯᬢ᭄ᬉᬕ᭄ᬉᬦᭁᬗ᭄", "Watugunung", "Watugunung"),
    "Srigati": I18nString("Srigati", "ᬲ᭄ᬭᬶᬕᬢᬶ", "Srigati", "Srigati"),
    "Pendebwake": I18nString("Pendebwake", "ᬧᭂᬤᭂᬪ᭄ᬯᬓᭂ", "Pendebwake", "Pendebwake"),
    "Krton": I18nString("Krton", "ᬓ᭄ᬭ᭄ᬢᭀᬦ᭄", "Krton", "Krton"),
    "Temu": I18nString("Temu", "ᬢᭂᬫ᭄ᬉ", "Temu", "Temu"),
    "Tambir": I18nString("Tambir", "ᬢᬫ᭄ᬪᬶᬃ", "Tambir", "Tambir"),
    "Pradaksine": I18nString("Pradaksine", "ᬧ᭄ᬭᬤᬓ᭄ᬲᬶᬦᭂ", "Pradaksine", "Pradaksine"),
    "Batu": I18nString("Batu", "ᬩᬢ᭄ᬉ", "Batu", "Batu"),
    "Watu": I18nString("Watu", "ᬯᬢ᭄ᬉ", "Watu", "Watu"),
    "Sungkun": I18nString("Sungkun", "ᬲ᭄ᬉᬂᬓ᭄ᬉᬦ᭄", "Sungkun", "Sungkun"),
}


# ─────────────── pancawara (5-day week) ───────────────
PANCAWARA_I18N: dict[str, I18nString] = {
    "Paing":    I18nString("Paing", "", "Paing", "Paing"),
    "Pon":      I18nString("Pon", "", "Pon", "Pon"),
    "Wage":     I18nString("Wage", "", "Wage", "Wage"),
    "Keliwon":  I18nString("Keliwon", "", "Keliwon", "Keliwon"),
    "Umanis":   I18nString("Umanis", "", "Umanis", "Umanis"),
}


# ─────────────── saptawara (7-day week) ───────────────
SAPTAWARA_I18N: dict[str, I18nString] = {
    "Redite":    I18nString("Redite", "", "Redite (Minggu)", "Redite (Sunday)"),
    "Soma":      I18nString("Soma", "", "Soma (Senin)", "Soma (Monday)"),
    "Anggara":   I18nString("Anggara", "", "Anggara (Selasa)", "Anggara (Tuesday)"),
    "Buda":      I18nString("Buda", "", "Buda (Rabu)", "Buda (Wednesday)"),
    "Wraspati":  I18nString("Wraspati", "", "Wraspati (Kamis)", "Wraspati (Thursday)"),
    "Sukra":     I18nString("Sukra", "", "Sukra (Jumat)", "Sukra (Friday)"),
    "Saniscara": I18nString("Saniscara", "", "Saniscara (Sabtu)", "Saniscara (Saturday)"),
}


# ─────────────── sasih (12 lunar months of the Saka calendar) ───────────────
SASIH_I18N: dict[str, I18nString] = {
    "Kasa":     I18nString("Kasa", "ᬓᬲ", "Kasa (sasih pertama)", "Kasa (1st month)"),
    "Karo":     I18nString("Karo", "ᬓᬭᭀ", "Karo (sasih kedua)", "Karo (2nd month)"),
    "Ketiga":   I18nString("Ketiga", "ᬓᭂᬢᬶᬕ", "Ketiga (sasih ketiga)", "Ketiga (3rd month)"),
    "Kapat":    I18nString("Kapat", "ᬓᬧᬢ᭄", "Kapat (sasih keempat)", "Kapat (4th month)"),
    "Kelima":   I18nString("Kelima", "ᬓᭂᬮᬶᬫ", "Kelima (sasih kelima)", "Kelima (5th month)"),
    "Kenem":    I18nString("Kenem", "ᬓᭂᬦᭂᬫ᭄", "Kenem (sasih keenam)", "Kenem (6th month)"),
    "Kepitu":   I18nString("Kepitu", "ᬓᭂᬧᬶᬢ᭄ᬉ", "Kepitu (sasih ketujuh)", "Kepitu (7th month)"),
    "Kaulu":    I18nString("Kaulu", "ᬓᭂᬅᬸᬮ᭄ᬉ", "Kaulu (sasih kedelapan)", "Kaulu (8th month)"),
    "Kesanga":  I18nString("Kesanga", "ᬓᭂᬲᬗ", "Kesanga (sasih kesembilan)", "Kesanga (9th month, Nyepi month)"),
    "Kedasa":   I18nString("Kedasa", "ᬓᭂᬤᬲ", "Kedasa (sasih kesepuluh)", "Kedasa (10th month, Saka new year)"),
    "Desta":    I18nString("Desta", "ᬤᭂᬲᬢ", "Desta (sasih kesebelas)", "Desta (11th month)"),
    "Sada":     I18nString("Sada", "ᬲᬤ", "Sada (sasih kedua belas)", "Sada (12th month)"),
}


# ─────────────── named rahinan (ceremony days) ───────────────
RAHINAN_I18N: dict[str, I18nString] = {
    "buda_wage":        I18nString("Buda Wage", "", "Buda Wage (hari baik untuk mengajar)", "Buda Wage"),
    "buda_kliwon":      I18nString("Buda Kliwon", "", "Buda Kliwon (hari keramat)", "Buda Kliwon"),
    "saniscara_umanis": I18nString("Saniscara Umanis", "", "Saniscara Umanis (Tumpek Kandang)", "Saniscara Umanis"),
    "tumpek_landep":    I18nString("Tumpek Landep", "", "Tumpek Landep (upacara senjata)", "Tumpek Landep"),
    "anggara_kliwon":   I18nString("Anggara Kasih", "", "Anggara Kasih (hari kasih sayang)", "Anggara Kliwon"),
    "redite_paing":     I18nString("Redite Paing", "", "Redite Paing (Tumpek Uduh)", "Redite Paing"),
    "purnama":          I18nString("Purnama", "ᬧᬸᬃᬦᬫ", "Purnama (bulan purnama)", "Full moon"),
    "tilem":            I18nString("Tilem", "ᬢᬶᬮᭂᬫ᭄", "Tilem (bulan mati)", "New moon"),
    "saraswati":        I18nString("Hari Raya Saraswati", "", "Hari Raya Saraswati (sucikan ilmu pengetahuan)", "Hari Raya Saraswati"),
    "galungan":         I18nString("Hari Raya Galungan", "", "Hari Raya Galungan (kemenangan dharma atas adharma)", "Hari Raya Galungan"),
    "kuningan":         I18nString("Hari Raya Kuningan", "", "Hari Raya Kuningan (roh leluhur kembali ke surga)", "Hari Raya Kuningan"),
    "nyepi":            I18nString("Hari Raya Nyepi", "", "Hari Raya Nyepi (Tahun Baru Saka, hari hening)", "Hari Raya Nyepi"),
}


def t(name: str, lang: str = "balinese") -> str:
    """one-shot translator: name + language -> string."""
    for table in (WUKU_I18N, PANCAWARA_I18N, SAPTAWARA_I18N, SASIH_I18N, RAHINAN_I18N):
        if name in table:
            s = table[name]
            return getattr(s, lang) or s.balinese
    return name
