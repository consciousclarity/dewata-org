"""conformance harness for the dewata calendar engine.

`pytest -q tests/test_conformance.py` runs all conformance vectors and
the corpus-authority gate tests.

## corpus enumeration

the harness explicitly enumerates corpus basenames in PUBLISHED_CORPORA.
it does NOT glob `*.json` under `conformance/` because that directory
also contains STATUS.json (the corpus-authority registry), which is
metadata, not corpus vectors. STATUS.json must never be loadable as a
corpus — a directory name does not confer authority (see
phase-1/conformance/STATUS.schema.md).

the harness exercises three published corpora:
  - cunningham_1994        (UNVERIFIED — book not held on this host)
  - igarashi_1999          (UNVERIFIED — publisher unverified)
  - kalenderbali_2026-09   (NON_AUTHORITATIVE — practitioner calendar)

each corpus is loaded via dewatacalendar.conformance.load_corpus(),
which annotates each vector with `_corpus_status` per the v1.0
authority model. tests below assert that the annotations match the
declared STATUS.json registry and that the gate predicates behave
correctly.

the pre-v1.0 assumption that any file under conformance/published/ is
authoritative has been explicitly corrected here. STATUS.json is the
single source of truth for authority, and only ATTESTED corpora pass
the independent-reference validation gate.

this file does NOT touch test_dispute_recordable_classifications or
any other test in tests/test_cultural_adapters.py — those belong to
the v1.0 dispute-schema migration (item 7 in the gap analysis
remediation order), not to the corpus-authority quarantine.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

from dewatacalendar.api import compose_day
from dewatacalendar.conformance import load_corpus
from dewatacalendar.corpus_status import (
    CorpusStatus,
    annotate_vectors_with_status,
    can_be_described_as_ground_truth,
    can_be_silently_copied_to_authoritative_fixture,
    can_promote_ruleset_using,
    can_satisfy_validation_gate,
    corpus_record_for,
    corpus_status_for,
)


CORPUS_ROOT = Path(__file__).resolve().parent.parent / "conformance"
PUBLISHED_DIR = CORPUS_ROOT / "published"
STATUS_FILE = CORPUS_ROOT / "STATUS.json"

# explicit enumeration — do not use glob. a directory name does not
# confer authority. STATUS.json is metadata and is excluded by name
# here, NOT by glob-exclusion logic.
PUBLISHED_CORPORA: tuple[str, ...] = (
    "cunningham_1994",
    "igarashi_1999",
    "kalenderbali_2026-09",
)

# mapping from corpus basename to expected authority status per
# phase-1/conformance/STATUS.json. any drift between this map and
# the actual STATUS.json fails the registry-drift test below.
EXPECTED_STATUS: dict[str, str] = {
    "cunningham_1994": CorpusStatus.UNVERIFIED.value,
    "igarashi_1999": CorpusStatus.UNVERIFIED.value,
    "kalenderbali_2026-09": CorpusStatus.NON_AUTHORITATIVE.value,
}


# ──────────────────────────────────────────────────────────────────────
# Section 1 — registry integrity: STATUS.json is the single source of
# truth, and the canonical STATUS location is conformance/STATUS.json
# ──────────────────────────────────────────────────────────────────────


def test_status_file_exists_at_canonical_location():
    """STATUS.json lives at phase-1/conformance/STATUS.json. it does
    NOT live under published/. STATUS.json is metadata; published/
    contains historical corpus material."""
    assert STATUS_FILE.exists(), f"missing canonical registry: {STATUS_FILE}"
    assert not (PUBLISHED_DIR / "STATUS.json").exists(), (
        "STATUS.json must NOT live under published/ — authority comes "
        "from the canonical STATUS location, not from directory placement"
    )


def test_status_file_is_not_loadable_as_a_corpus():
    """STATUS.json must never be interpretable as a corpus. load_corpus
    refuses to load it (either because no file is found at the
    STATUS location, or because the file's structure does not match
    a corpus — both are refusals)."""
    with pytest.raises((FileNotFoundError, ValueError)):
        load_corpus("STATUS")


def test_registry_status_matches_expected_for_each_published_corpus():
    """for every corpus in PUBLISHED_CORPORA, the status declared in
    STATUS.json matches the expected v1.0 quarantine status."""
    for name in PUBLISHED_CORPORA:
        actual = corpus_status_for(name).value
        expected = EXPECTED_STATUS[name]
        assert actual == expected, (
            f"corpus {name!r}: STATUS.json says {actual!r}, expected {expected!r}"
        )


def test_unknown_corpus_fails_closed_to_unverified():
    """corpora not registered in STATUS.json must default to UNVERIFIED
    rather than be treated as authoritative by default. a directory
    name does not confer authority."""
    for name in ("totally_made_up_corpus", "another_unknown", ""):
        assert corpus_status_for(name) == CorpusStatus.UNVERIFIED


def test_only_attested_passes_the_independent_reference_gate():
    """the gate is the single point at which authority is enforced.
    UNVERIFIED and NON_AUTHORITATIVE corpora must NOT pass."""
    assert can_satisfy_validation_gate(CorpusStatus.ATTESTED) is True
    assert can_satisfy_validation_gate(CorpusStatus.UNVERIFIED) is False
    assert can_satisfy_validation_gate(CorpusStatus.NON_AUTHORITATIVE) is False
    # fail-closed on unrecognized status strings
    assert can_satisfy_validation_gate("MAYBE_OK") is False
    assert can_satisfy_validation_gate("") is False
    assert can_satisfy_validation_gate("authoritative") is False


def test_unverified_corpora_cannot_justify_ruleset_promotion():
    """per the gap analysis Finding 5: ruleset_promotion requires
    authoritative ground truth. UNVERIFIED and NON_AUTHORITATIVE
    corpora may inform the work but may not justify the promotion."""
    assert can_promote_ruleset_using(CorpusStatus.ATTESTED) is True
    assert can_promote_ruleset_using(CorpusStatus.UNVERIFIED) is False
    assert can_promote_ruleset_using(CorpusStatus.NON_AUTHORITATIVE) is False


def test_unverified_corpora_cannot_be_described_as_ground_truth():
    """ATTESTED may be described as ground truth; UNVERIFIED and
    NON_AUTHORITATIVE must be described as 'historical' or 'diagnostic'."""
    assert can_be_described_as_ground_truth(CorpusStatus.ATTESTED) is True
    assert can_be_described_as_ground_truth(CorpusStatus.UNVERIFIED) is False
    assert can_be_described_as_ground_truth(CorpusStatus.NON_AUTHORITATIVE) is False


def test_unverified_corpora_values_cannot_be_silently_copied_to_authoritative_fixtures():
    """per the gap analysis: 'their values must not be silently copied
    into new authoritative fixtures.' only ATTESTED corpora satisfy
    this predicate."""
    assert can_be_silently_copied_to_authoritative_fixture(CorpusStatus.ATTESTED) is True
    assert can_be_silently_copied_to_authoritative_fixture(CorpusStatus.UNVERIFIED) is False
    assert can_be_silently_copied_to_authoritative_fixture(CorpusStatus.NON_AUTHORITATIVE) is False


# ──────────────────────────────────────────────────────────────────────
# Section 2 — corpus loads + per-corpus status: prove the corpora are
# loadable for diagnostic comparison AND each is annotated with its
# authority status. loading must not depend on the corpus being
# authoritative.
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module", params=list(PUBLISHED_CORPORA))
def published_corpus_name(request) -> str:
    return request.param


def test_published_corpus_file_exists(published_corpus_name):
    """every corpus in PUBLISHED_CORPORA must have a JSON file under
    conformance/published/. this is a precondition for any loading."""
    path = PUBLISHED_DIR / f"{published_corpus_name}.json"
    assert path.exists(), f"corpus file missing: {path}"


def test_published_corpus_loads_with_status_annotation(published_corpus_name):
    """load_corpus returns the vectors and annotates each with
    _corpus_status. UNVERIFIED / NON_AUTHORITATIVE corpora remain
    loadable; they are diagnostic only and may not satisfy a
    validation gate (see Section 3)."""
    vectors = load_corpus(published_corpus_name)
    assert len(vectors) > 0, f"corpus {published_corpus_name} is empty"
    expected_status = EXPECTED_STATUS[published_corpus_name]
    for v in vectors:
        assert v.get("_corpus_status") == expected_status, (
            f"vector in {published_corpus_name} annotated with "
            f"{v.get('_corpus_status')!r}, expected {expected_status!r}"
        )


def test_published_corpus_annotation_carries_review_record(published_corpus_name):
    """each annotated vector carries a `_corpus_record` with reason,
    related_dispute_id, date_classified, and evidence_review_artifact.
    this is what makes the authority status a first-class field for
    downstream consumers — not a buried string."""
    vectors = load_corpus(published_corpus_name)
    sample = vectors[0]
    rec = sample.get("_corpus_record", {})
    assert rec.get("reason"), f"{published_corpus_name}: missing reason"
    assert rec.get("date_classified"), f"{published_corpus_name}: missing date_classified"
    assert rec.get("evidence_review_artifact"), f"{published_corpus_name}: missing evidence_review_artifact"


# ──────────────────────────────────────────────────────────────────────
# Section 3 — gate behavior per corpus: prove that the published
# corpora in their current status cannot satisfy any authority gate.
# this is the actual enforcement of the quarantine.
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module", params=list(EXPECTED_STATUS.items()))
def expected_status_pair(request) -> tuple[str, str]:
    """(corpus_name, expected_status_str)"""
    return request.param


def test_expected_corpus_status_matches_gate_predicate(expected_status_pair):
    """for each corpus, the status declared in STATUS.json must match
    the status returned by corpus_status_for, AND the gate must
    return False for that status (because no corpus is currently
    ATTESTED)."""
    name, expected = expected_status_pair
    actual_status = corpus_status_for(name)
    assert actual_status.value == expected, (
        f"corpus {name!r}: status is {actual_status.value!r}, expected {expected!r}"
    )
    assert can_satisfy_validation_gate(actual_status) is False, (
        f"corpus {name!r} unexpectedly passes the gate (status={actual_status.value!r}); "
        "this means the quarantine is broken"
    )


def test_each_published_corpus_cannot_satisfy_ruleset_promotion(published_corpus_name):
    """every currently-published corpus is non-ATTESTED, so none can
    justify a ruleset_promotion. this is the core enforcement: even
    if a future ruleset bump happens to match the corpus's vectors,
    the corpus's UNVERIFIED / NON_AUTHORITATIVE status blocks the
    promotion from being justified by that corpus alone."""
    status = corpus_status_for(published_corpus_name)
    assert can_promote_ruleset_using(status) is False


def test_each_published_corpus_cannot_be_described_as_ground_truth(published_corpus_name):
    """no published corpus may be described as ground truth in any
    artifact until positive evidence reclassifies its status."""
    status = corpus_status_for(published_corpus_name)
    assert can_be_described_as_ground_truth(status) is False


# ──────────────────────────────────────────────────────────────────────
# Section 4 — engine-side: the engine still produces internally
# consistent output for the dates in the published corpora, even when
# those corpora are quarantined. quarantine ≠ silence.
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module", params=list(PUBLISHED_CORPORA))
def published_corpus_vector_dates(published_corpus_name) -> list[str]:
    vectors = load_corpus(published_corpus_name)
    return [v.get("gregorian") or v.get("input", {}).get("date") for v in vectors]


def test_engine_produces_internal_consistency_for_each_published_corpus_date(
    published_corpus_name, published_corpus_vector_dates
):
    """even though the published corpora are quarantined, the engine
    must still produce internally consistent output for the dates
    they cover. quarantine means 'not authoritative', not 'engine
    output is broken'."""
    for date_str in published_corpus_vector_dates:
        if not date_str:
            continue
        try:
            date = _dt.date.fromisoformat(date_str)
        except ValueError:
            continue
        result = compose_day(date)
        assert result.gregorian == date.isoformat()
        assert result.ruleset
        assert result.saka
        assert result.pawukon
        assert result.wewaran
        assert isinstance(result.rahinan, list)


# ──────────────────────────────────────────────────────────────────────
# Section 5 — engine invariants that pre-date PROTOCOL v1.0. these
# tests assert the engine's internal consistency regardless of corpus
# authority status.
# ──────────────────────────────────────────────────────────────────────


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
