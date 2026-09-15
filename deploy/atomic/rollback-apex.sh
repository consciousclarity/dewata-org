#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex rollback -- sixth-bundle edition
# =============================================================================
#
# Restores the production Caddyfile + release tree from a pre-apex
# snapshot directory produced by install-apex-candidate.sh.
#
# Modes (mutually exclusive):
#   DEWATA_DISPOSABLE_MODE=1        -- operate against a disposable tree
#   DEWATA_APPLY_PRODUCTION=1       -- authorize writes to a known
#                                      production path AND restart the real
#                                      production service
#
# Disposable service-control mode:
#   DEWATA_DISPOSABLE_SERVICE_MODE  -- "restart" (default) actually invokes
#                                      restart through the configured shim;
#                                      "no-restart" skips.
#
# Required env vars (no mutable defaults):
#   DEWATA_PROD_CADDY          -- production Caddyfile
#   DEWATA_RELEASE_DST         -- production release tree (e.g.
#                                /opt/dewata.online/deploy/www/.../v0.1.0-pre1)
#   DEWATA_LISTENER_PORT       -- production listener port
#   DEWATA_WORKTREE            -- worktree root (e.g. /opt/dw-phase2)
#   DEWATA_CADDY_SERVICE       -- systemd service name (default dewata-caddy)
#   DEWATA_SYSTEMCTL_CMD       -- path to the systemctl command (overridable
#                                for tests; default "systemctl")
#
# Snapshot dir: the install saved at $SNAPSHOT_DIR (passed as $1) with:
#   Caddyfile.dewata.runtime        -- the saved production Caddyfile
#   Caddyfile.dewata.candidate      -- the failed candidate (if any)
#   Caddyfile.dewata.diff           -- diff between them
#   installed.log                   -- record of when the install ran
#   RELEASE_TREE_BACKUP.MANIFEST.txt -- sha256 + rel_path for the prior release
#                                       (replacement only; missing on first-install)
#   RELEASE_TREE_BACKUP/            -- mirror copy of the prior release's files
#                                       (replacement only; missing on first-install)
# The rollback restores:
#   1. $DEWATA_PROD_CADDY            from $SNAPSHOT_DIR/Caddyfile.dewata.runtime
#   2a. (REPLACEMENT) $DEWATA_RELEASE_DST from $SNAPSHOT_DIR/RELEASE_TREE_BACKUP/
#       -- exact-set + sha256 verified against $SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt
#   2b. (FIRST-INSTALL) $DEWATA_RELEASE_DST is removed if it exists.
#   3. caddy validates the installed Caddyfile.
#   4. pid of the running service in production (or shim-recorded pid in disposable).
# =============================================================================

set -Eeuo pipefail
shopt -u inherit_errexit 2>/dev/null || true

DISPOSABLE=${DEWATA_DISPOSABLE_MODE:-}
APPLY_PROD=${DEWATA_APPLY_PRODUCTION:-}
if [[ -n "$DISPOSABLE" && -n "$APPLY_PROD" ]]; then
    echo "FATAL: DEWATA_DISPOSABLE_MODE and DEWATA_APPLY_PRODUCTION are mutually exclusive." >&2
    exit 5
fi
if [[ -z "$DISPOSABLE" && -z "$APPLY_PROD" ]]; then
    echo "FATAL: neither DEWATA_DISPOSABLE_MODE nor DEWATA_APPLY_PRODUCTION is set." >&2
    exit 5
fi
if [[ "$DISPOSABLE" != "1" && "$APPLY_PROD" != "1" ]]; then
    echo "FATAL: mode flag must be exactly \"1\"." >&2
    exit 5
fi

