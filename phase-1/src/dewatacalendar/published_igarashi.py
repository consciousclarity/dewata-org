"""Igarashi 1999 — cross-validation corpus (re-exported via cross_validation)."""

from __future__ import annotations

import json
from pathlib import Path


CORPUS_PATH = Path(__file__).resolve().parent / "igarashi_1999.json"


def load_igarashi_corpus() -> list[dict]:
    """load the Igarashi corpus from disk."""
    if not CORPUS_PATH.exists():
        return []
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
