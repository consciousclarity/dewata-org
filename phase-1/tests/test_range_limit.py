"""tests for the bounded /dsp/v0.1/calendar/range endpoint.

run with: `python -m pytest tests/test_range_limit.py -q`
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _client() -> TestClient:
    from api.main import create_app
    return TestClient(create_app())


def _get_range(app_client: TestClient, start: str, end: str, fmt: str = "json"):
    return app_client.get(
        "/dsp/v0.1/calendar/range",
        params={"start": start, "end": end, "fmt": fmt},
    )


# ---------------------------------------------------------------------------
# configuration-parser tests
# ---------------------------------------------------------------------------
#
# The range cap is resolved from `DEWATA_MAX_RANGE_DAYS` once at module
# import time. The function `_resolve_max_range_days()` is itself a
# pure environment-reader: it does not modify the module state and
# does not reload the module. We test it directly here, with the env
# var monkey-patched per case, and assert the integer it returns.
#
# These cases preserve the prior contract: any value outside the
# inclusive range [1, 366] (including unset, empty, non-integer, <= 0,
# and > 366) falls back to the default 366.

_PARSER_CASES = [
    # (env_value, expected_cap, label)
    ("__unset__",     "366", "unset -> default"),
    ("",              "366", "empty -> default"),
    ("abc",           "366", "non-integer -> default"),
    ("1.5",           "366", "float string -> default"),
    ("0",             "366", "zero -> default"),
    ("-5",            "366", "negative -> default"),
    ("367",           "366", "above ceiling -> default"),
    ("730",           "366", "above ceiling -> default"),
    ("1000",          "366", "above ceiling -> default"),
    ("36600",         "366", "above ceiling -> default"),
    ("100000",        "366", "above ceiling -> default"),
    ("366",           "366", "ceiling accepted"),
    ("365",           "365", "lower than ceiling accepted"),
    ("200",           "200", "mid-range accepted"),
    ("1",             "1",   "minimum accepted"),
]


def _set_env(monkeypatch, raw):
    """set DEWATA_MAX_RANGE_DAYS to `raw`, or unset if `raw == "__unset__"`."""
    if raw == "__unset__":
        monkeypatch.delenv("DEWATA_MAX_RANGE_DAYS", raising=False)
    else:
        monkeypatch.setenv("DEWATA_MAX_RANGE_DAYS", raw)


@pytest.mark.parametrize(
    "raw,expected,reason",
    _PARSER_CASES,
    ids=[c[0] for c in _PARSER_CASES],
)
def test_resolve_max_range_days_parser_outcome(monkeypatch, raw, expected, reason):
    """the env-var parser returns 366 for any value outside
    [1, 366] inclusive (including unset)."""
    from dewatacalendar import dsp as dsp_mod
    _set_env(monkeypatch, raw)
    actual = dsp_mod._resolve_max_range_days()
    assert actual == int(expected), (
        f"env={raw!r} expected {expected} got {actual} — {reason}"
    )


def test_resolve_max_range_days_does_not_mutate_module_state(monkeypatch):
    """calling _resolve_max_range_days() must not modify the
    module-level `_MAX_RANGE_DAYS` constant or otherwise alter
    module state."""
    from dewatacalendar import dsp as dsp_mod
    before = dsp_mod._MAX_RANGE_DAYS
    # set an env var that would normally change the resolved value
    monkeypatch.setenv("DEWATA_MAX_RANGE_DAYS", "10")
    _ = dsp_mod._resolve_max_range_days()
    monkeypatch.delenv("DEWATA_MAX_RANGE_DAYS", raising=False)
    _ = dsp_mod._resolve_max_range_days()
    after = dsp_mod._MAX_RANGE_DAYS
    assert before == after, (
        f"_MAX_RANGE_DAYS mutated across parser calls: {before} -> {after}"
    )


# ---------------------------------------------------------------------------
# endpoint behaviour, exercised via FastAPI TestClient
# ---------------------------------------------------------------------------

def test_one_day_range_succeeds_and_items_has_length_one():
    with _client() as c:
        r = _get_range(c, "2026-09-07", "2026-09-07")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["start"] == "2026-09-07"
    assert body["end"] == "2026-09-07"
    assert body["count"] == 1
    assert isinstance(body["items"], list) and len(body["items"]) == 1


def test_exactly_366_inclusive_days_succeeds():
    # 2024 is a leap year; 2024-01-01 .. 2024-12-31 = 366 days inclusive
    with _client() as c:
        r = _get_range(c, "2024-01-01", "2024-12-31")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 366
    assert len(body["items"]) == 366


def test_367_inclusive_days_is_rejected_with_413_and_stable_body():
    # 2024-01-01 .. 2025-01-01 inclusive = 367 days
    with _client() as c:
        r = _get_range(c, "2024-01-01", "2025-01-01")
    assert r.status_code == 413, r.text
    body = r.json()
    assert body == {
        "detail": {
            "error": "range_too_large",
            "code": "RANGE_LIMIT_EXCEEDED",
            "max_days": 366,
            "requested_days": 367,
        }
    }


def test_730_day_request_is_rejected_with_413_max_366():
    # 730 days is approximately two years (1900-01-01 .. 1901-12-31
    # inclusive) — must be capped at the 366-day safety ceiling even
    # though a 730-day window is arithmetically valid.
    with _client() as c:
        r = _get_range(c, "1900-01-01", "1901-12-31")
    assert r.status_code == 413, r.text
    body = r.json()
    assert body == {
        "detail": {
            "error": "range_too_large",
            "code": "RANGE_LIMIT_EXCEEDED",
            "max_days": 366,
            "requested_days": 730,
        }
    }


def test_reversed_range_is_rejected_with_400_and_stable_id():
    with _client() as c:
        r = _get_range(c, "2026-09-15", "2026-09-01")
    assert r.status_code == 400, r.text
    body = r.json()
    assert body["detail"]["error"] == "range_reversed"
    assert body["detail"]["message"] == "end before start"


def test_same_day_range_does_not_trip_reversed_check():
    with _client() as c:
        r = _get_range(c, "2026-09-07", "2026-09-07")
    assert r.status_code == 200, r.text


def test_malformed_start_pattern_invalid_is_422():
    """`start=not-a-date` fails FastAPI's `Query(pattern=...)` and
    yields the standard FastAPI 422 validation envelope."""
    with _client() as c:
        r = _get_range(c, "not-a-date", "2026-09-07")
    assert r.status_code == 422, r.text
    body = r.json()
    # FastAPI's default 422 envelope. We only assert the shape, not
    # internal field names (those are FastAPI's contract, not ours).
    assert "detail" in body
    # it must not leak internal paths/secrets/exceptions
    body_str = str(body)
    for token in ("/opt/", "/root/.env", "Traceback", "Exception", "engine/", "invalid literal for"):
        assert token not in body_str, f"leaked internal token {token!r} in {body_str}"


def test_malformed_start_pattern_valid_but_nonexistent_is_400():
    """`start=2026-09-99` passes the regex (it looks like YYYY-MM-DD
    but is not a real calendar day) and falls through to my explicit
    400 handler. The body must show the fixed stable message — not
    Python's `ValueError` text."""
    with _client() as c:
        r = _get_range(c, "2026-09-99", "2026-12-31")
    assert r.status_code == 400, r.text
    body = r.json()
    assert body == {
        "detail": {
            "error": "invalid_date",
            "field": "start",
            "message": "must be a valid Gregorian date in YYYY-MM-DD format",
        }
    }


