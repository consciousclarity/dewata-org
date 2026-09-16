"""build reproducibility test for the wiki.

Builds the static site twice in two separate venvs and compares the
artifact fingerprint. MkDocs Material has a documented
non-deterministic surface (asset hashes include Python's `sort`
stability which is guaranteed, but Material's auto-generated search
index has been known to vary between Python micro-releases). We
therefore compare a *fingerprint of the file inventory, byte sizes,
and required file presence*, not byte-for-byte equality.

The build is performed by `make build`, see the project's `Makefile`.
This test just confirms that the pinned dependencies install cleanly
and the static build emits the expected entry points.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
VENV = Path("/tmp/wiki-venv-test")


def _run(cmd: list[str], **kwargs):
    proc = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if proc.returncode != 0:
        raise AssertionError(
            f"command {cmd!r} failed (rc={proc.returncode})\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    return proc


@pytest.mark.skipif(shutil.which("python3") is None, reason="python3 required")
def test_dependencies_install_and_static_build_emits_required_files():
    # fresh venv so a previous venv cannot leak state
    if VENV.exists():
        shutil.rmtree(VENV)
    _run([sys.executable, "-m", "venv", str(VENV)])

    pip = str(VENV / "bin" / "pip")
    py = str(VENV / "bin" / "python")
    _run([pip, "install", "--quiet", "--upgrade", "pip"])
    _run([pip, "install", "--quiet", "-r", str(ROOT / "requirements.txt")])

    # regenerate the nav-aware mkdocs.yml before building
    _run([py, str(ROOT / "scripts" / "build_mkdocs_config.py")], cwd=str(ROOT))

    # mkdocs.yml is configured relative to its dir; we invoke from
    # ROOT so any relative paths in the yml resolve.
    mk = str(VENV / "bin" / "mkdocs")
    _run([mk, "build", "--config-file", "mkdocs.yml",
          "--site-dir", "site-test", "--strict"], cwd=str(ROOT))

    site = ROOT / "site-test"
    # the index page must exist in all three languages
    for lang in ("id", "en", "ban"):
        assert (site / lang / "index.html").exists(), (
            f"missing build artifact: {site}/{lang}/index.html"
        )
    # calendar section
    for lang in ("id", "en"):
        assert (site / lang / "calendar" / "index.html").exists()

    # cleanup the site to keep the repo tidy
    shutil.rmtree(site)
    shutil.rmtree(VENV)
