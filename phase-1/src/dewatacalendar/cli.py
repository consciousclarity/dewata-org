"""cli for `python -m dewatacalendar`.

subcommands:
  date <YYYY-MM-DD>          print full calendar state for one date
  range <from> <to>         bulk dump of calendar state (csv or json)
  test [topic]              run conformance vectors, print summary
  ruleset                   print the active ruleset version + metadata
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from dataclasses import asdict

from .api import compose_day
from .conformance import run_corpus, load_corpus
from .rulesets import RULESET_VERSION, RULESET_METADATA


def cmd_date(args: argparse.Namespace) -> int:
    d = _dt.date.fromisoformat(args.date)
    day = compose_day(d)
    print(json.dumps(asdict(day), indent=2, ensure_ascii=False))
    return 0


def cmd_range(args: argparse.Namespace) -> int:
    start = _dt.date.fromisoformat(args.start)
    end = _dt.date.fromisoformat(args.end)
    if end < start:
        print("end before start", file=sys.stderr)
        return 2
    out = []
    d = start
    while d <= end:
        day = compose_day(d)
        out.append(asdict(day))
        d += _dt.timedelta(days=1)
    if args.format == "json":
        print(json.dumps(out, indent=2, ensure_ascii=False))
    elif args.format == "jsonl":
        for r in out:
            print(json.dumps(r, ensure_ascii=False))
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    topics = [args.topic] if args.topic else ["all"]
    if args.topic == "all" or not args.topic:
        topics = ["pawukon", "saka", "wewaran", "rahinan", "integration"]
    total_pass = 0
    total_fail = 0
    failed_topics = []
    for topic in topics:
        try:
            vectors = load_corpus(topic)
        except FileNotFoundError as e:
            print(f"skip {topic}: {e}", file=sys.stderr)
            continue
        from .conformance import run_corpus as _run
        passed, total, failures = _run(topic)
        total_pass += passed
        total_fail += total - passed
        if failures:
            failed_topics.append((topic, failures))
        print(f"  {topic:14s} {passed:>6d} / {total:<6d} pass")
    print(f"\n=== total: {total_pass} passed, {total_fail} failed ===")
    if failed_topics:
        print("\nfailures:")
        for topic, fails in failed_topics[:20]:
            for f in fails[:5]:
                print(f"  [{topic}] {f}")
        return 1

    # cross-validation against published sources
    print("\n--- cross-validation against published sources ---")
    try:
        from .cross_validation import cross_validate_all, format_outcome
        results = cross_validate_all()
        for r in results:
            print(f"  {r.date}  [{r.status:8s}]  {r.source[:60]}")
        n_match = sum(1 for r in results if r.status == "match")
        n_disputed = sum(1 for r in results if r.status == "disputed")
        print(f"  -- {n_match} match, {n_disputed} disputed (recorded in docs/runbook/disputes.json) --")
    except Exception as e:
        print(f"  cross-validation skipped: {e}")
    return 0


def cmd_ruleset(args: argparse.Namespace) -> int:
    print(f"version: {RULESET_VERSION}")
    print("metadata:")
    print(json.dumps(RULESET_METADATA, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dewatacalendar")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("date", help="show full calendar state for a date")
    s.add_argument("date")
    s.set_defaults(func=cmd_date)

    s = sub.add_parser("range", help="bulk dump of calendar state")
    s.add_argument("start")
    s.add_argument("end")
    s.add_argument("--format", choices=["json", "jsonl"], default="json")
    s.set_defaults(func=cmd_range)

    s = sub.add_parser("test", help="run conformance vectors")
    s.add_argument("topic", nargs="?", default=None)
    s.set_defaults(func=cmd_test)

    s = sub.add_parser("ruleset", help="print active ruleset")
    s.set_defaults(func=cmd_ruleset)

    s = sub.add_parser("disputes", help="refresh + report disputed cross-validation cases")
    s.add_argument("--refresh", action="store_true", help="rerun cross-validation and update disputes.json")
    s.add_argument("--report", action="store_true", help="print the report")
    s.set_defaults(func=cmd_disputes)

    args = p.parse_args(argv)
    return args.func(args)


def cmd_disputes(args: argparse.Namespace) -> int:
    from .disputes import load_disputes, refresh_disputes, report
    if args.refresh or not load_disputes():
        refresh_disputes()
    print(report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