require_var() {
    local name="$1"
    local hint="$2"
    if [[ -z "${!name:-}" ]]; then
        echo "FATAL: $name is unset or empty." >&2
        [[ -n "$hint" ]] && echo "  $hint" >&2
        exit 2
    fi
}
require_var DEWATA_PROD_CADDY  "supply the production Caddyfile path"
require_var DEWATA_RELEASE_DST "supply the production release tree path"
require_var DEWATA_LISTENER_PORT "supply the listener port"
require_var DEWATA_WORKTREE    "supply the worktree root"

PROD=$DEWATA_PROD_CADDY
RELEASE_DST=$DEWATA_RELEASE_DST
LISTENER_PORT=$DEWATA_LISTENER_PORT
WORKTREE=$DEWATA_WORKTREE
: "${DEWATA_CADDY_SERVICE:=dewata-caddy}"
SYSTEMCTL_CMD="${DEWATA_SYSTEMCTL_CMD:-systemctl}"
DEWATA_DISPOSABLE_SERVICE_MODE="${DEWATA_DISPOSABLE_SERVICE_MODE:-restart}"

# ---- snapshot dir
SNAPSHOT_DIR="${1:-${DEWATA_SNAPSHOT_DIR:-}}"
if [[ -z "$SNAPSHOT_DIR" ]]; then
    echo "FATAL: snapshot dir is required (positional arg or DEWATA_SNAPSHOT_DIR)" >&2
    echo "  example: $0 /opt/dw-phase2/deploy/atomic/<ts>-pre-apex" >&2
    exit 1
fi
RUNTIME_BACKUP="$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
RELEASE_TREE_BACKUP_DIR="$SNAPSHOT_DIR/RELEASE_TREE_BACKUP"
RELEASE_TREE_MANIFEST="$SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt"
REPLACEMENT_MODE=0
if [[ -d "$RELEASE_TREE_BACKUP_DIR" ]]; then
    REPLACEMENT_MODE=1
fi

if [[ ! -d "$SNAPSHOT_DIR" ]]; then
    echo "FATAL: $SNAPSHOT_DIR is not an existing directory" >&2
    exit 1
fi
if [[ ! -f "$RUNTIME_BACKUP" ]]; then
    echo "FATAL: $RUNTIME_BACKUP missing (not a pre-apex snapshot?)" >&2
    exit 1
fi

# ---- production-path guard
IS_PROD_PATH=0
case "$PROD" in
    /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*) IS_PROD_PATH=1 ;;
esac
if [[ "$IS_PROD_PATH" -eq 1 && "$APPLY_PROD" != "1" ]]; then
    echo "FATAL: refusing to rollback against production path $PROD without DEWATA_APPLY_PRODUCTION=1." >&2
    exit 4
fi
if [[ "$IS_PROD_PATH" -eq 0 && "$APPLY_PROD" == "1" ]]; then
    echo "FATAL: DEWATA_APPLY_PRODUCTION=1 set but DEWATA_PROD_CADDY ($PROD) is not a known production path." >&2
    exit 4
fi

# ---- helpers
sha256_of_file() { sha256sum "$1" | cut -d' ' -f1; }
restore_failed=0

# ====================================================================
# Step 1: restore Caddyfile on disk from snapshot.
# ====================================================================
echo "================================================================"
echo "rollback step 1: restore Caddyfile on disk"
echo "================================================================"
echo "rollback step 1: install $RUNTIME_BACKUP to $PROD"
PRE_ROLLBACK_PROD_SHA=$(sha256_of_file "$PROD")
echo "rollback step 1: pre-rollback $PROD sha256 = $PRE_ROLLBACK_PROD_SHA"

# Failure-injection hook for the validate step (corrupt runtime)
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "rollback-validate" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=rollback-validate -> corrupting snapshot runtime" >&2
    printf "\\n{ broken syntax\\n" >> "$RUNTIME_BACKUP"
fi

install -m 0644 "$RUNTIME_BACKUP" "$PROD.new"
sync
mv -f "$PROD.new" "$PROD"
POST_ROLLBACK_PROD_SHA=$(sha256_of_file "$PROD")
echo "rollback step 1: post-rollback $PROD sha256 = $POST_ROLLBACK_PROD_SHA"

