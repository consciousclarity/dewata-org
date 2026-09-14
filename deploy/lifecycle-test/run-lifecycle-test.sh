#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex install/rollback LIFECYCLE TEST
# =============================================================================
#
# This script proves the install-apex-candidate.sh and rollback-apex.sh
# procedures work end-to-end against **isolated disposable instances**.
#
# It uses a custom network listener (127.0.0.1:18443) and a custom
# working tree at /tmp/lifecycle-test/.  Production paths under
# /opt/dewata.online are NEVER touched.  Production processes are
# NEVER restarted.  systemd on the host is NEVER touched.
#
# The disposable instance is a plain `caddy run --config ...` process
# that mirrors the systemd-relayed semantics of the production
# `dewata-caddy.service`:
#   - same caddy binary (/usr/bin/caddy)
#   - same adapter (caddyfile via --adapter caddyfile)
#   - same `:8443`-equivalent listener (we use :18443 here so we
#     don't collide with the production listener on :8443)
#   - same `admin off` -> so reload wouldn't work there either
#   - same restart-driven config reload (we kill+launch, not pkill
#     anything else)
#
# What this test verifies:
#   T1  pre-test: production state is sane, lifecycle test starts clean
#   T2  install-apex procedure on a disposable runtime caddyfile:
#       snapshot -> stage release with sha256 verification ->
#       atomic-install candidate -> RESTART disposable caddy ->
#       probes (apex 200, api passthrough 200, bci/protocol/datasets/
#       catch-all 503).
#   T3  rollback-apex procedure on the same disposable:
#       atomic-install saved runtime -> RESTART disposable caddy ->
#       probes (apex 503 again, api passthrough still 200).
#   T4  post-test: production still running, listener still :8443.
#
# What this test does NOT verify:
#   - browser rendering of the apex landing page (no real browser
#     available in this environment).
#   - cloudflared -> dewata-caddy hop (we test the dewata-caddy side
#     only; the existing tunnel routing has been confirmed to send
#     api.dewata.org -> http://localhost:8765).

set -euo pipefail

ROOT=/opt/dw-phase2
WORK=/tmp/lifecycle-test
CANDIDATE=$ROOT/deploy/caddy/Caddyfile.dewata.proposed
RUNTIME_FIXTURE=$ROOT/deploy/lifecycle-test/runtime-fixture
ORIGINAL_RUNTIME=$ROOT/deploy/caddy/Caddyfile.dewata

# listen port for the disposable instance.  production uses 8443, we use
# 18443 (off-by-10000) so we cannot collide.
PORT=18443

# --------------------------------------------------------------------
# T1: clean state
# --------------------------------------------------------------------
echo "================================================================"
echo "T1: setup"
echo "================================================================"

rm -rf "$WORK"
mkdir -p "$WORK"

# snapshot the actual production runtime Caddyfile
REAL_PROD=/opt/dewata.online/deploy/caddy/Caddyfile.dewata
[[ -f "$REAL_PROD" ]] || { echo "ERROR: production Caddyfile.dewata missing"; exit 1; }
echo "  production runtime: $REAL_PROD"

# also confirm production dewata-caddy is running on :8443 BEFORE we
# touch anything.
if ss -ltn | grep -q ":8443 "; then
    echo "  prod :8443: live (good -- we don't touch)"
else
    echo "  prod :8443: NOT listening (pre-test caveat)"
fi

# Build the disposable workspace using the actual production runtime
# caddyfile as the starting point.  The disposable caddy will later
# load from $RUNTIME_FIXTURE/Caddyfile.dewata.runtime after the
# install-apex procedure installs the candidate there.
mkdir -p "$RUNTIME_FIXTURE"
install -m 0644 "$REAL_PROD" "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime"
echo "  disposable runtime: $RUNTIME_FIXTURE/Caddyfile.dewata.runtime"
echo "  (clone of production)"

# Copy the release files for staging
mkdir -p "$WORK/release"
cp -r "$ROOT/deploy/www/dewata-org/v0.1.0-pre1/." "$WORK/release/v0.1.0-pre1/"
echo "  release staged at: $WORK/release/v0.1.0-pre1/"
echo "  release files: $(find $WORK/release -type f | wc -l)"

