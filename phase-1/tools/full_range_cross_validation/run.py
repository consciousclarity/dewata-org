#!/usr/bin/env python3
"""Run the pinned 1900-2099 Dewata/Peradnya/Rust comparison.

This program never changes calendar rules. It executes the two checked-out
upstream implementations, records their native output, and writes a distinct
phase-normalized comparison. Source bytes are checked before execution.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from dewatacalendar.pawukon import pawukon_for_gregorian
from dewatacalendar.wewaran import wewaran_for_position

START = dt.date(1900, 1, 1)
END = dt.date(2099, 12, 31)
FIELDS = ("pawukon_position", "wuku", "pancawara", "saptawara", "triwara", "sadwara")
PANCA = {"paing": 0, "pon": 1, "wage": 2, "kliwon": 3, "keliwon": 3, "umanis": 4}
SAPTA = {name: idx for idx, name in enumerate(("redite", "soma", "anggara", "buda", "wraspati", "sukra", "saniscara"))}
TRI = {name: idx for idx, name in enumerate(("pasah", "beteng", "kajeng"))}
SAD = {name: idx for idx, name in enumerate(("tungleh", "aryang", "urukung", "paniron", "was", "maulu"))}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dates() -> list[str]:
    count = (END - START).days + 1
    return [(START + dt.timedelta(days=offset)).isoformat() for offset in range(count)]


def validate_sources(root: Path, record: dict) -> None:
    for relative, expected in record["files"].items():
        path = root / relative
        if not path.is_file():
            raise SystemExit(f"required pinned source missing: {path}")
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"source hash mismatch for {path}: {actual} != {expected}")


def run_json_adapter(command: list[str], input_text: str, env: dict[str, str]) -> list[dict]:
    completed = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if completed.returncode:
        raise SystemExit(f"adapter failed ({completed.returncode}): {completed.stderr}")
    return [json.loads(line) for line in completed.stdout.splitlines() if line]


def run_rust_adapter(binary: Path, input_text: str) -> list[dict]:
    completed = subprocess.run(
        [str(binary)], input=input_text, text=True, capture_output=True, check=False
    )
    if completed.returncode:
        raise SystemExit(f"Rust adapter failed ({completed.returncode}): {completed.stderr}")
    records = []
    for line in completed.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 11:
            raise SystemExit(f"unexpected Rust adapter row: {line!r}")
        records.append(
            {
                "date": parts[0],
                "pawukon_position_zero_based": int(parts[1]),
                "wuku_index_zero_based": int(parts[2]),
                "wuku_name": parts[3],
                "pancawara_native_index": int(parts[4]),
                "pancawara_name": parts[5],
                "saptawara_native_index": int(parts[6]),
                "saptawara_name": parts[7],
                "triwara_name": parts[8],
                "sadwara_name": parts[9],
                "wuku_day_zero_based": int(parts[10]),
            }
        )
    return records


def dewata_record(value: str) -> dict:
    date = dt.date.fromisoformat(value)
    pawukon = pawukon_for_gregorian(date)
    wewaran = wewaran_for_position(pawukon.position_in_cycle)
    return {
        "date": value,
        "pawukon_position_one_based": pawukon.position_in_cycle,
        "pawukon_position_zero_based": pawukon.position_in_cycle - 1,
        "wuku_index_one_based": pawukon.wuku_idx,
        "wuku_index_zero_based": pawukon.wuku_idx - 1,
        "wuku_name": pawukon.wuku_name,
        "pancawara_native_index_one_based": wewaran.pancawara_idx,
        "pancawara_name": wewaran.pancawara_name,
        "saptawara_native_index_one_based": wewaran.saptawara_idx,
        "saptawara_name": wewaran.saptawara_name,
        "triwara_native_index_one_based": wewaran.triwara_idx,
        "triwara_name": wewaran.triwara_name,
        "sadwara_native_index_one_based": wewaran.sadwara_idx,
        "sadwara_name": wewaran.sadwara_name,
    }


def common(record: dict) -> dict[str, int]:
    return {
        "pawukon_position": record["pawukon_position_zero_based"],
        "wuku": record["wuku_index_zero_based"],
        "pancawara": PANCA[record["pancawara_name"].lower()],
        "saptawara": SAPTA[record["saptawara_name"].lower()],
        "triwara": TRI[record["triwara_name"].lower()],
        "sadwara": SAD[record["sadwara_name"].lower()],
    }


def phase_normalize_dewata(values: dict[str, int]) -> dict[str, int]:
    shifted = (values["pawukon_position"] + 84) % 210
    return {
        "pawukon_position": shifted,
        "wuku": shifted // 7,
        "pancawara": (values["pancawara"] + 84) % 5,
        "saptawara": (values["saptawara"] + 84) % 7,
        "triwara": (values["triwara"] + 84) % 3,
        "sadwara": (values["sadwara"] + 84) % 6,
    }


def write_jsonl_gzip(path: Path, records: list[dict]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as text:
                for record in records:
                    text.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peradnya-root", type=Path, required=True)
    parser.add_argument("--rust-root", type=Path, required=True)
    parser.add_argument("--rust-binary", type=Path, required=True)
    parser.add_argument("--node", default="node")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    tool_dir = Path(__file__).resolve().parent
    provenance = json.loads((tool_dir / "provenance.json").read_text(encoding="utf-8"))
    validate_sources(args.peradnya_root, provenance["peradnya"])
    validate_sources(args.rust_root, provenance["rust"])
    built_entry = args.peradnya_root / "node/BalineseDate.js"
    if not built_entry.is_file():
        raise SystemExit("Peradnya build missing; run `npm ci --ignore-scripts && npm run build:nodejs`")
    if not args.rust_binary.is_file():
        raise SystemExit(f"Rust adapter binary missing: {args.rust_binary}")

    date_values = dates()
    input_text = "\n".join(date_values) + "\n"
    env = dict(os.environ)
    env["TZ"] = "UTC"
    peradnya = run_json_adapter(
        [args.node, str(tool_dir / "peradnya_adapter.js"), str(args.peradnya_root)],
        input_text,
        env,
    )
    rust = run_rust_adapter(args.rust_binary, input_text)
    expected_count = len(date_values)
    if len(peradnya) != expected_count or len(rust) != expected_count:
        raise SystemExit(
            f"row count mismatch: dates={expected_count}, peradnya={len(peradnya)}, rust={len(rust)}"
        )

    raw_records: list[dict] = []
    normalized_records: list[dict] = []
    counts = {
        pair: {axis: {field: Counter() for field in FIELDS} for axis in ("raw", "phase_normalized")}
        for pair in ("dewata_vs_peradnya", "dewata_vs_rust", "peradnya_vs_rust")
    }
    pawukon_offsets: set[int] = set()
    wuku_offsets: set[int] = set()
    pancawara_offsets: set[int] = set()

    for index, value in enumerate(date_values):
        dew = dewata_record(value)
        per = peradnya[index]
        rus = rust[index]
        if per["date"] != value or rus["date"] != value:
            raise SystemExit(f"adapter ordering mismatch at {value}")
        raw_records.append({"date": value, "dewata": dew, "peradnya": per, "rust": rus})
        d_common, p_common, r_common = common(dew), common(per), common(rus)
        d_normalized = phase_normalize_dewata(d_common)
        pawukon_offsets.add((p_common["pawukon_position"] - d_common["pawukon_position"]) % 210)
        wuku_offsets.add((p_common["wuku"] - d_common["wuku"]) % 30)
        pancawara_offsets.add((d_common["pancawara"] - p_common["pancawara"]) % 5)

        pairs = {
            "dewata_vs_peradnya": (d_common, p_common, d_normalized, p_common),
            "dewata_vs_rust": (d_common, r_common, d_normalized, r_common),
            "peradnya_vs_rust": (p_common, r_common, p_common, r_common),
        }
        row = {"date": value, "dewata_shift_days": 84, "comparisons": {}}
        for pair, (left, right, normalized_left, normalized_right) in pairs.items():
            raw_matches = {}
            normalized_matches = {}
            for field in FIELDS:
                raw_match = left[field] == right[field]
                normalized_match = normalized_left[field] == normalized_right[field]
                counts[pair]["raw"][field]["matches" if raw_match else "disagreements"] += 1
                counts[pair]["phase_normalized"][field]["matches" if normalized_match else "disagreements"] += 1
                raw_matches[field] = raw_match
                normalized_matches[field] = normalized_match
            row["comparisons"][pair] = {
                "raw_match": raw_matches,
                "phase_normalized_match": normalized_matches,
            }
        normalized_records.append(row)

    if pawukon_offsets != {84} or wuku_offsets != {12} or pancawara_offsets != {1}:
        raise SystemExit(
            "expected offsets were not constant: "
            f"pawukon={sorted(pawukon_offsets)}, wuku={sorted(wuku_offsets)}, "
            f"pancawara={sorted(pancawara_offsets)}"
        )

    serial_counts = {
        pair: {
            axis: {
                field: {
                    "matches": counter["matches"],
                    "disagreements": counter["disagreements"],
                }
                for field, counter in field_counts.items()
            }
            for axis, field_counts in axes.items()
        }
        for pair, axes in counts.items()
    }
    summary = {
        "schema_version": "1.0",
        "generated_at": "2026-09-16",
        "range": {"start": START.isoformat(), "end": END.isoformat(), "inclusive_days": expected_count},
        "implementations": {
            "dewata": {"repository_commit": "25ad44dc8c7f492efb942a8810fdb6efabdfdd18"},
            "peradnya": {"commit": provenance["peradnya"]["commit"], "release": provenance["peradnya"]["release"]},
            "rust": {"commit": provenance["rust"]["commit"], "release": provenance["rust"]["release"]},
        },
        "constant_offsets": {
            "pawukon_reference_minus_dewata_days_mod_210": 84,
            "wuku_reference_minus_dewata_mod_30": 12,
            "pancawara_dewata_minus_reference_days_mod_5": 1,
        },
        "counts": serial_counts,
        "interpretation_limit": "Implementation agreement establishes reproducibility only; it does not establish cultural or customary authority and does not resolve any dispute.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "raw-outputs.jsonl.gz"
    normalized_path = args.output_dir / "phase-normalized-comparisons.jsonl.gz"
    summary_path = args.output_dir / "summary.json"
    write_jsonl_gzip(raw_path, raw_records)
    write_jsonl_gzip(normalized_path, normalized_records)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_targets = [raw_path, normalized_path, summary_path, tool_dir / "provenance.json"]
    checksum_lines = [f"{sha256(path)}  {path.name}" for path in checksum_targets]
    (args.output_dir / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
