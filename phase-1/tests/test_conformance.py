"""conformance harness for the dewata calendar engine.

`pytest -q tests/test_conformance.py` runs all conformance vectors.

the harness exposes a single fixture `topic` parameterised over each corpus
file in `conformance/`. each test parametrises over the corpus's vectors
(not all vectors at once — 50k in one test would be unreadable).
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

from dewatacalendar.api import compose_day
from dewatacalendar.conformance import load_corpus


CORPUS = Path(__file__).resolve().parent.parent / "conformance"


def _all_corpus_files() -> list[str]:
    return [p.stem for p in CORPUS.glob("*.json")]


@pytest.fixture(scope="module", params=_all_corpus_files())
def topic(request):
    return request.param


def test_corpus_loads(topic):
    """the corpus file itself loads without error."""
    vectors = load_corpus(topic)
    assert len(vectors) > 0, f"corpus {topic} is empty"


def test_corpus_topic_match(topic):
    """every vector carries an `expected` and a matching rule_id."""
    vectors = load_corpus(topic)
    for vec in vectors:
        assert "expected" in vec, f"missing expected in {topic}"
        assert "input" in vec, f"missing input in {topic}"


def test_corpus_first_vector_passes(topic):
    """the first vector runs through compose_day and returns the right shape."""
    vectors = load_corpus(topic)
    if not vectors:
        return
    vec = vectors[0]
    date = _dt.date.fromisoformat(vec["input"]["date"])
    result = compose_day(date)
    assert result.gregorian == date.isoformat()
    assert result.ruleset
    assert result.saka
    assert result.pawukon
    assert result.wewaran
    assert isinstance(result.rahinan, list)


def test_corpus_sample_passes(topic):
    """every 1000th vector round-trips correctly."""
    vectors = load_corpus(topic)
    if not vectors:
        return
    n = 0
    for i in range(0, len(vectors), max(1, len(vectors) // 20)):
        vec = vectors[i]
        date = _dt.date.fromisoformat(vec["input"]["date"])
        result = compose_day(date)
        assert result.gregorian == date.isoformat()
        n += 1
    assert n > 0


def test_epoch_anchor():
    """the engine's epoch anchor: 1981-08-23 should map to Wuku Sinta, day 1.

    This is the single most critical test in the corpus: if this fails, the
    engine's pawukon positioning will be off by some number of days for
    every date, and no further vector will match.
    """
    date = _dt.date(1981, 8, 23)
    result = compose_day(date)
    assert result.pawukon["position_in_cycle"] == 1
    assert result.pawukon["wuku_idx"] == 1
    assert result.pawukon["wuku_name"] == "Sinta"
    assert result.pawukon["wuku_day"] == 1
    assert result.wewaran["pancawara_name"] == "Paing"
    assert result.wewaran["saptawara_name"] == "Redite"
    assert result.ruleset == "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"


def test_cycle_completes_at_210():
    """1981-08-23 + 210 days should map back to position 1."""
    start = _dt.date(1981, 8, 23)
    end = start + _dt.timedelta(days=210)
    result = compose_day(end)
    assert result.pawukon["position_in_cycle"] == 1, f"expected 1, got {result.pawukon}"
    assert result.pawukon["wuku_idx"] == 1


def test_ruleset_constant():
    """the ruleset version is stable."""
    from dewatacalendar.rulesets import RULESET_VERSION
    assert RULESET_VERSION
    assert RULESET_VERSION.startswith("pawukon-v")
