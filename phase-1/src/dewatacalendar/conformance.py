"""conformance corpus loader + runner.

the corpus is a JSONL file at /opt/dewata.online/phase-1/conformance/<topic>.jsonl
or .json. each line is a JSON object:

  {
    "input":  { "date": "YYYY-MM-DD" },
    "expected": { "field": value, ... },
    "topic": "pawukon",
    "rule_id": "pawukon-v0.4.1",
    "history_source": "Cunningham 1994 / Igarashi / publ"
  }

the harness loads each file, runs `compose_day` (or a topic-specific function),
asserts the output matches expected, and emits a pass/fail summary.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Callable, Iterable

from .api import compose_day


CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "conformance"


def load_corpus(topic: str) -> list[dict]:
    """load conformance vectors for a topic. returns list of dicts."""
    path = CORPUS_DIR / f"{topic}.json"
    if not path.exists():
        path = CORPUS_DIR / f"{topic}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no corpus file for topic: {topic}")
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, dict) and "vectors" in data:
        return data["vectors"]
    if isinstance(data, list):
        return data
    raise ValueError(f"unknown corpus format for {topic}")


def _check_value(actual: object, expected: object, path: str, errors: list[str]) -> bool:
    """recurse-compare; errors collect mismatches with a dotted path."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        ok = True
        for k, v in expected.items():
            if k not in actual:
                errors.append(f"{path}.{k}: missing key")
                ok = False
                continue
            if not _check_value(actual[k], v, f"{path}.{k}", errors):
                ok = False
        return ok
    if isinstance(expected, list) and isinstance(actual, list):
        # for lists, compare sorted JSON-equality
        if len(expected) != len(actual):
            errors.append(f"{path}: length mismatch {len(expected)} vs {len(actual)}")
            return False
        return all(_check_value(a, e, f"{path}[]", errors) for a, e in zip(actual, expected))
    if actual != expected:
        errors.append(f"{path}: actual={actual!r} expected={expected!r}")
        return False
    return True


def run_corpus(topic: str, *, on_date: Callable[[_dt.date], object] | None = None) -> tuple[int, int, list[str]]:
    """run conformance vectors for a topic. returns (passed, total, errors)."""
    vectors = load_corpus(topic)
    if on_date is None:
        on_date = compose_day

    passed = 0
    failures: list[str] = []
    for i, vec in enumerate(vectors):
        d = _dt.date.fromisoformat(vec["input"]["date"])
        expected = vec.get("expected", {})
        result = on_date(d)
        if hasattr(result, "__dataclass_fields__"):
            from dataclasses import asdict  # noqa: PLC0415 - lazy
            result = asdict(result)
        errors: list[str] = []
        if _check_value(result, expected, "root", errors):
            passed += 1
        else:
            failures.append(f"#{i} {vec['input']['date']}: {' / '.join(errors)}")
    return passed, len(vectors), failures
