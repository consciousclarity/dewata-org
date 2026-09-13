"""wewaran — 10 concurrent weeks running through the 210-day cycle.

the cycle's natural weeks are 1, 2, 3, 5, 6, 7 days (factors of 210).
the 4-, 8-, 9-, 10-day weeks are *derived* and require derivation via the
*urip* (life-value) arithmetic described in:

    Dershowitz & Reingold, *Calendrical Calculations*, ch. 11.
    Wikipedia: Pawukon calendar.

derivation ruleset:

  5-day week (Pancawara):
      urip_5 = [9, 7, 4, 8, 5]
      cycle for cycle_pos p in 1..210:
        pancawara = (((p - 1) % 5) + 1) → look up name

  7-day week (Saptawara):
      urip_7 = [5, 4, 3, 7, 8, 6, 9]
      saptawara = (((p - 1) % 7) + 1) → look up name

  10-day week (Dasa Wara):
      urip_10 = [5, 2, 8, 6, 4, 7, 10, 3, 9, 1]
      dasa = ((urip_5_index + urip_7_index) + 1) % 10, then look up by urip match
      (the urip match isn't sequential; we sum to compute it.)

  the other weeks (1, 2, 3, 4, 6, 8, 9):
      simpler modular arithmetic.

all weeks are reproducible from cycle position. determinism: yes.

note on the 4-, 8-, 9-day weeks: because 210 is not divisible by 4, 8, or 9,
the actual cycle for these weeks repeats day-positions within the 210-day
window. Specifically the 4-day and 8-day weeks add an extra repetition
around the 72-day boundary; the 9-day week repeats its first day 3 times
in the first week of the cycle. we compute that as a derived offset in the
`week_4`, `week_8`, `week_9` fields below.
"""

from __future__ import annotations

from dataclasses import dataclass

# 30 Wuku names repeat every 7 wuku-days (one full wuku).
# Indexed by Pawukon position 1..210 with `(p - 1) // 7`.

# Pancawara (5-day week)
PANCAWARA_NAMES_BALINESE: tuple[str, ...] = ("Paing", "Pon", "Wage", "Keliwon", "Umanis")
URIP_5: tuple[int, ...] = (9, 7, 4, 8, 5)

# Saptawara (7-day week)
SAPTAWARA_NAMES_BALINESE: tuple[str, ...] = (
    "Redite", "Soma", "Anggara", "Buda", "Wraspati", "Sukra", "Saniscara",
)
URIP_7: tuple[int, ...] = (5, 4, 3, 7, 8, 6, 9)

# Dasa Wara (10-day week). urip = [5, 2, 8, 6, 4, 7, 10, 3, 9, 1] — NOT sequential.
DASAWARA_NAMES_BALINESE: tuple[str, ...] = (
    "Sri", "Patra", "Pade", "Suka", "Duka", "Sri", "Manuh", "Pati", "Pujut", "Kala",
)
URIP_10: tuple[int, ...] = (5, 2, 8, 6, 4, 7, 10, 3, 9, 1)

# Sadwara (6-day week)
SADWARA_NAMES_BALINESE: tuple[str, ...] = ("Tungleh", "Aryang", "Urukung", "Paniron", "Was", "Maulu")

# Caturwara (4-day week, with repetition around day 72)
CATURWARA_NAMES_BALINESE: tuple[str, ...] = ("Sri", "Laba", "Jaya", "Menala")

# Asta Wara (8-day week, with repetition around day 72)
ASTAWARA_NAMES_BALINESE: tuple[str, ...] = ("Sri", "Indra", "Guru", "Yama", "Lingga", "Karngin", "Ma", "Pitra")

# Sangawara (9-day week, with first day repeated 3x in days 1..9)
SANGAWARA_NAMES_BALINESE: tuple[str, ...] = ("Dangu", "Jangur", "Gulma", "Toroh", "Klisura", "Buku", "ulu", "Ratu", "Dadi")

# Triwara (3-day week)
TRIWARA_NAMES_BALINESE: tuple[str, ...] = ("Pasah", "Beteng", "Kajeng")

# Dwiwara (2-day week). derived from dasa-wara urip sum: even → Pepet, odd → Menga.
# Ekawara (1-day week). derived: when the urip value is odd, the day exists.

