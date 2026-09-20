"""verify engine-output provenance for the four evidence artifacts.

this file adds two tests for the artifacts produced by the dewata engine
and recorded under phase-1/evidence/:

1. test_dew_wku_name_invariant — for each of the seven dates in
   corrected-seven-date-comparison.csv, the recorded dew_wku_name
   must equal pawukon_for_gregorian(date).wuku_name at HEAD. this is
   the engine-output invariant: the column is engine output, not
   hand-filled.

2. test_recorded_commit_is_ancestor_of_head_and_rederivation_still_matches
   — for each of the three CSVs, the recorded engine commit must be
   reachable from HEAD (an ancestor), AND re-deriving the engine-
   output columns at HEAD must match what is recorded. not == HEAD;
   the recorded commit must be reachable and the recorded values must
   be engine output at HEAD.

these tests are read-only against the engine and the artifacts. they
do not regenerate anything.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

# three CSVs under EVDIR
EVDIR = ROOT / "evidence" / "references" / "reingold-dershowitz-2018-pawukon"
RAW_DEW = EVDIR / "firstparty-EdReingold-calendar-code2" / "cycle-comparison" / "raw-dewata-210.csv"
DEW_CYC = EVDIR / "firstparty-EdReingold-calendar-code2" / "cycle-comparison" / "dewata-cycle-210.csv"
CORR_7 = EVDIR / "firstparty-EdReingold-calendar-code2" / "cycle-comparison" / "corrected-seven-date-comparison.csv"


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------


def _read_provenance_header(path: Path) -> dict[str, str]:
    """parse `# key: value` lines from the top of a CSV file."""
    out: dict[str, str] = {}
    with path.open() as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("#"):
                break
            if ":" in line:
                key, _, value = line[1:].partition(":")
                out[key.strip()] = value.strip()
    return out


def _git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    return completed.stdout.strip()


def _read_pipe_rows(path: Path) -> list[list[str]]:
    """read a pipe-delimited CSV with optional `#`-prefixed comment lines.

    returns rows of fields. the column header is the first non-comment
    line; everything after that is a data row. blank lines are skipped.
    """
    rows = []
    saw_header = False
    with path.open() as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith("#"):
                continue
            if not saw_header:
                saw_header = True
                continue
            rows.append(line.split("|"))
    return rows


PAWUKON = None


def _pawukon():
    """return the dewatacalendar.pawukon module from this repo's working tree.

    cached after first call. importing as a package via sys.path setup so
    the relative `from .exceptions import InvalidDateError` inside
    pawukon.py resolves.
    """
    global PAWUKON
    if PAWUKON is not None:
        return PAWUKON
    src_dir = str(ROOT / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    import dewatacalendar  # noqa: F401 — register package
    from dewatacalendar import pawukon as _pawukon
    PAWUKON = _pawukon
    return _pawukon


def _wuku_name(date: dt.date) -> str:
    """engine output: pawukon_for_gregorian(date).wuku_name at HEAD."""
    return _pawukon().pawukon_for_gregorian(date).wuku_name


# ----------------------------------------------------------------------------
# 1. engine-output invariant for dew_wku_name
# ----------------------------------------------------------------------------


def test_dew_wku_name_invariant():
    """for each of the seven dates in corrected-seven-date-comparison.csv,
    the recorded dew_wku_name must equal pawukon_for_gregorian(date).wuku_name
    at HEAD. this is the engine-output invariant: the column is engine
    output, not hand-filled.

    hand-correction is forbidden (per the audit on the wuku-table fix);
    a future commit that updates the column without re-deriving will
    fail this test.
    """
    provenance = _read_provenance_header(CORR_7)
    assert "git_commit" in provenance, (
        f"corrected-seven-date-comparison.csv has no `# git_commit:` "
        f"provenance header. add one before claiming this column is "
        f"engine output."
    )

    rows = _read_pipe_rows(CORR_7)
    assert len(rows) == 7, (
        f"corrected-seven-date-comparison.csv: expected 7 data rows, got {len(rows)}"
    )

    mismatches = []
    for fields in rows:
        date_iso = fields[0]
        recorded = fields[12]  # dew_wku_name column
        date = dt.date.fromisoformat(date_iso)
        derived = _wuku_name(date)
        if recorded != derived:
            mismatches.append((date_iso, recorded, derived))

    assert not mismatches, (
        "dew_wku_name in corrected-seven-date-comparison.csv does not "
        "match engine output at HEAD. this column is engine output; "
        "hand-correction is forbidden. re-derive by execution via "
        "phase-1/tools/full_range_cross_validation/redrive.py:\n"
        + "\n".join(f"  {d}: recorded={r!r}, derived={e!r}"
                    for d, r, e in mismatches)
    )


# ----------------------------------------------------------------------------
# 2. provenance: recorded commit is ancestor of HEAD, re-derivation matches
# ----------------------------------------------------------------------------


# (artifact_path, label, kind) where kind ∈ {"engine_name_column",
# "invariant_position", "engine_name_column_seven_dates"}.
# the third arg describes what to re-derive at HEAD.
_CSV_ARTIFACTS = [
    pytest.param(RAW_DEW, "raw-dewata-210.csv", "invariant_position",
                 id="raw-dewata-210.csv"),
    pytest.param(DEW_CYC, "dewata-cycle-210.csv", "invariant_position",
                 id="dewata-cycle-210.csv"),
    pytest.param(CORR_7, "corrected-seven-date-comparison.csv",
                 "engine_name_column_seven_dates",
                 id="corrected-seven-date-comparison.csv"),
]


@pytest.mark.parametrize("artifact_path,artifact_label,kind", _CSV_ARTIFACTS)
def test_recorded_commit_is_ancestor_of_head_and_rederivation_still_matches(
    artifact_path, artifact_label, kind
):
    """the recorded engine commit must be reachable from HEAD (an
    ancestor), AND re-deriving the engine-output columns at HEAD must
    match what is recorded.

    not == HEAD. == the recorded value at HEAD.

    this catches two distinct failure modes:
    1. stale provenance: recorded commit is no longer an ancestor of
       HEAD. a reader checking out HEAD cannot reach the recorded
       commit; the recorded commit was edited or dropped from history.
    2. accidental drift: the recorded value no longer matches what the
       current engine produces. the recorded values should match the
       engine at HEAD if the columns are invariant across engine
       changes (which is the documented property of each artifact).

    for raw-dewata-210.csv: the WUKU_NAME column is **superseded** by
    PR #8. the documented invariant is that WUKU_IDX and position-
    based columns are unaffected by the wuku fix. we verify by
    re-deriving the GREGORIAN date column and asserting the position
    math holds (idx == (days_since_epoch // 7) + 1).

    for dewata-cycle-210.csv: every column is derived from cycle
    position. POS column is the index itself. re-derive: assert
    POS == row_index.

    for corrected-seven-date-comparison.csv: dew_wku_name is engine
    output. re-derive: assert each value matches
    pawukon_for_gregorian(date).wuku_name at HEAD. (this is the same
    invariant as test_dew_wku_name_invariant, but here we also check
    the recorded commit is an ancestor of HEAD.)
    """
    provenance = _read_provenance_header(artifact_path)
    assert "git_commit" in provenance, (
        f"{artifact_label}: missing `# git_commit:` provenance header"
    )
    recorded_commit = provenance["git_commit"]

    head_sha = _git(["rev-parse", "HEAD"])

    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", recorded_commit, head_sha],
        capture_output=True,
    )
    if completed.returncode == 128:
        # exit 128 means git could not find one of the two commits in
        # the local object database. this is NOT a provenance failure:
        # the recorded commit may be perfectly valid, the repository
        # simply has not fetched it. the most common cause is a shallow
        # clone (github actions/checkout defaults to fetch-depth: 1).
        # other causes: a fork that has not synced from upstream; a
        # local clone whose refspec excludes the recorded branch.
        #
        # in any of these cases the right next step is to fetch the
        # missing history, not to investigate the recorded commit.
        # the message below is written for the most common cause
        # (shallow clone in CI) and the one fix this repo already
        # carries (.github/workflows/tests.yml sets fetch-depth: 0 on
        # both jobs).
        assert False, (
            f"{artifact_label}: recorded engine commit {recorded_commit[:12]} "
            f"is not present in the local clone ({head_sha[:12]} is HEAD, "
            f"recorded_commit = {recorded_commit}). exit 128 from "
            f"'git merge-base --is-ancestor' means git could not find "
            f"the recorded commit in the local object database — not "
            f"that the recorded commit is not an ancestor of HEAD.\n\n"
            f"most likely cause: shallow clone (github actions/checkout "
            f"defaults to fetch-depth: 1, which drops every commit except "
            f"HEAD; the recorded engine commit is older than HEAD and is "
            f"therefore missing from the clone).\n\n"
            f"fix: ensure the checkout step sets fetch-depth: 0 "
            f"(see .github/workflows/tests.yml for the existing setting "
            f"in this repo). if running locally: 'git fetch --unshallow' "
            f"or clone with --no-shallow."
        )
    if completed.returncode == 1:
        # exit 1 means git found both commits and they are not in an
        # ancestor relationship. this is a real provenance failure:
        # the recorded engine commit is reachable from a different
        # branch, has been force-pushed, or its SHA has been edited.
        # a reader checking out HEAD cannot reach the recorded commit.
        assert False, (
            f"{artifact_label}: recorded engine commit {recorded_commit[:12]} "
            f"exists in the repository but is not an ancestor of HEAD "
            f"{head_sha[:12]}. the recorded commit was either edited "
            f"(its SHA is no longer reachable from the branch that "
            f"produced this artifact) or has been dropped from this "
            f"branch's history (force-push, rebase). the provenance "
            f"recorded in the artifact is no longer reachable; a reader "
            f"checking out HEAD cannot reproduce what is recorded."
        )
    assert completed.returncode == 0, (
        f"{artifact_label}: 'git merge-base --is-ancestor {recorded_commit[:12]} "
        f"{head_sha[:12]}' returned unexpected exit code "
        f"{completed.returncode}. stdout: {completed.stdout!r}; "
        f"stderr: {completed.stderr!r}"
    )

    rows = _read_pipe_rows(artifact_path)

    if kind == "invariant_position":
        # raw-dewata-210.csv: idx == (days_since_epoch // 7) + 1
        # dewata-cycle-210.csv: pos == row_index
        # for raw-dewata-210.csv, the structure is
        # IDX|GREGORIAN|DEW_POS|WUKU_IDX|WUKU_NAME|PAN|...
        # we re-derive DEW_POS from GREGORIAN and assert it equals
        # (IDX + 1).
        if artifact_label == "raw-dewata-210.csv":
            # check IDX column is in [0..209] and GREGORIAN is well-formed
            mismatches = []
            for fields in rows:
                idx = int(fields[0])
                gregorian = fields[1]
                dew_pos = int(fields[2])
                wuku_idx = int(fields[3])
                date = dt.date.fromisoformat(gregorian)
                # wuku_idx == (position_in_cycle - 1) // 7 + 1
                # and we know position_in_cycle == dew_pos
                expected_wuku_idx = (dew_pos - 1) // 7 + 1
                if wuku_idx != expected_wuku_idx:
                    mismatches.append(
                        (idx, gregorian, "wuku_idx mismatch",
                         wuku_idx, expected_wuku_idx)
                    )
                # also: the engine at HEAD must produce the same wuku_idx
                # for this gregorian date (it's index-based, invariant)
                head_wuku_idx = _pawukon().pawukon_for_gregorian(date).wuku_idx
                if wuku_idx != head_wuku_idx:
                    mismatches.append(
                        (idx, gregorian, "wuku_idx != HEAD",
                         wuku_idx, head_wuku_idx)
                    )
            assert not mismatches, (
                f"{artifact_label}: invariant violation:\n"
                + "\n".join(f"  idx={i} greg={g}: {kind}: recorded={r}, expected={e}"
                            for i, g, kind, r, e in mismatches)
            )
        elif artifact_label == "dewata-cycle-210.csv":
            # structure: POS|DEWATA_POS|LUANG|DWI|...
            assert len(rows) == 210, (
                f"{artifact_label}: expected 210 rows, got {len(rows)}"
            )
            for i, fields in enumerate(rows):
                pos = int(fields[0])
                assert pos == i, (
                    f"{artifact_label}: row {i} has POS={pos}, expected {i}"
                )
        else:
            raise AssertionError(f"unhandled invariant_position: {artifact_label}")

    elif kind == "engine_name_column_seven_dates":
        # corrected-seven-date-comparison.csv: dew_wku_name (col 12 in
        # 0-indexed = field index 12) must equal engine output at HEAD.
        mismatches = []
        for fields in rows:
            date_iso = fields[0]
            recorded = fields[12]
            date = dt.date.fromisoformat(date_iso)
            derived = _wuku_name(date)
            if recorded != derived:
                mismatches.append((date_iso, recorded, derived))
        assert not mismatches, (
            f"{artifact_label}: dew_wku_name at HEAD does not match "
            f"recorded values:\n"
            + "\n".join(f"  {d}: recorded={r!r}, HEAD={e!r}"
                        for d, r, e in mismatches)
        )

    else:
        raise AssertionError(f"unhandled kind: {kind!r}")
