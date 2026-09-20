"""Round-2 finding 2 tests: separate public validation from diagnostic comparisons.

The corrections-only follow-up (commit 1018721) introduced a
diagnostic field `saka_year_diagnostic_january_rollover` for the
harness and dispute packet. Cross-validation then used the diagnostic
field as a substitute for the unavailable public `saka_year`,
producing `fields_ok.saka_year=True` and `status="match"` when
diagnostic matched expected. Codex flagged this as round-2 finding 2:

  Stop treating diagnostic agreement as successful validation of
  the public field. Keep actual.saka_year=None. Represent a
  required but unavailable year explicitly in structured output,
  separately from any diagnostic comparison. Do not claim
  "all fields match" when a required public field is unavailable.
  Preserve the distinction between an unavailable actual value and
  a reference that does not specify an expected value.

The fix:
  - `CrossValidationOutcome.fields_unavailable` records when the
    public field was required by the reference but the engine
    returned None.
  - `CrossValidationOutcome.fields_diagnostic_match` records the
    diagnostic value's comparison with expected; it never feeds
    into `fields_ok` or `status`.
  - `status` is "match" only when every required public field is
    available and agrees. "incomplete_public" if at least one
    required public field was unavailable. "disputed" otherwise.
  - `runbook.classify()` returns `unavailable_public_field` instead
    of `epoch_offset` / `calendar_variant` when the public
    `saka_year` is unavailable.
"""

from __future__ import annotations

import datetime as _dt

import pytest

from dewatacalendar.api import compose_day
from dewatacalendar.cross_validation import cross_validate_one
from dewatacalendar.runbook import classify


# --- Helpers --------------------------------------------------------------

def _diagnostic_value_for(date_iso: str) -> int:
    """read the diagnostic saka_year from compose_day output."""
    day = compose_day(_dt.date.fromisoformat(date_iso))
    return day.saka["saka_year_diagnostic_january_rollover"]


# --- Finding 2 regressions ------------------------------------------------


def test_f2_unavailable_year_is_not_a_match_even_when_diagnostic_matches():
    """Round-2 finding 2: when the public `saka_year` is unavailable,
    a matching diagnostic value MUST NOT produce `status="match"` or
    `fields_ok.saka_year=True`.

    1981-08-23 is in Cunningham 1994 (saka_year=1903, sasih_idx=4).
    The diagnostic for 1981-08-23 returns 1903; the public returns
    None. The outcome must be `incomplete_public`, not `match`, and
    `fields_unavailable.saka_year` must be True.
    """
    expected = {
        "gregorian": "1981-08-23",
        "pawukon_position": 1,
        "pawukon_wuku_idx": 1,
        "saka_year": 1903,
        "sasih_idx": 4,
        "source": "Cunningham 1994, Balinese Calendar: a Pre-Dating Guide, p. 47",
        "page": 47,
        "rule_id": "pawukon-v0.4.1+saka-bali-v0.2.3",
    }
    outcome = cross_validate_one(
        expected_gregorian="1981-08-23",
        expected=expected,
        source="Cunningham 1994, p. 47",
        page=47,
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
        corpus_basename="",
    )

    # Sanity: the diagnostic actually equals expected for this date.
    diag = _diagnostic_value_for("1981-08-23")
    assert diag == 1903, (
        f"diagnostic for 1981-08-23 should equal expected 1903; got {diag}"
    )

    # The structured output must clearly distinguish the unavailable
    # public field from the matching diagnostic.
    assert outcome.fields_unavailable.get("saka_year") is True, (
        f"finding 2: fields_unavailable.saka_year must be True; got "
        f"{outcome.fields_unavailable}"
    )
    assert outcome.fields_ok.get("saka_year") is False, (
        f"finding 2: fields_ok.saka_year must be False when public field "
        f"is unavailable; got {outcome.fields_ok}"
    )
    assert outcome.fields_diagnostic_match.get("saka_year") is True, (
        f"finding 2: diagnostic should be recorded separately and "
        f"match expected; got {outcome.fields_diagnostic_match}"
    )
    assert outcome.actual["saka_year"] is None, (
        f"finding 2: actual.saka_year must remain None; got {outcome.actual['saka_year']}"
    )
    assert outcome.status == "incomplete_public", (
        f"finding 2: status must be incomplete_public; got {outcome.status!r}. "
        f"notes={outcome.notes!r}"
    )
    # The notes must mention the unavailable status, not claim a match.
    assert "unavailable" in outcome.notes.lower(), (
        f"finding 2: notes must mention unavailable; got {outcome.notes!r}"
    )
    assert "all required public fields match" not in outcome.notes.lower(), (
        f"finding 2: notes must NOT claim a public match; got {outcome.notes!r}"
    )


