"""verify the reingold-dershowitz-2018-pawukon evidence package.

this script recomputes sha256 over every artifact under
phase-1/evidence/references/reingold-dershowitz-2018-pawukon/ and
compares against the recorded hashes in MANIFEST.md. a mismatch
indicates the package has been altered.

this is a documentary integrity check — it does NOT verify any
calendrical claim. the chapter body is not archived here.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


EVDIR = Path(__file__).resolve().parent.parent / "evidence" / "references" / "reingold-dershowitz-2018-pawukon"
MANIFEST = EVDIR / "MANIFEST.md"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def parse_recorded_hashes(manifest_text: str) -> dict[str, str]:
    """parse '`name` | `sha256`' rows from the MANIFEST table."""
    out: dict[str, str] = {}
    # match markdown table rows that have sha256 in the row
    for line in manifest_text.splitlines():
        m = re.search(r"`([^`]+)`.*?`([0-9a-f]{64})`", line)
        if m and len(m.group(1)) < 80:
            out[m.group(1)] = m.group(2)
    return out


def main() -> int:
    if not MANIFEST.exists():
        print(f"manifest not found: {MANIFEST}")
        return 2
    recorded = parse_recorded_hashes(MANIFEST.read_text(encoding="utf-8"))
    if not recorded:
        print("no hashes parsed from manifest")
        return 3

    errors = 0
    checked = 0
    for name, expected_hash in recorded.items():
        path = EVDIR / name
        if not path.exists():
            print(f"MISSING: {name} (expected sha256={expected_hash})")
            errors += 1
            continue
        actual = sha256(path)
        ok = actual == expected_hash
        status = "OK" if ok else "MISMATCH"
        print(f"{status:>8}  {name}  sha256={actual}")
        if not ok:
            print(f"        expected: {expected_hash}")
            errors += 1
        checked += 1

    print()
    print(f"checked {checked}, errors {errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