# urip values for 5-day and 7-day
@dataclass(frozen=True, slots=True)
class Wewaran:
    """wewaran positions for a single pawukon cycle-day."""
    position: int                  # [1..210]
    # cycle-synchronous weeks (factors of 210)
    pancawara_idx: int             # [1..5]
    pancawara_name: str
    saptawara_idx: int             # [1..7]
    saptawara_name: str
    sadwara_idx: int               # [1..6]
    sadwara_name: str
    triwara_idx: int               # [1..3]
    triwara_name: str
    # derived weeks
    dasawara_idx: int              # [1..10]
    dasawara_name: str
    dasawara_urip: int             # the urip match used
    caturwara_idx: int             # [1..4]
    caturwara_name: str
    astawara_idx: int              # [1..8]
    astawara_name: str
    sangawara_idx: int             # [1..9]
    sangawara_name: str
    dwiwara_name: str              # 'Menga' or 'Pepet'
    ekawara_present: bool          # false means no ekawara (raw void)


def _repeating_4(p: int) -> int:
    """4-day week with repetition around day 72.

    210 / 4 = 52.5, so the 4-day week can't fit cleanly. the convention
    (per Dershowitz & Reingold) is that the penultimate day repeats in
    the week that would otherwise end on day 72. Day 72 → 'Laba' first
    occurrence + 'Laba' second occurrence (so day 72 = Laba, day 73 = Jaya)."""
    if p == 72:
        return 3
    if p == 73:
        return 4
    return ((p - 1) % 4) + 1 if p < 72 else ((p - 1) % 4) + 1  # noqa: PLR2004 - remove the special case, but keep sym.


def _repeating_8(p: int) -> int:
    """8-day week with repetition around day 72."""
    if p == 72:
        return 7
    if p == 73:
        return 8
    return ((p - 1) % 8) + 1


def _repeating_9(p: int) -> int:
    """9-day week: first day repeats 3x in days 1..3 of the cycle.

    9-day arithmetic doesn't fit 210 cleanly. the convention: day 1..3
    all map to position 1 (Dangu)."""
    if p == 1 or p == 2 or p == 3:
        return 1
    return ((p - 1) % 9) + 1


def wewaran_for_position(position: int) -> Wewaran:
    """compute wewaran for a given pawukon cycle position [1..210]."""
    if not 1 <= position <= 210:
        raise ValueError(f"position out of range: {position}")

    # cycle-synchronous
    pancawara_idx = ((position - 1) % 5) + 1
    saptawara_idx = ((position - 1) % 7) + 1
    sadwara_idx = ((position - 1) % 6) + 1
    triwara_idx = ((position - 1) % 3) + 1

    # derived: urip sum of pancawara + saptawara + 1, look up in urip_10
    urip_5_value = URIP_5[pancawara_idx - 1]
    urip_7_value = URIP_7[saptawara_idx - 1]
    urip_sum = (urip_5_value + urip_7_value + 1) % 10  # noqa: PLR2004 - Dershowitz formula
    if urip_sum == 0:
        urip_sum = 10
    try:
        dasawara_idx = URIP_10.index(urip_sum) + 1
    except ValueError as exc:
        raise RuntimeError(  # noqa: TRY003 - defensive, should never happen
            f"urip lookup failed: 5={urip_5_value} 7={urip_7_value} sum={urip_sum}",
        ) from exc

    # caturwara, astawara, sangawara use repeating arithmetic
    caturwara_idx = _repeating_4(position)
    astawara_idx = _repeating_8(position)
    sangawara_idx = _repeating_9(position)

    # dwiwara: even → Pepet, odd → Menga (based on dasawara urip sum)
    dwiwara_name = "Pepet" if urip_sum % 2 == 0 else "Menga"
    ekawara_present = urip_sum % 2 == 1

    return Wewaran(
        position=position,
        pancawara_idx=pancawara_idx,
        pancawara_name=PANCAWARA_NAMES_BALINESE[pancawara_idx - 1],
        saptawara_idx=saptawara_idx,
        saptawara_name=SAPTAWARA_NAMES_BALINESE[saptawara_idx - 1],
        sadwara_idx=sadwara_idx,
        sadwara_name=SADWARA_NAMES_BALINESE[sadwara_idx - 1],
        triwara_idx=triwara_idx,
        triwara_name=TRIWARA_NAMES_BALINESE[triwara_idx - 1],
        dasawara_idx=dasawara_idx,
        dasawara_name=DASAWARA_NAMES_BALINESE[dasawara_idx - 1],
        dasawara_urip=urip_sum,
        caturwara_idx=caturwara_idx,
        caturwara_name=CATURWARA_NAMES_BALINESE[caturwara_idx - 1],
        astawara_idx=astawara_idx,
        astawara_name=ASTAWARA_NAMES_BALINESE[astawara_idx - 1],
        sangawara_idx=sangawara_idx,
        sangawara_name=SANGAWARA_NAMES_BALINESE[sangawara_idx - 1],
        dwiwara_name=dwiwara_name,
        ekawara_present=ekawara_present,
    )
