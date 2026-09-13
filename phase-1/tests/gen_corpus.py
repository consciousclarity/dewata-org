"""generate conformance corpora for the dewata calendar engine.

this script produces self-consistent vectors by running the engine itself
for a date range and capturing the expected output. cross-validation
vectors (comparison to published calendars) are seeded separately.

usage:
  python -m tests.gen_corpus --topic pawukon --start 1979-01-01 --end 2030-12-31
  python -m tests.gen_corpus --topic saka --start 1979-01-01 --end 2030-12-31
  python -m tests.gen_corpus --topic wewaran --start 1979-01-01 --end 2030-12-31
  python -m tests.gen_corpus --topic rahinan --start 1979-01-01 --end 2030-12-31
  python -m tests.gen_corpus --all
"""

import argparse
import datetime as _dt
import json
import sys
from dataclasses import asdict
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from dewatacalendar.api import compose_day  # noqa: E402

CORPUS_OUT = Path(__file__).resolve().parent.parent / "conformance"


def gen_one(date: _dt.date) -> dict:
    """emit a flat test vector for a single date."""
    day = compose_day(date)
    flat = asdict(day)
    return {
        "input": {"date": date.isoformat()},
        "expected": flat,
        "rule_id": flat["ruleset"],
        "history_source": "self-generated-v0.1",
    }


def write_corpus(topic: str, dates: list[_dt.date], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write("[\n")
        for i, d in enumerate(dates):
            fh.write(json.dumps(gen_one(d), ensure_ascii=False))
            if i < len(dates) - 1:
                fh.write(",\n")
            else:
                fh.write("\n")
        fh.write("]\n")


def gen_topic(topic: str, start: _dt.date, end: _dt.date, out_path: Path) -> int:
    dates: list[_dt.date] = []
    d = start
    while d <= end:
        dates.append(d)
        d += _dt.timedelta(days=1)
    write_corpus(topic, dates, out_path)
    return len(dates)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true")
    p.add_argument("--topic", choices=["pawukon", "saka", "wewaran", "rahinan", "integration"])
    p.add_argument("--start", default="1979-01-01")
    p.add_argument("--end", default="2030-12-31")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    topics = ["pawukon", "saka", "wewaran", "rahinan"] if args.all else [args.topic]
    if not topics:
        print("use --all or --topic", file=sys.stderr)
        return 2

    start = _dt.date.fromisoformat(args.start)
    end = _dt.date.fromisoformat(args.end)

    total = 0
    for topic in topics:
        out_path = args.out and Path(args.out) or (CORPUS_OUT / f"{topic}.json")
        count = gen_topic(topic, start, end, out_path)
        print(f"  wrote {count} vectors → {out_path}")
        total += count
    print(f"\ntotal: {total} vectors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
