"""verify the CALENDRICA 4.0 first-party implementation runs and reproduces
sample values from dates4.csv.

this test is OPTIONAL — it requires sbcl to be installed. if sbcl is not
available, the test is SKIPPED. this is appropriate because:

  - the CALENDRICA source file is NOT redistributed (license clause 1)
  - this test only verifies that the runtime reproduces the sample data
    WHEN the source is locally available at /tmp/refs/calendrica-4.0.cl
  - the test is part of the evidence-package integrity chain

the test loads the source, runs a few wewaran functions, and compares to
the dates4.csv sample values for the first 10 RDs.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
from pathlib import Path

import pytest


SBCL_PATH = shutil.which("sbcl")
CAL_SOURCE = Path("/tmp/refs/calendrica-4.0.cl")
CAL_LICENSE = Path("/tmp/refs/COPYRIGHT_DERSHOWITZ_RHEINGOLD.txt")
CAL_SAMPLE = Path("/tmp/refs/dates4.csv")

# expected SHA-256 of the source file
EXPECTED_SOURCE_SHA = "5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb"

# first 10 sample rows from dates4.csv (RD, Luang, Dwiwara, Triwara, Caturwara,
# Pancawara, Sadwara, Saptawara, Asatawara, Sangawara, Dasawara)
EXPECTED_SAMPLES = [
    (-214193, "f", 1, 1, 1, 3, 1, 1, 5, 7, 3),
    (-61387, "t", 2, 2, 1, 4, 5, 4, 5, 5, 2),
    (25469, "t", 2, 2, 1, 5, 5, 4, 1, 5, 6),
    (49217, "f", 1, 2, 3, 3, 5, 1, 3, 5, 3),
    (171307, "f", 1, 1, 3, 3, 1, 4, 3, 1, 5),
    (210155, "t", 2, 2, 1, 1, 5, 2, 1, 8, 0),
    (253427, "f", 1, 2, 3, 3, 5, 7, 3, 2, 7),
    (369740, "f", 1, 2, 2, 1, 2, 1, 2, 2, 1),
    (400085, "f", 1, 2, 1, 1, 5, 1, 1, 8, 1),
    (434355, "t", 2, 3, 1, 1, 3, 6, 1, 3, 2),
]


def _sha256_of(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_calendrica_script(script: str) -> str:
    """Load CALENDRICA + run script via sbcl, return stdout."""
    if not SBCL_PATH:
        pytest.skip("sbcl not installed; CALENDRICA runtime test skipped")
    if not CAL_SOURCE.exists():
        pytest.skip(f"CALENDRICA source not present at {CAL_SOURCE}")
    # write script to a temp file
    script_path = Path("/tmp/calendrica-test-script.lisp")
    script_path.write_text(script)
    r = subprocess.run(
        [SBCL_PATH, "--noinform", "--noprint", "--non-interactive",
         "--load", str(script_path)],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        pytest.fail(f"sbcl exited non-zero:\n{r.stderr[-2000:]}")
    return r.stdout


@pytest.mark.skipif(SBCL_PATH is None, reason="sbcl not installed")
@pytest.mark.skipif(not CAL_SOURCE.exists(), reason="CALENDRICA source not present")
def test_calendrica_source_sha256_matches_record():
    """the locally-cached source file must match the recorded sha-256."""
    actual = _sha256_of(CAL_SOURCE)
    assert actual == EXPECTED_SOURCE_SHA, (
        f"CALENDRICA source SHA-256 mismatch: actual={actual} expected={EXPECTED_SOURCE_SHA}"
    )


@pytest.mark.skipif(SBCL_PATH is None, reason="sbcl not installed")
@pytest.mark.skipif(not CAL_SOURCE.exists(), reason="CALENDRICA source not present")
@pytest.mark.skipif(not CAL_SAMPLE.exists(), reason="CALENDRICA dates4.csv not present")
def test_calendrica_runtime_matches_sample_data():
    """CALENDRICA runtime must reproduce the sample-data Pawukon fields
    for the first 10 RDs in dates4.csv."""
    # build a script that loads CALENDRICA + returns the Pawukon fields
    rd_list = [str(rd) for rd, *_ in EXPECTED_SAMPLES]
    script = """
(defpackage :cc4 (:use :cl))
(load "/tmp/refs/calendrica-4.0.cl")
(in-package :cc4)
(let ((rds '(""" + " ".join(rd_list) + """)))
  (dolist (rd rds)
    (let ((p (bali-pawukon-from-fixed rd)))
      (format t "~a|~a|~a|~a|~a|~a|~a|~a|~a|~a|~a~%"
              rd
              (if (first p) "t" "f")
              (second p) (third p) (fourth p) (fifth p) (sixth p)
              (seventh p) (eighth p) (ninth p) (tenth p)))))
(sb-ext:exit)
"""
    output = _run_calendrica_script(script)
    lines = [l for l in output.splitlines() if "|" in l]
    assert len(lines) >= 10, f"expected at least 10 lines, got {len(lines)}\n{output}"
    for i, expected in enumerate(EXPECTED_SAMPLES):
        rd_exp, luang_exp, dwi, tri, cat, pan, sad, sap, ast, sng, das = expected
        line = lines[i]
        parts = line.split("|")
        rd_act, luang_act = parts[0], parts[1]
        dwi_a, tri_a, cat_a, pan_a = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
        sad_a, sap_a, ast_a, sng_a, das_a = int(parts[6]), int(parts[7]), int(parts[8]), int(parts[9]), int(parts[10])
        assert int(rd_act) == rd_exp, f"RD mismatch: line {i} says {rd_act} expected {rd_exp}"
        assert luang_act == luang_exp, (
            f"Luang mismatch at RD {rd_exp}: CAL={luang_act} expected={luang_exp}"
        )
        # field-by-field
        actuals = (dwi_a, tri_a, cat_a, pan_a, sad_a, sap_a, ast_a, sng_a, das_a)
        expected_vals = (dwi, tri, cat, pan, sad, sap, ast, sng, das)
        assert actuals == expected_vals, (
            f"Field mismatch at RD {rd_exp}: actual={actuals} expected={expected_vals}"
        )


@pytest.mark.skipif(SBCL_PATH is None, reason="sbcl not installed")
@pytest.mark.skipif(not CAL_SOURCE.exists(), reason="CALENDRICA source not present")
def test_calendrica_bali_epoch_constant():
    """bali-epoch must equal -1721279 (Rata Die) per the source code."""
    script = """
(defpackage :cc4 (:use :cl))
(load "/tmp/refs/calendrica-4.0.cl")
(in-package :cc4)
(format t "bali-epoch=~a~%" bali-epoch)
(format t "bali-day-from-fixed(723415)=~a~%" (bali-day-from-fixed 723415))
(sb-ext:exit)
"""
    output = _run_calendrica_script(script)
    assert "bali-epoch=-1721279" in output, f"unexpected bali-epoch output:\n{output}"
    assert "bali-day-from-fixed(723415)=84" in output, (
        f"unexpected bali-day-from-fixed output:\n{output}"
    )


@pytest.mark.skipif(not CAL_LICENSE.exists(), reason="CALENDRICA LICENSE not present")
def test_calendrica_license_recorded_sha():
    """the license file SHA-256 in the recorded metadata must match the actual file."""
    actual = _sha256_of(CAL_LICENSE)
    expected = "d34115459b34df91fdd60134384e2f427d29e483a6991b11c2cea42df237412c"
    assert actual == expected, f"license SHA mismatch: actual={actual} expected={expected}"