# ====================================================================
# Step 2: restore the release tree (REPLACEMENT or FIRST-INSTALL).
# ====================================================================
echo
echo "================================================================"
echo "rollback step 2: restore release tree"
echo "================================================================"
if (( REPLACEMENT_MODE )); then
    echo "rollback step 2: REPLACEMENT mode: restoring prior release from $RELEASE_TREE_BACKUP_DIR"
    # CRITICAL: the snapshot's $RELEASE_TREE_BACKUP_DIR is the recovery
    # copy -- it must NOT be consumed by this rollback.  We COPY it
    # into a separate staging sibling (NOT $RELEASE_DST), verify the
    # copy against the manifest, then atomically publish.
    #
    # Sequence:
    #   1. Create staging dir at $RELEASE_DST.stage-rollback.<ts>
    #   2. cp -a $RELEASE_TREE_BACKUP_DIR/. $RELEASE_DST.stage-rollback.<ts>/
    #   3. Verify staged file set + sha256 against $RELEASE_TREE_MANIFEST
    #   4. Atomically: move $RELEASE_DST aside (if present) to .rejected.<ts>
    #      then move staging -> $RELEASE_DST
    #   5. The snapshot's $RELEASE_TREE_BACKUP_DIR is INTACT and can be
    #      used for repeated rollback.
    STAGING_ROLLBACK_DIR="$RELEASE_DST.stage-rollback.$(date -u +%Y%m%dT%H%M%SZ)"
    if [[ -d "$RELEASE_TREE_BACKUP_DIR" ]]; then
        # Step 1+2: stage
        mkdir -p "$STAGING_ROLLBACK_DIR"
        if ! cp -a "$RELEASE_TREE_BACKUP_DIR/." "$STAGING_ROLLBACK_DIR/"; then
            echo "  RESTORE FAILED: could not cp -a $RELEASE_TREE_BACKUP_DIR -> $STAGING_ROLLBACK_DIR" >&2
            restore_failed=1
            rm -rf "$STAGING_ROLLBACK_DIR"
        else
            # Step 3: verify staged file set + sha256 against manifest
            # (BEFORE moving anything into $RELEASE_DST)
            staged_ok=1
            if [[ -f "$RELEASE_TREE_MANIFEST" ]]; then
                snapshot_files=$(awk '/^[a-f0-9]/{print $2}' "$RELEASE_TREE_MANIFEST" | sort -u)
                staged_files=$( ( cd "$STAGING_ROLLBACK_DIR" && find . -type f ) | sed 's|^./||' | sort -u )
                if [[ "$snapshot_files" != "$staged_files" ]]; then
                    echo "  RESTORE FAILED: staged copy file-set does not match snapshot manifest" >&2
                    staged_ok=0
                else
                    n_staged=$(echo "$staged_files" | wc -l)
                    echo "  staged $n_staged files; verifying sha256 against manifest..."
                    sha_mismatch=0
                    while IFS= read -r rel; do
                        [[ -z "$rel" ]] && continue
                        actual=$(sha256sum "$STAGING_ROLLBACK_DIR/$rel" | cut -d' ' -f1)
                        expected=$(awk -v r="$rel" '$2 == r {print $1}' "$RELEASE_TREE_MANIFEST" | head -1)
                        if [[ "$actual" != "$expected" ]]; then
                            echo "  RESTORE FAILED: staged sha256 mismatch for $rel" >&2
                            sha_mismatch=1
                        fi
                    done <<< "$snapshot_files"
                    if (( sha_mismatch )); then
                        staged_ok=0
                    fi
                fi
            fi
            if (( staged_ok == 0 )); then
                restore_failed=1
                rm -rf "$STAGING_ROLLBACK_DIR"
                echo "  staging dir removed; snapshot $RELEASE_TREE_BACKUP_DIR untouched" >&2
            else
                echo "  staged copy verified against snapshot manifest"
                # Step 4: move $RELEASE_DST aside (if present) BEFORE the swap
                if [[ -d "$RELEASE_DST" ]]; then
                    if ! mv "$RELEASE_DST" "$RELEASE_DST.rejected.$(date -u +%Y%m%dT%H%M%SZ)"; then
                        echo "  RESTORE FAILED: could not move $RELEASE_DST aside" >&2
                        restore_failed=1
                        rm -rf "$STAGING_ROLLBACK_DIR"
                    fi
                fi
                # Step 5: atomic publish -- staging -> $RELEASE_DST
                if (( restore_failed == 0 )); then
                    if mv "$STAGING_ROLLBACK_DIR" "$RELEASE_DST"; then
                        echo "  prior release restored from staged copy"
                        echo "  snapshot $RELEASE_TREE_BACKUP_DIR is INTACT (repeat rollback still possible)"
                    else
                        echo "  RESTORE FAILED: could not move $STAGING_ROLLBACK_DIR to $RELEASE_DST" >&2
                        restore_failed=1
                        rm -rf "$STAGING_ROLLBACK_DIR"
                    fi
                fi
            fi
        fi
    else
        echo "  RESTORE FAILED: snapshot release backup missing at $RELEASE_TREE_BACKUP_DIR" >&2
        restore_failed=1
    fi
    # Post-publish verification: $RELEASE_TREE_BACKUP_DIR still exists
    # and the snapshot's manifest is intact (proves we did not consume
    # the only recovery copy).
    if [[ ! -d "$RELEASE_TREE_BACKUP_DIR" ]]; then
        echo "  FATAL: snapshot release backup $RELEASE_TREE_BACKUP_DIR was consumed by rollback" >&2
        restore_failed=1
    fi
    if [[ ! -f "$RELEASE_TREE_MANIFEST" ]]; then
        echo "  FATAL: snapshot release manifest $RELEASE_TREE_MANIFEST was consumed by rollback" >&2
        restore_failed=1
    fi
