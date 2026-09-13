"""Cunningham 1994 — cross-validation corpus (re-exported via cross_validation)."""

from __future__ import annotations

import json
from pathlib import Path


CORPUS_PATH = Path(__file__).resolve().parent / "cunningham_1994.json"


def load_cunningham_corpus() -> list[dict]:
    """load the Cunningham corpus from disk. each item is a dict with: gregorian, pawukon_position, pawukon_wuku_idx, saka_year, sasih_idx, source, page, rule_id."""
    if not CORPUS_PATH.exists():
        return []
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