def test_f2_runbook_does_not_classify_unavailability_as_epoch_or_variant():
    """Round-2 finding 2: runbook.classify must NOT classify
    unavailability as `epoch_offset` or `calendar_variant`. It must
    return `unavailable_public_field`.
    """
    expected = {
        "gregorian": "1981-08-23",
        "pawukon_position": 1,
        "pawukon_wuku_idx": 1,
        "saka_year": 1903,
        "sasih_idx": 4,
    }
    outcome = cross_validate_one(
        expected_gregorian="1981-08-23",
        expected=expected,
        source="test",
        page=None,
        rule_id="test",
        corpus_basename="",
    )
    classification, notes = classify(outcome)
    assert classification == "unavailable_public_field", (
        f"finding 2: classification must be unavailable_public_field; "
        f"got {classification!r}. notes={notes!r}"
    )
    assert classification != "epoch_offset"
    assert classification != "calendar_variant"
    assert classification != "rule_drift"
    assert classification != "transcription"


def test_f2_unspecified_expected_year_is_not_unavailable():
    """Round-2 finding 2: when the reference does not specify
    `saka_year` (`expected.saka_year is None`), the public field's
    unavailability does not matter -- the field is not required.

    The status can be "match" if all required fields agree, even when
    the public `saka_year` is None.
    """
    expected = {
        "gregorian": "1981-08-23",
        "pawukon_position": 1,
        "pawukon_wuku_idx": 1,
        # saka_year intentionally omitted from the reference.
        "sasih_idx": 4,
    }
    outcome = cross_validate_one(
        expected_gregorian="1981-08-23",
        expected=expected,
        source="test",
        page=None,
        rule_id="test",
        corpus_basename="",
    )

    # saka_year is not in expected, so fields_unavailable should be empty.
    assert outcome.fields_unavailable == {}, (
        f"finding 2: saka_year unspecified in expected => no unavailability; "
        f"got {outcome.fields_unavailable}"
    )
    # saka_year pass-through: True.
    assert outcome.fields_ok.get("saka_year") is True
    # If all required fields agree, status is match.
    assert outcome.status == "match", (
        f"finding 2: status must be match when required fields agree and "
        f"saka_year unspecified; got {outcome.status!r}. notes={outcome.notes!r}"
    )


def test_f2_incomplete_outcome_status_field_is_incomplete_public():
    """Round-2 finding 2: the status field must literally be the string
    'incomplete_public' (no other variants) when a required field is
    unavailable. The CLI report uses this string directly.
    """
    expected = {
        "gregorian": "1979-03-29",
        "pawukon_position": 46,
        "pawukon_wuku_idx": 7,
        "saka_year": 1901,
        "sasih_idx": 10,
    }
    outcome = cross_validate_one(
        expected_gregorian="1979-03-29",
        expected=expected,
        source="test",
        page=None,
        rule_id="test",
        corpus_basename="",
    )
    assert outcome.status == "incomplete_public"
    assert "match" not in outcome.status, (
        f"finding 2: status must NOT contain 'match' substring; "
        f"got {outcome.status!r}"
    )


def test_f2_all_required_public_fields_available_and_match_yields_match():
    """Round-2 finding 2: when the engine returns a complete public
    field set and they all agree with the reference, status is
    "match" -- unchanged from prior behaviour.
    """
    expected = {
        "gregorian": "1981-08-23",
        "pawukon_position": 1,
        "pawukon_wuku_idx": 1,
        # saka_year unspecified so we don't trigger the unavailable
        # path. The remaining required fields must agree.
        "sasih_idx": 4,
    }
    outcome = cross_validate_one(
        expected_gregorian="1981-08-23",
        expected=expected,
        source="test",
        page=None,
        rule_id="test",
        corpus_basename="",
    )
    assert outcome.status == "match"
    assert outcome.fields_unavailable == {}


def test_f2_incomplete_classification_includes_diagnostic_note():
    """Round-2 finding 2: when classification is
    `unavailable_public_field`, the notes must say whether the
    diagnostic agreed with expected. This is the human-readable
    signal that helps the dispute packet author decide what to do.
    """
    expected = {
        "gregorian": "1981-08-23",
        "pawukon_position": 1,
        "pawukon_wuku_idx": 1,
        "saka_year": 1903,
        "sasih_idx": 4,
    }
    outcome = cross_validate_one(
        expected_gregorian="1981-08-23",
        expected=expected,
        source="test",
        page=None,
        rule_id="test",
        corpus_basename="",
    )
    classification, notes = classify(outcome)
    assert classification == "unavailable_public_field"
    assert "diagnostic" in notes.lower(), (
        f"finding 2: classification notes must mention the diagnostic; "
        f"got {notes!r}"
    )