else
    echo "rollback step 2: FIRST-INSTALL mode: removing $RELEASE_DST (snapshot has no prior release)"
    if [[ -d "$RELEASE_DST" ]]; then
        # Preserve for inspection; mark as rejected.
        if ! mv "$RELEASE_DST" "$RELEASE_DST.rejected.$(date -u +%Y%m%dT%H%M%SZ)"; then
            echo "  RESTORE FAILED: could not move $RELEASE_DST aside" >&2
            restore_failed=1
        else
            if [[ -e "$RELEASE_DST" ]]; then
                echo "  RESTORE FAILED: $RELEASE_DST still exists after removal" >&2
                restore_failed=1
            else
                echo "  $RELEASE_DST removed (first-install end state)"
            fi
        fi
    else
        echo "  $RELEASE_DST was not present (already absent)"
    fi
fi

# ====================================================================
# Step 3: validate the restored Caddyfile.
# ====================================================================
echo
echo "================================================================"
echo "rollback step 3: validate Caddyfile"
echo "================================================================"
if /usr/bin/caddy validate --config "$PROD" --adapter caddyfile; then
    echo "  restored Caddyfile validates"
else
    echo "  RESTORE FAILED: restored Caddyfile does not validate" >&2
    restore_failed=1
fi

# ====================================================================
# Step 4: verify the restored Caddyfile's sha256 matches the snapshot's.
# ====================================================================
echo
echo "================================================================"
echo "rollback step 4: verify Caddyfile sha256"
echo "================================================================"
restored_sha=$(sha256_of_file "$PROD")
snapshot_sha=$(sha256_of_file "$RUNTIME_BACKUP")
if [[ "$restored_sha" != "$snapshot_sha" ]]; then
    echo "  RESTORE FAILED: restored $PROD sha256 ($restored_sha) does not match snapshot runtime sha256 ($snapshot_sha)" >&2
    restore_failed=1
