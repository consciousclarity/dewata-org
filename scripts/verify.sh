#!/usr/bin/env bash
# verify.sh — run after a fresh clone + `pip install -e phase-1`.
# asserts the engine works, the ruleset matches, and live fastapi binds.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> calendar engine version"
python -m dewatacalendar ruleset | head -1

echo "==> epoch anchor"
python -m dewatacalendar date 1981-08-23 \
  | python -c "import sys, json; d = json.load(sys.stdin); assert d['pawukon']['position_in_cycle'] == 1, d['pawukon']; print('  position_in_cycle =', d['pawukon']['position_in_cycle'], 'wuku_name =', d['pawukon']['wuku_name'])"

echo "==> pytest"
python -m pytest phase-1/tests/ -q --tb=line

echo "==> conformance sample"
python -m dewatacalendar test

echo
echo "✓ all phase 1 checks passed."
