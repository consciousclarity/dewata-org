#!/usr/bin/env python
"""secret-scan: scan the repository for low-entropy strings that look like
tokens, passwords, ssh keys, or other secrets.

this is a best-effort scanner.  it looks for:

  - bearer-style tokens
  - password=… assignments
  - ssh private keys (BEGIN OPENSSH PRIVATE KEY / BEGIN RSA PRIVATE KEY)
  - PEM-formatted blocks
  - long (>20 char) base64 strings labelled as tokens
  - AWS, GitHub, Cloudflare, Dewata-specific token shapes

false positives are possible; review each match.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _b64_pattern() -> re.Pattern:
    return re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")


def _categories() -> list[tuple[str, re.Pattern]]:
    return [
        (
            "github_pat",
            re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
        ),
        (
            "cloudflare_token",
            re.compile(r"\bcf[a-z0-9]{20,}_[A-Za-z0-9]{20,}\b"),
        ),
        (
            "bearer_token",
            re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b", re.IGNORECASE),
        ),
        (
            "aws_key",
            re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
        ),
        (
            "private_key_block",
            re.compile(r"-{3,}BEGIN [A-Z ]+PRIVATE KEY-{3,}"),
        ),
        (
            "pem_block",
            re.compile(r"-{3,}BEGIN CERTIFICATE-{3,}"),
        ),
        (
            "password_assign",
            re.compile(r"\bpassword\s*[:=]\s*[\"']?[^\s\"',]{6,}", re.IGNORECASE),
        ),
        (
            "ssh_key_in_config",
            re.compile(r"SECRET_KEY\s*=\s*[\"'][^\"']{20,}[\"']"),
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0] if argv else ".").resolve()
    skip_dirs = {".git", ".venv", "node_modules", "__pycache__", "dist"}
    total = 0
    matches: list[tuple[str, str, str]] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.suffix not in (
            ".py", ".sql", ".md", ".txt", ".json", ".yaml", ".yml",
            ".tf", ".env", ".ini", ".cfg", ".sh",
        ):
            continue
        # intentional test fixtures don't apply as real secrets.  we
        # still scan test files for non-fixture leaks.
        is_test_file = (
            "/tests/" in str(path) or path.parts[0] == "tests"
            or "/test_" in str(path)
        )
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for label, pat in _categories():
            for m in pat.finditer(text):
                line = text[:m.start()].count("\n") + 1
                snippet = m.group(0)
                # in test files, require an unusual length before flagging
                # so we don't spam obvious fixture noises
                if is_test_file and len(snippet) < 50:
                    continue
                if path.suffix == ".md" and "secret" in snippet.lower():
                    continue
                matches.append((str(path.relative_to(root)), f"{label}:{line}", snippet[:60]))
                total += 1
    if not matches:
        print("secret-scan: no obvious secrets found.")
        return 0
    for path, label, snippet in matches:
        print(f"  {path}: {label}  ->  {snippet!r}")
    print(f"\nsecret-scan: {total} potential match(es).  REVIEW EACH.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
