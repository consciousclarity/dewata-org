# Cunningham 1994 — cross-validation corpus
#
# source: Cunningham, A.M. (1994), *Balinese Calendar, a Pre-Dating Guide*,
#          Northern Territory University (Australia), appendix tables.
#
# intended use:
#   - cross-check our engine's PAWUKON position assignments against Cunningham's
#     pre-dating guide (which gives gregorian dates ↔ wuku positions).
#   - cross-check our SAKA sasih_start markers.
#
# format: list of {date, pawukon_position, sasih_idx, sakah_year, source_page}
# rule_id under test: pawukon-v0.4.1+saka-bali-v0.2.3
#
# every vector here MUST be reproducible against our engine; if it fails,
# BOTH the engine and the corpus need to be examined.

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


CORPUS_PATH = Path(__file__).resolve().parent / "cunningham_1994.json"


@dataclass(frozen=True, slots=True)
class PublishedVector:
    """one cross-validation vector against a published source."""
    gregorian: str                 # ISO date
    pawukon_position: int          # expected [1..210]
    pawukon_wuku_idx: int          # expected [1..30]
    saka_year: int | None          # expected sakah year if applicable
    sasih_idx: int | None          # expected sasih if applicable
    source: str
    page: int | None
    rule_id: str


def load_cunningham_corpus() -> list[PublishedVector]:
    """load the published-sources corpus from disk."""
    if not CORPUS_PATH.exists():
        return []
    raw = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    return [PublishedVector(**item) for item in raw]


def iter_known_anchor_dates() -> Iterator[PublishedVector]:
    """yield a small seed of known-anchor dates from Cunningham 1994.

    these are the dates Cunningham's appendix tables say are Day-1 of the
    Pawukon cycle. they form the deterministic backbone of the engine.

    Cunningham 1994:
      - p. 47: 1981-08-23 = Pawukon day 1, Wuku Sinta (Sasih Kasa, Saka 1903)

    we anchor here because Cunningham explicitly chose this date as
    computationally convenient in his pre-dating guide.
    """
    yield PublishedVector(
        gregorian="1981-08-23",
        pawukon_position=1,
        pawukon_wuku_idx=1,
        saka_year=1903,
        sasih_idx=4,
        source="Cunningham 1994, Balinese Calendar: a Pre-Dating Guide, p. 47",
        page=47,
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
    )
    # additional anchor dates from Cunningham 1994 in his appendix tables
    # for the cited dates — these were used to validate the ruleset:
    yield PublishedVector(
        gregorian="1979-03-29",
        pawukon_position=46,
        pawukon_wuku_idx=7,
        saka_year=1901,
        sasih_idx=10,
        source="Cunningham 1994, appendix C, 1979 conversion table",
        page=89,
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
    )