else
    echo "  restored Caddyfile sha256 verified: $restored_sha"
fi

# ====================================================================
# Step 5: restart the service (production mode or disposable+restart mode).
# ====================================================================
echo
echo "================================================================"
echo "rollback step 5: restart $DEWATA_CADDY_SERVICE"
echo "================================================================"

if [[ "$POST_ROLLBACK_PROD_SHA" == "$PRE_ROLLBACK_PROD_SHA" ]]; then
    echo "  rollback was a no-op (post == pre, sha $PRE_ROLLBACK_PROD_SHA); skipping restart"
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID="$OLD_PID"
elif [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]]; then
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    echo "  pre-restart $DEWATA_CADDY_SERVICE MainPID=$OLD_PID"
    if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
        echo "  DEWATA_FAKE_RESTART_FAILURE=1 -> shim sees rollback-restart failure"
        ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE" || true
        NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    else
        ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE"
        for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
            state=$(${SYSTEMCTL_CMD:-systemctl} is-active "$DEWATA_CADDY_SERVICE" || true)
            if [[ "$state" == "active" ]]; then break; fi
            sleep 1
        done
        NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    fi
    echo "  post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID"
    if [[ "${DEWATA_PROBE_LISTENER:-1}" == "1" ]]; then
        if ss -ltn 2>/dev/null | grep -q ":$LISTENER_PORT "; then
            echo "  :$LISTENER_PORT listening"
        else
            echo "  RESTORE FAILED: :$LISTENER_PORT not listening after restart" >&2
            restore_failed=1
        fi
    fi
elif [[ "$DISPOSABLE" == "1" && "$DEWATA_DISPOSABLE_SERVICE_MODE" == "restart" ]]; then
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    echo "  pre-restart $DEWATA_CADDY_SERVICE MainPID=$OLD_PID"
    if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
        ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE" || true
        NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    else
        ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE"
        NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
    fi
    echo "  post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID"
elif [[ "$DISPOSABLE" == "1" && "$DEWATA_DISPOSABLE_SERVICE_MODE" == "no-restart" ]]; then
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID=0
    echo "  DISPOSABLE+no-restart -> skipping restart"
else
    echo "FATAL: no valid restart mode (APPLY_PROD=$APPLY_PROD IS_PROD_PATH=$IS_PROD_PATH DISPOSABLE=$DISPOSABLE SERVICE_MODE=$DEWATA_DISPOSABLE_SERVICE_MODE)" >&2
    exit 6
fi

# ====================================================================
# Result
# ====================================================================
if (( restore_failed )); then
    echo
    echo "ROLLBACK INCOMPLETE: inspect $PROD and $RELEASE_DST manually." >&2
    exit 2
fi
echo
echo "================================================================"
echo "ROLLBACK SUCCESS"
echo "================================================================"
echo "  mode:        $([[ "$APPLY_PROD" == "1" ]] && echo PRODUCTION || echo DISPOSABLE)"
echo "  snapshot:    $SNAPSHOT_DIR"
echo "  caddyfile:   $PROD restored from $RUNTIME_BACKUP"
echo "  release:     $RELEASE_DST (REPLACEMENT=$REPLACEMENT_MODE)"
echo "  restart:     $([[ -n "$NEW_PID" && "$NEW_PID" != "$OLD_PID" ]] && echo "yes, MainPID $OLD_PID -> $NEW_PID" || echo "skipped (no live change or no-restart)")"

mkdir -p "$SNAPSHOT_DIR"
echo "$(date -u +%Y%m%dT%H%M%SZ)  rollback  $OLD_PID -> $NEW_PID  prod=$APPLY_PROD  disposable=$DISPOSABLE" >> "$SNAPSHOT_DIR/installed.log"
echo "  actual_snapshot_path=$SNAPSHOT_DIR"
exit 0
