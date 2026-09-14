#!/usr/bin/env bash
# ============================================================
# Dewata apex deployment lifecycle test
# ============================================================
# This driver exercises the REAL install-apex-candidate.sh and the REAL
# rollback-apex.sh against an isolated disposable tree on :18443. It does
# NOT invent its own install/rollback — it controls the caddy lifecycle
# between disk operations.
#
# Phases:
#   T0  setup disposable dirs + reviewed manifest
#   T1  capture production baselines (read-only)
#   T2  drive install-apex-candidate.sh against the disposable
#       (atomic install of the candidate caddyfile; DEWATA_TEST_MODE=1
#        short-circuits the systemctl call)
#   T3  launch disposable caddy with the pre-install caddyfile,
#       probe baseline (apex 503, api 200)
#   T4  launch disposable caddy with the post-install caddyfile,
#       probe apex pages and api passthrough
#   T5  drive rollback-apex.sh against the disposable
#       (atomic restore of the snapshot caddyfile)
#   T6  launch disposable caddy with the post-rollback caddyfile,
#       probe apex back to 503, api still 200
#   T7  verify production untouched
#   T8  cleanup owned paths/processes
# ============================================================

set -euo pipefail

WORKTREE=/opt/dw-phase2
INSTALL_SH=$WORKTREE/deploy/atomic/install-apex-candidate.sh
ROLLBACK_SH=$WORKTREE/deploy/atomic/rollback-apex.sh
REVIEWED_MANIFEST=$WORKTREE/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt
CAND_SOURCE=$WORKTREE/deploy/caddy/Caddyfile.dewata.proposed
RELEASE_SOURCE=$WORKTREE/deploy/www/dewata-org/v0.1.0-pre1
CADDY=/usr/bin/caddy
TEST_PORT=18443
LOG_PREFIX="[lifecycle-test]"

# unique work directory; owned and removed by T8 only
WORK=$(mktemp -d /tmp/dewata-lifecycle.XXXXXXXX)
DISP_BASE=$WORK/disp
DISP_CADDY_DIR=$DISP_BASE/caddy
DISP_WWW_DIR=$DISP_BASE/www
DISP_BASE_LOG=$WORK/disposable.log
TRACKED_PIDS=()

cleanup() {
    set +e
    for pid in "${TRACKED_PIDS[@]:-}"; do
        kill -TERM "$pid" 2>/dev/null
    done
    sleep 1
    for pid in "${TRACKED_PIDS[@]:-}"; do
        kill -KILL "$pid" 2>/dev/null
    done
    if [[ -z "${DEWATA_LIFECYCLE_KEEP:-}" ]]; then
        rm -rf "$WORK"
    fi
}
trap cleanup EXIT

# Launch a disposable caddy process isolated to its own XDG storage,
# so it never collides with the production caddy on :8443 and never
# opens the production-default :2019 admin endpoint.
launch_disposable_caddy() {
    local caddyfile="$1"
    local XDG_STORAGE="$WORK/xdg-storage-$$-$BASHPID"
    mkdir -p "$XDG_STORAGE"
    HOME="$WORK/h-$$-$BASHPID" \
        XDG_DATA_HOME="$XDG_STORAGE" \
        DEWATA_RELEASE_ROOT="$DISP_WWW_DIR/dewata-org/v0.1.0-pre1" \
        DEWATA_LOG_FILE="$WORK/disposable-caddy.log" \
        "$CADDY" run --config "$caddyfile" --adapter caddyfile > "$DISP_BASE_LOG" 2>&1 &
    local pid=$!
    TRACKED_PIDS+=("$pid")
    # Wait up to 8s for the listener to come up
    for attempt in 1 2 3 4 5 6 7 8; do
        sleep 1
        if ss -ltn 2>/dev/null | grep -q ":$TEST_PORT "; then
            return 0
        fi
    done
    echo "$LOG_PREFIX ERROR: caddy (pid $pid) did not bind :$TEST_PORT"
    cat "$DISP_BASE_LOG"
    return 1
}

stop_disposable_caddy() {
    local pid
    for pid in "${TRACKED_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
        fi
    done
    sleep 2
    for pid in "${TRACKED_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null
        fi
    done
    TRACKED_PIDS=()
    # Wait for the port to be free
    for attempt in 1 2 3 4 5; do
        if ! ss -ltn 2>/dev/null | grep -q ":$TEST_PORT "; then
            return 0
        fi
        sleep 1
    done
}

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T0: setup"
echo "================================================================"
echo "  work directory: $WORK"

mkdir -p "$DISP_CADDY_DIR" "$DISP_WWW_DIR"

