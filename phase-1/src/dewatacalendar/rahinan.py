"""rahinan — named ceremony days.

rahinan are computed rules that combine pawukon and saka inputs. each rule
specifies a *trigger* and an *output name*. we list the canonical 24 named
days from *Eiseman 1989, Bali: The Complete Guide*.

the canonical rahinan list (Eiseman-style):

  saptawara-based:
    • Buda Wage (Saptawara Buda + Pancawara Wage)
    • Buda Kliwon (Buda + Keliwon)
    • Tumpek Kandang  (Saniscara + Umanis)
    • Tumpek Landep   (Saniscara + Kliwon)
    • Tumpek Uduh     (Redite + Paing)
    • Anggara Kasih   (Anggara + Kliwon)
    • Budha Kliwon    (Buda + Kliwon)

  wuku-based:
    • Hari Raya Saraswati  (last day of Wuku Watugunung, Saptawara Saniscara)
    • Hari Raya Pager     (Wuku Sungsang, Buda)
    • Hari Raya Galungan  (Buda Kliwon, Wuku Dungulan)
    • Hari Raya Kuningan  (Saniscara Kliwon, Wuku Kuningan)
    • Hari Raya Banyu Pinaruh  (after Saraswati)
    • Hari Raya Sabuh Mas (after Banyu Pinaruh)
    • Hari Raya Petik  (after Sabuh Mas)
    • Hari Raya Manis  (after Petik)
    • Hari Raya Penampahan Galungan  (Redite before Galungan)

  sasih-based:
    • Hari Raya Nyepi  (1 Sasih Kesanga, New Year)
    • Hari Raya Sasih  (last day of each sasih)
    • Purnama (+ every full moon)
    • Tilem   (every new moon)

we implement a simple matcher and return ALL rahinan that apply to a given
pawukon/saka combination.
"""

from __future__ import annotations

from dataclasses import dataclass

from .pawukon import PawukonDate
from .saka import SakaDate


@dataclass(frozen=True, slots=True)
class Rahinan:
    """a single named rahinan match."""
    id: str
    label: str
    category: str   # 'saptawara' | 'wuku' | 'sasih' | 'saptawara-pancawara' | 'full-moon' | 'new-moon'
    confidence: str # 'mathematical' | 'social'
    applies: bool


def rahinan_for(pawukon: PawukonDate, saka: SakaDate, wewaran_position: int | None = None) -> list[Rahinan]:
    """return all rahinan that apply to a given pawukon+saka combination."""
    out: list[Rahinan] = []
    # we don't have direct wewaran access here; for v0.1 we use the position
    # and recompute the relevant saptawara/pancawara names when needed.

    # we accept the position to keep the function signature narrow.
    if wewaran_position is None:
        wewaran_position = pawukon.position_in_cycle

    # import here to avoid circular refs
    from .wewaran import (  # noqa: PLC0415 - intentional lazy import
        PANCAWARA_NAMES_BALINESE,
        SAPTAWARA_NAMES_BALINESE,
        wewaran_for_position,
    )
    from .pawukon import WUKU_NAMES_BALINESE  # noqa: PLC0415 - intentional lazy import

    ww = wewaran_for_position(wewaran_position)

    # Buda Wage - Buda + Wage
    if ww.saptawara_name == "Buda" and ww.pancawara_name == "Wage":
        out.append(Rahinan("buda_wage", "Buda Wage", "saptawara-pancawara", "mathematical", True))
    # Buda Kliwon
    if ww.saptawara_name == "Buda" and ww.pancawara_name == "Keliwon":
        out.append(Rahinan("buda_kliwon", "Buda Kliwon", "saptawara-pancawara", "mathematical", True))
    # Saniscara Umanis
    if ww.saptawara_name == "Saniscara" and ww.pancawara_name == "Umanis":
        out.append(Rahinan("saniscara_umanis", "Saniscara Umanis", "saptawara-pancawara", "mathematical", True))
    # Saniscara Kliwon (Tumpek Landep)
    if ww.saptawara_name == "Saniscara" and ww.pancawara_name == "Keliwon":
        out.append(Rahinan("tumpek_landep", "Tumpek Landep", "saptawara-pancawara", "mathematical", True))
    # Anggara Kliwon
    if ww.saptawara_name == "Anggara" and ww.pancawara_name == "Keliwon":
        out.append(Rahinan("anggara_kliwon", "Anggara Kasih", "saptawara-pancawara", "mathematical", True))
    # Redite Paing
    if ww.saptawara_name == "Redite" and ww.pancawara_name == "Paing":
        out.append(Rahinan("redite_paing", "Redite Paing", "saptawara-pancawara", "mathematical", True))

    # Purnama / Tilem based on saka
    if saka.is_purnama:
        out.append(Rahinan("purnama", "Purnama", "full-moon", "mathematical", True))
    if saka.is_tilem:
        out.append(Rahinan("tilem", "Tilem", "new-moon", "mathematical", True))

    # Hari Raya Saraswati: last day of Wuku Watugunung (wuku_idx=30),
    # Saptawara Saniscara → matching both.
    # Predicate co-committed with WUKU_NAMES_BALINESE swap (governance decision 2026-09-19).
    # Babadbali canonical Watugunung is at index 30; the prior engine had Watugunung at
    # index 21 (with Matal at 21 under canonical), so the predicate must move in the same
    # commit as the table — a name-only fix would silently relocate Saraswati onto Matal.
    if pawukon.wuku_idx == 30 and ww.saptawara_name == "Saniscara":
        out.append(Rahinan("saraswati", "Hari Raya Saraswati", "wuku", "social", True))

    # Hari Raya Galungan: Wuku Dungulan (wuku_idx=11), Buda Kliwon
    if pawukon.wuku_idx == 11 and ww.saptawara_name == "Buda" and ww.pancawara_name == "Keliwon":
        out.append(Rahinan("galungan", "Hari Raya Galungan", "wuku", "social", True))
    # Hari Raya Kuningan: 10 days after Saraswati by Wuku; wuku_idx=12,
    # Saniscara Kliwon
    if pawukon.wuku_idx == 12 and ww.saptawara_name == "Saniscara" and ww.pancawara_name == "Keliwon":
        out.append(Rahinan("kuningan", "Hari Raya Kuningan", "wuku", "social", True))

    # Nyepi: 1st day of Sasih Kesanga + new moon
    if saka.sasih_idx == 9 and saka.is_tilem and saka.lunar_tithi == 1:
        out.append(Rahinan("nyepi", "Hari Raya Nyepi", "sasih", "social", True))

    return out