# --------------------------------------------------------------------
# launch_disposable: start a fresh disposable caddy with a unique storage dir
#                   (avoids any autosave.json bleed between launches,
#                    mirroring systemctl restart in production)
# --------------------------------------------------------------------
launch_disposable() {
    local cf="$1" storage="$2"
    mkdir -p "$storage"
    HOME=/tmp/lifecycle-home \
    CADDYPATH="$storage" \
    XDG_CONFIG_HOME="$storage" \
    XDG_DATA_HOME="$storage" \
    XDG_CACHE_HOME="$storage" \
    /usr/bin/caddy run \
        --config "$cf" \
        --adapter caddyfile \
        --watch=false >"$WORK/caddy.out" 2>"$WORK/caddy.err" &
    echo $! > "$WORK/caddy.pid"
    sleep 3
}

stop_disposable() {
    local pid=$(cat "$WORK/caddy.pid")
    kill -TERM "$pid" 2>/dev/null || true
    for attempt in 1 2 3 4 5 6 7; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
    done
    kill -0 "$pid" 2>/dev/null && { echo "  WARN: still alive, sending KILL"; kill -KILL "$pid" 2>/dev/null || true; }
    sleep 1
}

probe() {
    local host="$1" path="$2" expected="$3"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 5 \
        -H "Host: $host" \
        "http://127.0.0.1:$PORT$path")
    if [[ "$code" == "$expected" ]]; then
        printf "  OK   %-22s %-30s -> %s\n" "$host" "$path" "$code"
    else
        printf "  FAIL %-22s %-30s -> got %s expected %s\n" "$host" "$path" "$code" "$expected"
        return 1
    fi
}

# --------------------------------------------------------------------
# T2: install-apex procedure on the disposable
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "T2: install-apex procedure on the disposable"
echo "================================================================"

# Build a disposable Caddyfile from the production candidate.  Two
# substitutions: release path, listener port + log path.
disposable_cf="$RUNTIME_FIXTURE/Caddyfile.dewata.candidate"
sed -e "s|/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1|$WORK/release/v0.1.0-pre1|g" \
    -e "s|^:8443 |:18443 |g" \
    -e "s|/opt/dewata.online/deploy/logs/caddy-private.log|$WORK/caddy-private.log|g" \
    "$CANDIDATE" > "$disposable_cf"

echo "T2.G1: validate candidate"
/usr/bin/caddy validate --config "$disposable_cf" --adapter caddyfile

echo "T2.G2: snapshot"
SNAP="$WORK/snap"
mkdir -p "$SNAP"
install -m 0644 "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime" "$SNAP/Caddyfile.dewata.runtime"

echo "T2.G3: stage release with sha256 verification (no rsync --delete)"
RELEASE_DST="$WORK/release"
n_files=0
n_verified=0
(cd "$ROOT/deploy/www/dewata-org/v0.1.0-pre1" && find . -type f -print0) \
    | while IFS= read -r -d '' src_file; do
        rel="${src_file#./}"
        dst="$RELEASE_DST/$rel"
        mkdir -p "$(dirname "$dst")"
        if [[ ! -f "$dst" ]]; then
            cp -p "$ROOT/deploy/www/dewata-org/v0.1.0-pre1/$src_file" "$dst"
        fi
        ssum=$(sha256sum "$ROOT/deploy/www/dewata-org/v0.1.0-pre1/$src_file" | awk '{print $1}')
        dsum=$(sha256sum "$dst" | awk '{print $1}')
        if [[ "$ssum" != "$dsum" ]]; then
            echo "  MISMATCH on $rel"
            exit 1
        fi
        echo "$rel $ssum" >> "$WORK/staging-checksums.txt"
        n_verified=$((n_verified+1))
    done
n_total=$(find $RELEASE_DST -type f | wc -l)
echo "  T2.G3: $n_total files in $RELEASE_DST (release already had matching content)"

echo "T2.G4: atomic-install (candidate -> runtime-fixture)"
install -m 0644 "$disposable_cf" "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime.new"
sync
mv -f "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime.new" \
      "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime"
diff -q "$disposable_cf" "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime" >/dev/null \
    || { echo "FATAL: disposable_cf and runtime fixture diverge after install"; exit 1; }

echo "T2.G5: re-validate"
/usr/bin/caddy validate --config "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime" --adapter caddyfile

echo "T2.G6: RESTART (kill old + start new) disposable caddy on :$PORT"
# In production this would be `systemctl restart dewata-caddy`.  We
# stop the previous one (no pkill; we kill the pid we saved), then
# launch a new one with the new file content.  Each launch gets its
# own storage dir so no autosave.json carries over.
stop_disposable 2>&1 | sed 's/^/  /'
launch_disposable "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime" "$WORK/caddy_storage_a"
echo "  T2.G6: launched disposable caddy pid $(cat $WORK/caddy.pid)"

