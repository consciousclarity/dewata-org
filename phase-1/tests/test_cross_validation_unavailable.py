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
    """Round-2 finding 2 / round-3 precedence:

    The status field is `incomplete_public` ONLY when all AVAILABLE
    required public fields agree with the reference and at least one
    required field is unavailable. The CLI report uses this string
    directly. The fixture below sets pawukon_position, pawukon_wuku_idx,
    and sasih_idx to their actual values for 1981-08-23 (where the
    engine agrees on all available fields and only saka_year is
    unavailable).
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
    assert outcome.status == "incomplete_public", (
        f"status must be incomplete_public for 1981-08-23 with all "
        f"available fields agreeing; got {outcome.status!r}. "
        f"fields_ok={outcome.fields_ok} "
        f"fields_unavailable={outcome.fields_unavailable} "
        f"fields_disagree_available={outcome.fields_disagree_available}"
    )
    assert "match" not in outcome.status, (
        f"finding 2: status must NOT contain 'match' substring; "
        f"got {outcome.status!r}"
    )
    # Disagree-available must be empty: no available field disagrees.
    assert not any(outcome.fields_disagree_available.values()), (
        f"incomplete_public requires no available-field disagreements; "
        f"got {outcome.fields_disagree_available}"
    )


def test_round3_unavailable_does_not_hide_disagreement():
    """Round-3 precedence correction (Codex finding):

    A required unavailable `saka_year` MUST NOT hide substantive
    disagreements on other available fields. 1979-03-29 is in the
    Cunningham 1994 corpus with expected saka_year=1901; the public
    engine returns saka_year=None, but pawukon_position, pawukon_wuku_idx,
    and sasih_idx also disagree with the reference. The status must be
    `disputed`, NOT `incomplete_public`. The diagnostic value (also
    1901 in the harness) MUST NOT satisfy the public contract.

    This regression guard catches the round-2 defect where unavailability
    on one field collapsed all disagreement into `unavailable_public_field`.
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
        source="Cunningham 1994, p. 47",
        page=47,
        rule_id="pawukon-v0.4.1+saka-bali-v0.2.3",
        corpus_basename="",
    )

    # 1. The diagnostic does NOT satisfy saka_year.
    assert outcome.fields_ok.get("saka_year") is False, (
        f"round 3: diagnostic must not satisfy public saka_year; "
        f"got {outcome.fields_ok}"
    )
    assert outcome.fields_unavailable.get("saka_year") is True, (
        f"round 3: public saka_year must remain unavailable; "
        f"got {outcome.fields_unavailable}"
    )
    assert outcome.actual.get("saka_year") is None, (
        f"round 3: actual.saka_year must remain None; "
        f"got {outcome.actual.get('saka_year')!r}"
    )
    # Diagnostic agreement is recorded separately and is True here
    # (the diagnostic for 1979-03-29 equals 1901).
    assert outcome.fields_diagnostic_match.get("saka_year") is True, (
        f"round 3: diagnostic agreement must be recorded; "
        f"got {outcome.fields_diagnostic_match}"
    )

    # 2. The independent disagreement remains visible.
    assert outcome.fields_disagree_available.get("pawukon_position") is True
    assert outcome.fields_disagree_available.get("pawukon_wuku_idx") is True
    assert outcome.fields_disagree_available.get("sasih_idx") is True

    # 3. status is disputed, NOT incomplete_public.
    assert outcome.status == "disputed", (
        f"round 3: status must be disputed when available fields "
        f"disagree; got {outcome.status!r}. notes={outcome.notes!r}"
    )

    # 4. Notes expose both facts: the disagreement and the unavailability.
    notes_lower = outcome.notes.lower()
    assert "pawukon_position" in outcome.notes, (
        f"round 3: notes must list pawukon_position as a disagreeing "
        f"available field; got {outcome.notes!r}"
    )
    assert "pawukon_wuku_idx" in outcome.notes
    assert "sasih_idx" in outcome.notes
    assert "saka_year" in outcome.notes.lower(), (
        f"round 3: notes must mention saka_year unavailability; "
        f"got {outcome.notes!r}"
    )
    assert "unavailable" in notes_lower, (
        f"round 3: notes must mention unavailable; got {outcome.notes!r}"
    )

    # 5. runbook.classify yields rule_drift (pawukon disagreement on
    #    available fields), not unavailable_public_field. The
    #    classification notes add saka_year unavailability.
    from dewatacalendar.runbook import classify
    classification, classification_notes = classify(outcome)
    assert classification == "rule_drift", (
        f"round 3: classification must be rule_drift when pawukon "
        f"disagrees on available fields; got {classification!r}. "
        f"notes={classification_notes!r}"
    )
    assert "saka_year" in classification_notes.lower(), (
        f"round 3: classification notes must mention saka_year "
        f"unavailability addendum; got {classification_notes!r}"
    )
    assert "unavailable" in classification_notes.lower(), (
        f"round 3: classification notes must mention unavailable; "
        f"got {classification_notes!r}"
    )


def test_round3_cross_validate_all_does_not_silently_become_zero_disputed():
    """Round-3 aggregate guard:

    `cross_validate_all()` over the current v0.1 corpora must not
    silently become `0 disputed, 3 incomplete` again. With the round-3
    precedence, the 1979-03-29 and 2024-09-07 rows are `disputed` and
    the 1981-08-23 row is `incomplete_public`. The aggregate is
    `2 disputed, 1 incomplete_public`, with 3 rows total having
    `unavailable_fields`.
    """
    from dewatacalendar.cross_validation import cross_validate_all
    results = cross_validate_all()
    n_match = sum(1 for r in results if r.status == "match")
    n_disputed = sum(1 for r in results if r.status == "disputed")
    n_incomplete = sum(
        1 for r in results if r.status == "incomplete_public"
    )
    n_with_unavailable = sum(
        1 for r in results if any(r.fields_unavailable.values())
    )

    assert results, "cross_validate_all() must produce at least one row"
    assert n_disputed >= 2, (
        f"round 3: expected at least 2 disputed rows in current corpora "
        f"(1979-03-29 and 2024-09-07); got {n_disputed}. "
        f"per-row: "
        + ", ".join(
            f"{r.date}:{r.status}" for r in results
        )
    )
    assert n_incomplete >= 1, (
        f"round 3: expected at least 1 incomplete_public row "
        f"(1981-08-23); got {n_incomplete}"
    )
    assert n_match == 0, (
        f"round 3: no rows can be match while saka_year is "
        f"unavailable; got {n_match}"
    )
    assert n_with_unavailable == len(results), (
        f"round 3: all current corpus rows should have at least one "
        f"unavailable field; got {n_with_unavailable}/{len(results)}"
    )
    # And the disputed dimension must include rows with unavailable
    # fields -- this is the round-3 invariant that the round-2 CLI
    # output implied was impossible.
    n_disputed_with_unavailable = sum(
        1 for r in results
        if r.status == "disputed" and any(r.fields_unavailable.values())
    )
    assert n_disputed_with_unavailable >= 2, (
        f"round 3: at least 2 of the disputed rows must also have "
        f"unavailable fields; got {n_disputed_with_unavailable}"
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
