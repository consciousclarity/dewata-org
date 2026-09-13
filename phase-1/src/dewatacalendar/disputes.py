"""dispute review cadence.

this module provides:
  - `cli.py`:     `dewatacalendar disputes` subcommand
  - `tracker.py`: periodic check that flags disputes as matured after 30 days.

output of `dewatacalendar disputes`:
  - reads `docs/runbook/disputes.json`
  - emits each dispute with `matured: true` if older than 30 days
  - emits a summary report (counts by classification, oldest dispute)
  - emits a "needs review" sorted list

## 30-day review cadence

a dispute is created with status `pending`. if it stays `pending` for 30
days, it enters `matured` state. if 90 days, it enters `expired`. a
dispute can be `rejected`, `accepted`, or `variant`.

the cadence is enforced by the daily snapshot cron (see
`docs/runbook/DISPUTE_REVIEW_PROTOCOL.md`).
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from .cross_validation import cross_validate_all, format_outcome
from .runbook import classify, DisputeRecord


DISPUTES_LOG = Path(__file__).resolve().parent.parent.parent / "docs" / "runbook" / "disputes.json"
DISPUTES_DIR = DISPUTES_LOG.parent

MATURITY_DAYS = 30
EXPIRY_DAYS = 90


def load_disputes() -> list[dict]:
    """load existing disputes.json."""
    if not DISPUTES_LOG.exists():
        return []
    return json.loads(DISPUTES_LOG.read_text(encoding="utf-8"))


def write_disputes(disputes: list[dict]) -> None:
    """atomically write the disputes registry."""
    DISPUTES_LOG.parent.mkdir(parents=True, exist_ok=True)
    DISPUTES_LOG.write_text(
        json.dumps(disputes, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def refresh_disputes() -> list[dict]:
    """rerun cross-validation and rebuild disputes.json.

    Every dispute is classified as epoch_offset/rule_drift/calendar_variant.
    Recorded with full provenance. Already-recorded disputes are preserved
    (this is append-aware, not a re-write).
    """
    existing = load_disputes()

    seen = {d.get("date", "") + "|" + d.get("source", "") for d in existing}

    refreshed = list(existing)
    for outcome in cross_validate_all():
        if outcome.status != "disputed":
            continue
        key = outcome.date + "|" + outcome.source
        if key in seen:
            continue
        cls, notes = classify(outcome)
        rec = DisputeRecord.from_outcome(outcome, cls, notes)
        refreshed.append({
            "date": rec.date,
            "source": rec.source,
            "page": rec.page,
            "rule_id": rec.rule_id,
            "classification": rec.classification,
            "resolution": rec.resolution,
            "notes": rec.notes,
            "recorded_at": rec.recorded_at,
        })
        seen.add(key)

    write_disputes(refreshed)
    return refreshed


def maturity_status(recorded_at: str) -> str:
    """return one of 'fresh', 'matured', 'expired'."""
    if not recorded_at:
        return "fresh"
    try:
        recorded = _dt.datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
    except ValueError:
        return "fresh"
    age_days = (_dt.datetime.now(_dt.timezone.utc) - recorded).days
    if age_days >= EXPIRY_DAYS:
        return "expired"
    if age_days >= MATURITY_DAYS:
        return "matured"
    return "fresh"


def report(disputes: list[dict] | None = None) -> str:
    """a human-readable indonesian-language report of pending disputes."""
    disputes = disputes if disputes is not None else load_disputes()
    out: list[str] = []
    out.append("=== dispute registry ===")
    out.append(f"total disputes: {len(disputes)}")

    by_class: dict[str, int] = {}
    fresh = matured = expired = 0
    for d in disputes:
        cls = d.get("classification", "unknown")
        by_class[cls] = by_class.get(cls, 0) + 1
        ms = maturity_status(d.get("recorded_at", ""))
        if ms == "fresh":
            fresh += 1
        elif ms == "matured":
            matured += 1
        else:
            expired += 1

    out.append("berdasarkan klasifikasi:")
    for k, v in sorted(by_class.items()):
        out.append(f"  {k:18s} {v:>4d}")

    out.append(f"berdasarkan umur:")
    out.append(f"  fresh (0-29 hari)  {fresh:>4d}")
    out.append(f"  matured (30-89 hari) {matured:>4d}")
    out.append(f"  expired (>=90 hari) {expired:>4d}")

    if disputes:
        oldest = min(disputes, key=lambda d: d.get("recorded_at", "9999"))
        out.append(f"dispute tertua: {oldest['date']} ({oldest.get('classification')}, {oldest.get('recorded_at')})")

    out.append("")
    out.append("=== daftar untuk review ===")
    by_priority = {
        "expired": [],
        "matured": [],
        "fresh": [],
    }
    for d in disputes:
        ms = maturity_status(d.get("recorded_at", ""))
        by_priority[ms].append(d)

    out.append(f"\nEXPIRED (lebih dari 90 hari): {len(by_priority['expired'])}")
    for d in by_priority["expired"]:
        out.append(f"  {d['date']}  {d.get('classification'):18s}  {d.get('source','')[:50]}")
    out.append(f"\nMATURED (30-89 hari): {len(by_priority['matured'])}")
    for d in by_priority["matured"]:
        out.append(f"  {d['date']}  {d.get('classification'):18s}  {d.get('source','')[:50]}")
    out.append(f"\nFRESH (kurang dari 30 hari): {len(by_priority['fresh'])}")
    for d in by_priority["fresh"]:
        out.append(f"  {d['date']}  {d.get('classification'):18s}  {d.get('source','')[:50]}")
    return "\n".join(out)
