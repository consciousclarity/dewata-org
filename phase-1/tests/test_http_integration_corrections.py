"""Live HTTP integration test for the corrections follow-up to PR #15.

The user's verification requirement: "Candidate identity and
unsupported-observance status reach the actual HTTP responses."

This test boots the real `phase-1/src/api/main.py` via uvicorn on a
random port, hits it with `httpx`, and asserts that the JSON
response carries `candidate_id` and `unimplemented_observances`.
It does NOT touch production; the uvicorn process lives only for
the test.
"""

from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_http(url: str, timeout: float = 10.0) -> bool:
    """poll the URL until it returns 200 or timeout."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            r = httpx.get(url, timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


@pytest.fixture(scope="module")
def uvicorn_server():
    """boot the real api on a free port; tear down at end of module.

    The api package lives at phase-1/src/api (not under
    dewatacalendar). The systemd unit ExecStart is
    `/opt/dewata.online/.venv/bin/uvicorn api.main:app`. We mirror
    that: PYTHONPATH includes phase-1/src, and the module path is
    `api.main:app`.
    """
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "phase-1" / "src")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(REPO_ROOT / "phase-1"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        if not _wait_for_http(f"{base}/health"):
            try:
                stdout, stderr = proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate(timeout=2)
            pytest.fail(
                f"uvicorn failed to start within timeout.\n"
                f"stdout: {stdout.decode(errors='replace')[-1000:]}\n"
                f"stderr: {stderr.decode(errors='replace')[-1000:]}"
            )
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def test_http_response_carries_candidate_id(uvicorn_server):
    """F2: real HTTP response must include candidate_id."""
    base = uvicorn_server
    r = httpx.get(f"{base}/dsp/v0.1/calendar/date/2026-09-20", timeout=5.0)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:300]}"
    body = r.json()
    assert body["candidate_id"].startswith("candidate-"), (
        f"F2: HTTP response missing candidate_id; got {body.get('candidate_id')!r}"
    )
    # And the ruleset must still be present.
    assert body["ruleset"] == "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"


def test_http_response_carries_unimplemented_observances(uvicorn_server):
    """F5: real HTTP response must surface unimplemented_observances."""
    base = uvicorn_server
    r = httpx.get(f"{base}/dsp/v0.1/calendar/date/2026-09-20", timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    assert set(body["unimplemented_observances"]) == {"purnama", "tilem", "nyepi"}, (
        f"F5: HTTP response missing unimplemented_observances; got "
        f"{body.get('unimplemented_observances')!r}"
    )


def test_http_response_carries_diagnostic_field(uvicorn_server):
    """F1: real HTTP response must include the diagnostic year value."""
    base = uvicorn_server
    r = httpx.get(f"{base}/dsp/v0.1/calendar/date/2026-09-20", timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    # Public field is None; diagnostic field has the raw formula output.
    assert body["saka"]["saka_year"] is None
    assert body["saka"]["saka_year_diagnostic_january_rollover"] == 1948


def test_http_response_carries_note_when_rahinan_empty(uvicorn_server):
    """F5: empty rahinan on 2026-09-20 must carry the explanatory note."""
    base = uvicorn_server
    r = httpx.get(f"{base}/dsp/v0.1/calendar/date/2026-09-20", timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    assert body["rahinan"] == []
    assert body["note"] is not None
    for term in ("purnama", "tilem", "nyepi"):
        assert term in body["note"], (
            f"F5: HTTP response note must mention {term!r}; "
            f"got {body['note']!r}"
        )
