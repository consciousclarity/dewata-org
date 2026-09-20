#!/usr/bin/env python3
"""
re-derive dew_wku_name (column 13) in corrected-seven-date-comparison.csv
by executing the engine against the seven dates.

constraints:
  - no hand-typing. every value comes from pawukon_for_gregorian(date).wuku_name
    at the current working tree (HEAD).
  - the recorded commit (the engine that produced these values) is the commit
    in the artifact's provenance header.
  - other columns stay unchanged.
  - the script is idempotent: running it twice produces the same output.
  - the script is read-only with respect to anything outside this one CSV.

why this exists:
  the CSV's last-modified commit is b55b643 (pre-fix wuku table) but the
  recorded dew_wku_name values match the post-fix table. hand-correcting
  the column would have repeated the defect. instead, this script re-derives
  the column by executing the engine at HEAD and records both the engine
  commit and the file's git history separately.

see phase-1/evidence/MANIFEST.md for the provenance recording format.
"""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # phase-1/tools/full_range_cross_validation/redrive.py → phase-1
CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "evidence"
    / "references"
    / "reingold-dershowitz-2018-pawukon"
    / "firstparty-EdReingold-calendar-code2"
    / "cycle-comparison"
    / "corrected-seven-date-comparison.csv"
)
PAWUKON_SRC_ROOT = REPO_ROOT / "phase-1" / "src"


def read_working_tree_commit() -> str:
    """return git rev-parse HEAD, the engine commit this regeneration runs against."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return completed.stdout.strip()


def engine_output_for(date_iso: str) -> str:
    """return pawukon_for_gregorian(date).wuku_name at the working tree."""
    sys.path.insert(0, str(PAWUKON_SRC_ROOT))
    try:
        from dewatacalendar import pawukon
        pd = pawukon.pawukon_for_gregorian(dt.date.fromisoformat(date_iso))
        return pd.wuku_name
    finally:
        sys.path.pop(0)


def redrive(csv_path: Path, engine_commit: str) -> tuple[int, list[str]]:
    """re-derive col 13 (dew_wku_name) by execution. idempotent.

    returns (rows_changed, log_lines). rows_changed counts rows whose
    dew_wku_name differed from the engine output before this run (zero
    means the file already had engine output at the working tree).
    """
    text = csv_path.read_text()
    lines = text.splitlines()
    if not lines:
        raise RuntimeError(f"empty CSV: {csv_path}")
    header = lines[0]
    field_names = header.split("|")
    if field_names[12] != "dew_wku_name":
        raise RuntimeError(
            f"column 13 is {field_names[12]!r}, expected 'dew_wku_name'. "
            f"the CSV schema changed since this script was written."
        )

    rows_changed = 0
    new_lines: list[str] = [header]
    log_lines: list[str] = []
    for line_no, row_text in enumerate(lines[1:], start=2):
        if not row_text.strip():
            new_lines.append(row_text)
            continue
        fields = row_text.split("|")
        if len(fields) != len(field_names):
            raise RuntimeError(
                f"line {line_no}: {len(fields)} fields, expected {len(field_names)}"
            )
        date_iso = fields[0]
        derived = engine_output_for(date_iso)
        old = fields[12]
        if old != derived:
            rows_changed += 1
            log_lines.append(
                f"line {line_no}: {date_iso}  col 13 '{old}' → '{derived}' "
                f"(re-derived by execution at {engine_commit[:12]})"
            )
        fields[12] = derived
        new_lines.append("|".join(fields))

    csv_path.write_text("\n".join(new_lines) + "\n")
    return rows_changed, log_lines


def main() -> int:
    engine_commit = read_working_tree_commit()
    print(f"engine commit (HEAD): {engine_commit}")
    print(f"CSV: {CSV_PATH.relative_to(REPO_ROOT)}")
    print()
    rows_changed, log_lines = redrive(CSV_PATH, engine_commit)
    print(f"rows changed: {rows_changed}")
    if log_lines:
        print()
        print("log:")
        for line in log_lines:
            print(f"  {line}")
    if rows_changed == 0:
        print()
        print("idempotent: file already had engine output at this working tree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