# Copy the production Caddyfile to the disposable, substitute :8443 -> :$TEST_PORT
# and append auto_https off so the disposable never tries to bind :8443 (the prod
# listener) or open :2019 (the host admin endpoint).
cp "$WORKTREE/deploy/caddy/Caddyfile.dewata.runtime" "$DISP_CADDY_DIR/Caddyfile.dewata"

# Insert "auto_https off" inside the global options block (or top-level)
# and rewrite :8443 to :$TEST_PORT.  We use python3 because the substitution
# has to be precise.
python3 <<PYEOF
cf_path = "$DISP_CADDY_DIR/Caddyfile.dewata"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
pass  # auto_https off injection skipped
open(cf_path, "w").write(src)
PYEOF

# Pre-compute the disposable pre-install sha for drift protection
DISP_PRE_INSTALL_SHA=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | awk '{print $1}')

echo "  disposable pre-install sha: ${DISP_PRE_INSTALL_SHA:0:16}..."

# Validate the disposable Caddyfile directly so we know T3 will start it
"$CADDY" validate --config "$DISP_CADDY_DIR/Caddyfile.dewata" --adapter caddyfile > /dev/null
echo "  disposable caddyfile: valid"

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T1: capture production baselines (read-only)"
echo "================================================================"

PROD_MAIN_PID=$(systemctl show dewata-caddy -p MainPID --value)
PROD_LISTENER=$([ -n "$(ss -ltn 2>/dev/null | grep ':8443 ')" ] && echo yes || echo no)
PROD_CADDY_PRE_SHA=$(sha256sum "$WORKTREE/deploy/caddy/Caddyfile.dewata.runtime" | awk '{print $1}')

echo "  prod dewata-caddy.MainPID: $PROD_MAIN_PID"
echo "  prod :8443 listener     : $PROD_LISTENER"
echo "  prod Caddyfile.dewata  : ${PROD_CADDY_PRE_SHA:0:16}..."
echo "  prod release v0.1.0-pre1: $([ -d '/opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1' ] && echo yes || echo none)"

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T2: drive install-apex-candidate.sh (file operations only)"
echo "================================================================"

# T2 invokes the REAL install script against the disposable tree. The
# install script DEWATA_TEST_MODE=1 short-circuits systemctl restart;
# it only stages files, atomically installs the candidate caddyfile, and
# validates. It does NOT know which caddy is running or will run next.

env -i PATH="$PATH" HOME="$WORK" \
    DEWATA_TEST_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_CADDY_DIR/Caddyfile.dewata" \
    DEWATA_PROD_WWW="$DISP_WWW_DIR" \
    DEWATA_PROD_BASELINE_SHA="$DISP_PRE_INSTALL_SHA" \
    DEWATA_REVIEWED_MANIFEST="$REVIEWED_MANIFEST" \
    DEWATA_LISTENER_PORT="$TEST_PORT" \
    bash "$INSTALL_SH"

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T3: launch baseline (pre-install) disposable caddy and probe"
echo "================================================================"