def test_malformed_end_pattern_valid_but_nonexistent_is_400():
    with _client() as c:
        r = _get_range(c, "2026-09-01", "2026-09-99")
    assert r.status_code == 400, r.text
    body = r.json()
    assert body == {
        "detail": {
            "error": "invalid_date",
            "field": "end",
            "message": "must be a valid Gregorian date in YYYY-MM-DD format",
        }
    }


def test_leap_year_full_year_is_exactly_366_days():
    # 2024 is a leap year; 2024-01-01..2024-12-31 must yield exactly 366.
    with _client() as c:
        r = _get_range(c, "2024-01-01", "2024-12-31")
    assert r.status_code == 200
    assert r.json()["count"] == 366


def test_response_format_unchanged_for_valid_range():
    """previous callers expect {start, end, count, items} with items
    being an array of full CalendarDay dicts."""
    with _client() as c:
        r = _get_range(c, "2026-09-01", "2026-09-03")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"start", "end", "count", "items"}
    sample = body["items"][0]
    assert {"gregorian", "ruleset", "saka", "pawukon", "wewaran", "rahinan"} <= set(sample.keys())


def test_jsonl_format_shape_preserved():
    """the fmt=jsonl body shape is preserved from the original
    implementation: FastAPI sees the handler's `str` return and
    JSON-serialises it once, producing a single JSON string. A
    follow-up could switch the handler to `PlainTextResponse` for
    a stream-of-records wire format; that change is out of scope
    here."""
    with _client() as c:
        r = _get_range(c, "2026-09-01", "2026-09-02", fmt="jsonl")
    assert r.status_code == 200
    parsed = r.json()
    assert isinstance(parsed, str)
    assert "2026-09-01" in parsed
    assert "2026-09-02" in parsed


def test_single_date_endpoint_unaffected():
    with _client() as c:
        r = c.get("/dsp/v0.1/calendar/date/2026-09-07")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["gregorian"] == "2026-09-07"
    assert "ruleset" in body