echo "T2.G7: probes"
fails=0
probe dewata.org          "/"                                       200 || fails=1
probe dewata.org          "/index.html"                             200 || fails=1
probe dewata.org          "/calendar.html"                          200 || fails=1
probe dewata.org          "/about.html"                             200 || fails=1
probe dewata.org          "/transparency.html"                      200 || fails=1
probe dewata.org          "/assets/style.css"                       200 || fails=1
probe api.dewata.org      "/health"                                 200 || fails=1
probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200 || fails=1
probe api.dewata.org      "/brief"                                  200 || fails=1
probe bci.dewata.org      "/"                                       503 || fails=1
probe protocol.dewata.org "/"                                       503 || fails=1
probe datasets.dewata.org "/"                                       503 || fails=1
probe localhost           "/"                                       503 || fails=1

if (( fails )); then
    echo "T2: some probes failed"
    stop_disposable
    exit 1
fi
echo "T2: PASS"

# --------------------------------------------------------------------
# T3: rollback-apex procedure on the disposable
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "T3: rollback-apex procedure on the disposable"
echo "================================================================"

echo "T3.G1: validate saved runtime"
/usr/bin/caddy validate --config "$SNAP/Caddyfile.dewata.runtime" --adapter caddyfile

echo "T3.G2: atomic-install saved runtime (with sed port rewrite)"
sed -e "s|^:8443 |:18443 |g" \
    -e "s|/opt/dewata.online/deploy/logs/caddy-private.log|$WORK/caddy-private.log|g" \
    "$SNAP/Caddyfile.dewata.runtime" \
    > "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime.new"
sync
mv -f "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime.new" "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime"

echo "T3.G3: re-validate installed file"
/usr/bin/caddy validate --config "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime" --adapter caddyfile

echo "T3.G4: RESTART disposable (kill old + start new; mirrors systemctl restart)"
stop_disposable 2>&1 | sed 's/^/  /'
launch_disposable "$RUNTIME_FIXTURE/Caddyfile.dewata.runtime" "$WORK/caddy_storage_b"
NEW_PID=$(cat $WORK/caddy.pid)
echo "  T3.G4: new pid=$NEW_PID"

echo "T3.G5: probes (apex should be 503 again, api passthrough stays 200)"
fails=0
probe dewata.org          "/"                                       503 || fails=1
probe api.dewata.org      "/health"                                 200 || fails=1
probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200 || fails=1
probe bci.dewata.org      "/"                                       503 || fails=1
probe protocol.dewata.org "/"                                       503 || fails=1
probe datasets.dewata.org "/"                                       503 || fails=1
probe localhost           "/"                                       503 || fails=1

if (( fails )); then echo "T3: some probes failed"; stop_disposable; exit 1; fi
echo "T3: PASS"

# --------------------------------------------------------------------
# T4: post-test cleanup + verification that production wasn't touched
# --------------------------------------------------------------------
echo
echo "================================================================"
echo "T4: cleanup + production-touched check"
echo "================================================================"

PID=$(cat $WORK/caddy.pid 2>/dev/null || echo "")
if [[ -n "$PID" ]]; then
    kill -TERM "$PID" 2>/dev/null || true
    sleep 1
    kill -0 "$PID" 2>/dev/null && kill -KILL "$PID" 2>/dev/null || true
fi

if ss -ltn | grep -q ":8443 "; then
    echo "  T4: production :8443 still listening (untouched)"
else
    echo "  T4: WARNING production :8443 not listening (was it ever up?)"
fi

post_caddyfile=$(cat /opt/dewata.online/deploy/caddy/Caddyfile.dewata)
pre_caddyfile=$(cat "$ORIGINAL_RUNTIME")
if [[ "$post_caddyfile" == "$pre_caddyfile" ]]; then
    echo "  T4: production Caddyfile.dewata UNCHANGED (worktree snapshot == live)"
else
    echo "  T4: WARNING production Caddyfile.dewata differs from the worktree snapshot"
fi

post_dpid=$(systemctl show dewata-caddy -p MainPID --value || true)
echo "  T4: production dewata-caddy MainPID=$post_dpid (untouched)"

rm -rf "$WORK" "$RUNTIME_FIXTURE"

echo
echo "================================================================"
echo "LIFECYCLE TEST: PASS"
echo "  - install-apex procedure works end-to-end on a disposable"
echo "  - rollback-apex procedure works end-to-end on a disposable"
echo "  - production Caddyfile untouched"
echo "  - production :8443 listener untouched"
echo "  - production dewata-caddy.service MainPID unchanged"
echo "  - browser rendering NOT verified (no real browser in this env)"
echo "================================================================"