# T3 launches the caddy using the BASELINE caddyfile (saved by the
# installer into $SNAPSHOT_DIR).  The probe baseline must be: apex 503
# (catch-all), api 200.
SNAPSHOT_DIR=$(ls -1d "$WORKTREE"/deploy/atomic/*-pre-apex | sort | tail -1)
echo "  T3: snapshot baseline at $SNAPSHOT_DIR"
cp "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" "$DISP_CADDY_DIR/Caddyfile.dewata"
# Apply test-mode substitution (port + auto_https off) for the baseline
python3 <<PYEOF3
cf_path = "$DISP_CADDY_DIR/Caddyfile.dewata"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
pass  # auto_https off injection skipped
open(cf_path, "w").write(src)
PYEOF3
launch_disposable_caddy "$DISP_CADDY_DIR/Caddyfile.dewata"
PRE_T3_PID=$!

PRE_INSTALL_RESULTS=$(curl -s -o /tmp/probe.body -w "%{http_code}" --max-time 5 \
    -H "Host: dewata.org" "http://127.0.0.1:$TEST_PORT/" || echo 000)
PRE_INSTALL_BODY_SHA=$(sha256sum /tmp/probe.body 2>/dev/null | awk '{print $1}')
echo "  T3 dewata.org / -> $PRE_INSTALL_RESULTS  body_sha=${PRE_INSTALL_BODY_SHA:0:16}..."

PRE_INSTALL_API=$(curl -s -o /tmp/probe.body -w "%{http_code}" --max-time 5 \
    -H "Host: api.dewata.org" "http://127.0.0.1:$TEST_PORT/health" || echo 000)
echo "  T3 api.dewata.org /health -> $PRE_INSTALL_API"

stop_disposable_caddy

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T4: launch post-install disposable caddy and probe"
echo "================================================================"

# T4 launches the caddy using the CANDIDATE caddyfile (the one the install
# script atomically wrote to $DISP_CADDY_DIR).  Apply test-mode substitution
# to bind :$TEST_PORT and disable auto_https so the disposable never collides
# with the production :8443 listener or :2019 admin endpoint.
cp "$CAND_SOURCE" "$DISP_CADDY_DIR/Caddyfile.dewata"
python3 <<PYEOF4
cf_path = "$DISP_CADDY_DIR/Caddyfile.dewata"
src = open(cf_path).read()
src = src.replace(":8443 ", ":$TEST_PORT ")
pass  # auto_https off injection skipped
open(cf_path, "w").write(src)
PYEOF4
echo "  T4: post-install disposable caddyfile sha: $(sha256sum $DISP_CADDY_DIR/Caddyfile.dewata | awk \'{print $1}\' | head -c 16)..."
launch_disposable_caddy "$DISP_CADDY_DIR/Caddyfile.dewata"
POST_T4_PID=$!

fail=0
probe() {
    local host="$1" path="$2" expected_code="$3"
    local code body_sha
    code=$(curl -s -o /tmp/probe.body -w "%{http_code}" --max-time 5 \
        -H "Host: $host" "http://127.0.0.1:$TEST_PORT$path" || echo 000)
    body_sha=$(sha256sum /tmp/probe.body 2>/dev/null | awk '{print $1}')
    if [[ "$code" == "$expected_code" ]]; then
        printf "  OK   %-22s %-30s -> %s\n" "$host" "$path" "$code"
    else
        printf "  FAIL %-22s %-30s -> got %s expected %s\n" "$host" "$path" "$code" "$expected_code"
        fail=1
    fi
}

# apex pages must serve the bci landing
probe dewata.org          "/"                                       200
probe dewata.org          "/index.html"                             200
probe dewata.org          "/calendar.html"                          200
probe dewata.org          "/about.html"                             200
probe dewata.org          "/transparency.html"                      200
probe dewata.org          "/assets/style.css"                       200
# per-locale variants: ban (Balinese primary), id, en
probe dewata.org          "/index.ban.html"                         200
probe dewata.org          "/calendar.ban.html"                      200
probe dewata.org          "/about.ban.html"                         200
probe dewata.org          "/index.id.html"                          200
probe dewata.org          "/index.en.html"                          200
# api passthrough stays unchanged
probe api.dewata.org      "/health"                                 200
probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200
probe api.dewata.org      "/brief"                                  200
# placeholders stay 503
probe bci.dewata.org      "/"                                       503
probe protocol.dewata.org "/"                                       503
probe datasets.dewata.org "/"                                       503
# random-host catches the catch-all
probe localhost           "/"                                       503

if (( fail )); then
    echo "ERROR: post-install probes failed"
    cat "$DISP_BASE_LOG" | tail -20
    exit 1
fi

# Compare response body of /index.html against the released index.html
# (default = ban).  Then compare /index.ban.html, /index.id.html,
# /index.en.html separately to confirm per-locale content.
compare_body() {
    local url_path="$1"
    local released_path="$2"
    local label="$3"
    curl -s -H "Host: dewata.org" "http://127.0.0.1:$TEST_PORT$url_path" > /tmp/probe.body
    local served_sha
    served_sha=$(sha256sum /tmp/probe.body | awk '{print $1}')
    local released_sha
    released_sha=$(sha256sum "$released_path" | awk '{print $1}')
    if [[ "$served_sha" == "$released_sha" ]]; then
        echo "  OK   body comparison: served $url_path == released $released_path ($served_sha)"
    else
        echo "  FAIL body comparison: served=$served_sha released=$released_sha"
        exit 1
    fi
}

compare_body "/index.html"        "$DISP_WWW_DIR/dewata-org/v0.1.0-pre1/index.html"        "default"
compare_body "/index.ban.html"    "$DISP_WWW_DIR/dewata-org/v0.1.0-pre1/index.ban.html"    "ban"
compare_body "/index.id.html"     "$DISP_WWW_DIR/dewata-org/v0.1.0-pre1/index.id.html"     "id"
compare_body "/index.en.html"     "$DISP_WWW_DIR/dewata-org/v0.1.0-pre1/index.en.html"     "en"
compare_body "/calendar.ban.html" "$DISP_WWW_DIR/dewata-org/v0.1.0-pre1/calendar.ban.html" "calendar.ban"

stop_disposable_caddy

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T5: drive rollback-apex.sh (file operations only)"
echo "================================================================"

# Find the snapshot directory created by the installer
SNAPSHOT_DIR=$(ls -1d "$WORKTREE"/deploy/atomic/*-pre-apex | sort | tail -1)
echo "  using snapshot: $SNAPSHOT_DIR"

env -i PATH="$PATH" HOME="$WORK" \
    DEWATA_TEST_MODE=1 \
    DEWATA_PROD_CADDY="$DISP_CADDY_DIR/Caddyfile.dewata" \
    DEWATA_SNAPSHOT_DIR="$SNAPSHOT_DIR" \
    DEWATA_RELEASE_DST="$DISP_WWW_DIR/dewata-org/v0.1.0-pre1" \
    DEWATA_LISTENER_PORT="$TEST_PORT" \
    bash "$ROLLBACK_SH" "$SNAPSHOT_DIR"

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T6: launch post-rollback disposable caddy and probe"
echo "================================================================"

# After rollback, the disposable caddyfile should be the BASELINE
# again (apex 503 catch-all, api 200).
DISP_POST_ROLLBACK_SHA=$(sha256sum "$DISP_CADDY_DIR/Caddyfile.dewata" | awk '{print $1}')
echo "  post-rollback caddyfile sha: ${DISP_POST_ROLLBACK_SHA:0:16}..."
echo "  baseline caddyfile sha     : ${DISP_PRE_INSTALL_SHA:0:16}..."
if [[ "$DISP_POST_ROLLBACK_SHA" != "$DISP_PRE_INSTALL_SHA" ]]; then
    echo "  FAIL rollback did not restore baseline caddyfile"
    exit 1
fi

launch_disposable_caddy "$DISP_CADDY_DIR/Caddyfile.dewata"
POST_T6_PID=$!

probe_post_rollback() {
    local host="$1" path="$2" expected_code="$3"
    local code
    code=$(curl -s -o /tmp/probe.body -w "%{http_code}" --max-time 5 \
        -H "Host: $host" "http://127.0.0.1:$TEST_PORT$path" || echo 000)
    if [[ "$code" == "$expected_code" ]]; then
        printf "  OK   %-22s %-30s -> %s\n" "$host" "$path" "$code"
    else
        printf "  FAIL %-22s %-30s -> got %s expected %s\n" "$host" "$path" "$code" "$expected_code"
        exit 1
    fi
}

# After rollback: apex 503 catch-all, api passthrough 200
probe_post_rollback dewata.org          "/"            503
probe_post_rollback dewata.org          "/index.html"  503
probe_post_rollback api.dewata.org      "/health"      200
probe_post_rollback bci.dewata.org      "/"            503
probe_post_rollback localhost           "/"            503

stop_disposable_caddy

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T7: production untouched"
echo "================================================================"

POST_PROD_MAIN_PID=$(systemctl show dewata-caddy -p MainPID --value)
POST_PROD_LISTENER=$([ -n "$(ss -ltn 2>/dev/null | grep ':8443 ')" ] && echo yes || echo no)
POST_PROD_CADDY_SHA=$(sha256sum "$WORKTREE/deploy/caddy/Caddyfile.dewata.runtime" | awk '{print $1}')

if [[ "$PROD_MAIN_PID" != "$POST_PROD_MAIN_PID" ]]; then
    echo "  FAIL prod MainPID changed: $PROD_MAIN_PID -> $POST_PROD_MAIN_PID"
    exit 1
fi
if [[ "$PROD_LISTENER" != "$POST_PROD_LISTENER" ]]; then
    echo "  FAIL prod :8443 listener changed: $PROD_LISTENER -> $POST_PROD_LISTENER"
    exit 1
fi
if [[ "$PROD_CADDY_PRE_SHA" != "$POST_PROD_CADDY_SHA" ]]; then
    echo "  FAIL prod Caddyfile.dewata sha changed: $PROD_CADDY_PRE_SHA -> $POST_PROD_CADDY_SHA"
    exit 1
fi

echo "  prod dewata-caddy.MainPID: $PROD_MAIN_PID (unchanged)"
echo "  prod :8443 listener     : $POST_PROD_LISTENER (unchanged)"
echo "  prod Caddyfile.dewata  : ${POST_PROD_CADDY_SHA:0:16}... (unchanged)"

# ----------------------------------------------------------
echo
echo "================================================================"
echo "T8: cleanup owned paths/processes"
echo "================================================================"

# cleanup() trap handles the actual rm/kill
n_pids=0
for _pid in "${TRACKED_PIDS[@]:-}"; do
    [[ -n "$_pid" ]] && (( n_pids++ )) || true
done
echo "  cleanup: $n_pids pids, $WORK"


echo
echo "================================================================"
echo "LIFECYCLE TEST PASS"
echo "================================================================"