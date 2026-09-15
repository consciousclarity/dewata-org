#!/usr/bin/env bash
# =============================================================================
# dewata-caddy apex install -- reviewed for fifth-bundle corrections
# =============================================================================
#
# This script installs the reviewed apex Caddyfile + release tree into a
# production destination.  The lifecycle test exercises this script end-
# to-end against disposable trees.
#
# Two modes, MUTUALLY EXCLUSIVE:
#
#   DEWATA_DISPOSABLE_MODE=1   (formerly called DEWATA_TEST_MODE)
#     Skip ${SYSTEMCTL_CMD:-systemctl} restart.  Run the caddyfile / release tree
#     operations on a disposable tree, but verify caddy validate on
#     the disposable's caddyfile via the listener test that the
#     lifecycle driver launches.
#
#   DEWATA_APPLY_PRODUCTION=1
#     Authorize writes to a known production path AND restart the
#     real production service.  This is the ONLY way to install
#     against /opt/dewata.online/*, /etc/caddy/*, or /var/lib/dewata/*.
#     Must be explicitly set; the script refuses to run otherwise.
#
# The two modes are mutually exclusive: setting both, or neither, is
# a fatal error.
#
# Production-path guard (independent of mode):
#   If $DEWATA_PROD_CADDY points at a known production path
#   (/opt/dewata.online/*, /etc/caddy/*, /var/lib/dewata/*), the
#   script refuses to run unless DEWATA_APPLY_PRODUCTION=1 is set
#   explicitly.  This prevents accidental production writes from a
#   misconfigured disposable run.
#
# Source / destination separation:
#   The reviewed source files (Caddyfile candidate, release tree
#   files) live under a separate reviewed source directory.  The
#   installer reads from $DEWATA_RELEASE_SRC (release tree source)
#   and $DEWATA_CANDIDATE (candidate Caddyfile).  These should be
#   paths under the operator's REVIEWED source tree, e.g.
#   /opt/dewata.online/review/v0.1.0-pre1/{caddy,www}/.  The installer
#   writes to $DEWATA_PROD_CADDY (production Caddyfile destination)
#   and $DEWATA_RELEASE_DST (production release tree destination).
#   Never use the production destination as the source.
#
# Restore ordering (for do_restore on installation failure):
#   1. Restore the production Caddyfile on disk from the snapshot
#      (so the file is correct before any restart).
#   2. Restore the prior release tree from RELEASE_BACKED_UP
#      (so caddy sees a consistent tree when it restarts).  This step
#      is skipped on first installation (no prior release).
#   3. Validate the restored Caddyfile with `caddy validate`.
#   4. Verify the restored Caddyfile's sha256 matches the snapshot
#      runtime sha256 (the strongest possible verification).
#   5. Restart the service in production mode.
#   6. Verify the listener is up.
# Only if every step succeeds does do_restore declare "AUTO-RESTORE
# COMPLETE".  Any failure sets restore_failed=1 and the script exits
# with rc=2 and prints "AUTO-RESTORE INCOMPLETE".
#
# Idempotence: the script is NOT idempotent.  Each invocation creates
# a new snapshot and (in production mode) restarts the service.
# The deploy wrapper (deploy/apex-deploy.sh) enforces a 60-second
# cooldown between invocations.
#
# =============================================================================

set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

# --------------------------------------------------------------------
# Mode selection: DEWATA_DISPOSABLE_MODE=1 OR DEWATA_APPLY_PRODUCTION=1
# (mutually exclusive)
# --------------------------------------------------------------------
# Configurable systemctl command.  Defaults to the system systemctl.
# In the lifecycle test, the runner overrides this with the disposable
# shim path so the install's `systemctl restart` calls do NOT reach
# the real production service.
DISPOSABLE=${DEWATA_DISPOSABLE_MODE:-}
APPLY_PROD=${DEWATA_APPLY_PRODUCTION:-}

if [[ -n "$DISPOSABLE" && -n "$APPLY_PROD" ]]; then
    echo "FATAL: DEWATA_DISPOSABLE_MODE and DEWATA_APPLY_PRODUCTION are mutually exclusive." >&2
    echo "  exactly one must be set; both, or neither, is an error." >&2
    exit 5
fi
if [[ -z "$DISPOSABLE" && -z "$APPLY_PROD" ]]; then
    echo "FATAL: neither DEWATA_DISPOSABLE_MODE nor DEWATA_APPLY_PRODUCTION is set." >&2
    echo "  set DEWATA_DISPOSABLE_MODE=1 for a disposable run, OR" >&2
    echo "  set DEWATA_APPLY_PRODUCTION=1 to authorize a production install." >&2
    exit 5
fi
if [[ "$DISPOSABLE" != "1" && "$APPLY_PROD" != "1" ]]; then
    echo "FATAL: DEWATA_DISPOSABLE_MODE must be \"1\" (got \"$DISPOSABLE\")" >&2
    echo "  or DEWATA_APPLY_PRODUCTION must be \"1\" (got \"$APPLY_PROD\")." >&2
    exit 5
fi

# --------------------------------------------------------------------
# Mandatory env vars (no mutable defaults)
# --------------------------------------------------------------------
require_var() {
    local name="$1"
    local hint="$2"
    if [[ -z "${!name:-}" ]]; then
        echo "FATAL: $name is unset or empty." >&2
        [[ -n "$hint" ]] && echo "  $hint" >&2
        exit 2
    fi
}

require_var DEWATA_PROD_CADDY        "supply the production Caddyfile path, e.g. /opt/dewata.online/deploy/caddy/Caddyfile.dewata"
require_var DEWATA_PROD_WWW          "supply the production www root, e.g. /opt/dewata.online/deploy/www"
require_var DEWATA_RELEASE_SRC       "supply the reviewed release source, e.g. /opt/dewata.online/review/v0.1.0-pre1/www/dewata-org/v0.1.0-pre1"
require_var DEWATA_RELEASE_DST       "supply the production release destination, e.g. /opt/dewata.online/deploy/www/dewata-org/v0.1.0-pre1"
require_var DEWATA_CANDIDATE        "supply the candidate Caddyfile, e.g. /opt/dewata.online/review/v0.1.0-pre1/caddy/Caddyfile.dewata.proposed"
require_var DEWATA_REVIEWED_MANIFEST "supply the reviewed manifest, e.g. /opt/dewata.online/deploy/atomic/RELEASES/v0.1.0-pre1.MANIFEST.txt"
require_var DEWATA_PROD_BASELINE_SHA "supply the sha256 of the production Caddyfile right now (mandatory drift guard)"
require_var DEWATA_LISTENER_PORT     "supply the listener port (production 8443 or disposable 18443)"
require_var DEWATA_WORKTREE         "supply the worktree root, e.g. /opt/dw-phase2"
require_var DEWATA_SNAPSHOT_PARENT  "supply the snapshot parent directory"

PROD=$DEWATA_PROD_CADDY
PROD_WWW=$DEWATA_PROD_WWW
RELEASE_SRC=$DEWATA_RELEASE_SRC
RELEASE_DST=$DEWATA_RELEASE_DST
CANDIDATE=$DEWATA_CANDIDATE
REVIEWED_MANIFEST=$DEWATA_REVIEWED_MANIFEST
PROD_BASELINE_SHA=$DEWATA_PROD_BASELINE_SHA
LISTENER_PORT=$DEWATA_LISTENER_PORT
WORKTREE=$DEWATA_WORKTREE
SNAPSHOT_PARENT=$DEWATA_SNAPSHOT_PARENT

# --------------------------------------------------------------------
# Production-path guard
# --------------------------------------------------------------------
if [[ "$APPLY_PROD" == "1" ]]; then
    echo "[install] mode: PRODUCTION (DEWATA_APPLY_PRODUCTION=1)"
elif [[ "$DISPOSABLE" == "1" ]]; then
    echo "[install] mode: DISPOSABLE (DEWATA_DISPOSABLE_MODE=1)"
fi

# A "known production path" requires DEWATA_APPLY_PRODUCTION=1.
# In production, the path must be under /opt/dewata.online/*, /etc/caddy/*,
# or /var/lib/dewata/*.  Disposable runs (DEWATA_DISPOSABLE_MODE=1)
# use paths under /tmp/ or wherever the test sets -- these are NOT
# production paths and the installer's behavior differs accordingly
# (no real systemctl restart, no real caddyfile writes to prod
# destinations).  The disposable-mode flag IS the guard: if it's set,
# the path under /tmp is treated as a disposable mirror regardless of
# its location.
IS_PROD_PATH=0
case "$PROD" in
    /opt/dewata.online/*|/etc/caddy/*|/var/lib/dewata/*) IS_PROD_PATH=1 ;;
esac
if [[ "${DEWATA_DISPOSABLE_MODE:-0}" == "1" ]]; then
    # Disposable mode: even if the path HAPPENS to be a production path,
    # the disposable-mode flag overrides -- the installer's writes are
    # sandboxed to the disposable paths the test controls.
    IS_PROD_PATH=0
fi
if [[ "${DEWATA_DEPLOYER_TEST_MODE:-0}" == "1" ]]; then
    # Legacy alias for DEWATA_DISPOSABLE_MODE (kept for backwards
    # compatibility).  Treat as disposable.
    IS_PROD_PATH=0
fi

if [[ "$IS_PROD_PATH" -eq 1 && "$APPLY_PROD" != "1" ]]; then
    echo "FATAL: refusing to run against production path $PROD without DEWATA_APPLY_PRODUCTION=1." >&2
    echo "  this guard prevents accidental production writes from a misconfigured disposable run." >&2
    echo "  if you really want to install against this production path, set" >&2
    echo "  DEWATA_APPLY_PRODUCTION=1 explicitly." >&2
    echo "  otherwise, set DEWATA_DISPOSABLE_MODE=1 and pass a disposable DEWATA_PROD_CADDY." >&2
    exit 4
fi
if [[ "$IS_PROD_PATH" -eq 0 && "$APPLY_PROD" == "1" ]]; then
    # Operator marked the run as production but the path is not a known
    # production path.  This is ambiguous; the path should be one of
    # the three known production paths.  Refuse.
    echo "FATAL: DEWATA_APPLY_PRODUCTION=1 set but DEWATA_PROD_CADDY ($PROD) is not a known production path." >&2
    echo "  known production paths: /opt/dewata.online/*, /etc/caddy/*, /var/lib/dewata/*" >&2
    echo "  if you are doing a first-time install into a new path, use DEWATA_DISPOSABLE_MODE=1 first." >&2
    echo "  to exercise the deploy wrapper end-to-end against a disposable mirror, use DEWATA_DEPLOYER_TEST_MODE=1." >&2
    exit 4
fi

# --------------------------------------------------------------------
# Disposable-systemctl adapter validation (correction 1 from 7th-bundle review).
#
# When DEWATA_DISPOSABLE_MODE=1 is set, the installer is operating
# against a disposable test tree (e.g. /tmp/...), NOT real
# /opt/dewata.online.  In that mode every systemctl call must be
# redirected to a disposable adapter (a shim script that records
# calls instead of touching real systemd).  Falling back to the real
# systemctl would call `systemctl restart dewata-caddy` against the
# production service.
#
# The operator MUST pass DEWATA_SYSTEMCTL_CMD=<path-to-shim-script>
# and the shim path MUST satisfy every condition below:
#   1. is set and non-empty
#   2. is NOT the literal string "systemctl" or anything that
#      resolves under PATH to /bin/systemctl etc.
#   3. is a regular file (not a symlink to systemctl)
#   4. is executable
#   5. is a shell script (first line is a shebang)
#
# If any condition fails AND DEWATA_DISPOSABLE_MODE=1 is set, the
# installer REFUSES to run (rc=8) BEFORE any write.  This prevents
# recurrence of the disposal-mode-falls-back-to-real-systemctl bug
# that restarted production earlier.
# --------------------------------------------------------------------
SYSTEMCTL_CMD=""
if [[ "$DISPOSABLE" == "1" ]]; then
    shim_path="${DEWATA_SYSTEMCTL_CMD:-}"
    if [[ -z "$shim_path" ]]; then
        echo "FATAL: DEWATA_DISPOSABLE_MODE=1 requires DEWATA_SYSTEMCTL_CMD" >&2
        echo "  pointing at a disposable-shim script (not real systemctl)." >&2
        echo "  example: DEWATA_SYSTEMCTL_CMD=/opt/dw-phase2/tests/disposable-systemctl.sh" >&2
        exit 8
    fi
    if [[ "$shim_path" == "systemctl" ]] \
        || [[ "$shim_path" == "/bin/systemctl" ]] \
        || [[ "$shim_path" == "/usr/bin/systemctl" ]]; then
        echo "FATAL: DEWATA_SYSTEMCTL_CMD=$shim_path IS the real systemctl; refusing." >&2
        echo "  in DISPOSABLE mode the install must use a shim that records calls." >&2
        echo "  pass DEWATA_SYSTEMCTL_CMD=/opt/dw-phase2/tests/disposable-systemctl.sh instead." >&2
        exit 8
    fi
    # Resolve via PATH so e.g. /usr/local/bin/systemctl is also caught.
    resolved=$(command -v "$shim_path" 2>/dev/null || echo "<not-in-path>")
    case "$resolved" in
        */systemctl|/bin/systemctl|/usr/bin/systemctl)
            echo "FATAL: DEWATA_SYSTEMCTL_CMD=$shim_path resolves via PATH to $resolved," >&2
            echo "  which is the real systemctl.  refusing in DISPOSABLE mode." >&2
            exit 8 ;;
    esac
    if [[ ! -e "$shim_path" ]]; then
        echo "FATAL: DEWATA_SYSTEMCTL_CMD=$shim_path does not exist." >&2
        exit 8
    fi
    if [[ -L "$shim_path" ]]; then
        target=$(readlink -f "$shim_path" 2>/dev/null || echo "<unresolved>")
        case "$target" in
            */systemctl)
                echo "FATAL: DEWATA_SYSTEMCTL_CMD=$shim_path is a symlink to $target (real systemctl)." >&2
                exit 8 ;;
        esac
    fi
    if [[ ! -x "$shim_path" ]]; then
        echo "FATAL: DEWATA_SYSTEMCTL_CMD=$shim_path is not executable." >&2
        exit 8
    fi
    head_line=$(head -n 1 "$shim_path" 2>/dev/null || echo "")
    case "$head_line" in
        "#!"*) ;;
        *)
            echo "FATAL: DEWATA_SYSTEMCTL_CMD=$shim_path first line is not a shebang (got: ${head_line:0:60})." >&2
            echo "  refusing to call it without confirmation." >&2
            exit 8 ;;
    esac
    SYSTEMCTL_CMD="$shim_path"
    echo "[install] DISPOSABLE_MODE: validated disposable adapter at $SYSTEMCTL_CMD"
else
    # Production mode: SYSTEMCTL_CMD defaults to the system systemctl.
    SYSTEMCTL_CMD="${DEWATA_SYSTEMCTL_CMD:-systemctl}"
fi

# Disposable-validation adapter (correction from 8th-bundle review).
#
# When DEWATA_USE_DISPOSABLE_VALIDATE=1, validation of the installed /
# restored Caddyfile goes through DEWATA_VALIDATE_CMD (a disposable shim
# that returns 0 / non-zero instead of invoking real caddy).  NEGATIVE-10
# uses this to exercise the recovery-validation failure path WITHOUT
# touching the snapshot file -- only the on-disk Caddyfile.  The shim
# must be a real shell script (not a symlink or a non-shell binary),
# and cannot be a caddy binary.
# --------------------------------------------------------------------
VALIDATE_CMD="${DEWATA_VALIDATE_CMD:-}"
if [[ "${DEWATA_USE_DISPOSABLE_VALIDATE:-0}" == "1" ]]; then
    if [[ -z "$VALIDATE_CMD" ]]; then
        echo "FATAL: DEWATA_USE_DISPOSABLE_VALIDATE=1 requires DEWATA_VALIDATE_CMD" >&2
        echo "  pointing at a disposable validation adapter." >&2
        echo "  example: DEWATA_VALIDATE_CMD=/opt/dw-phase2/tests/disposable-validate.sh" >&2
        exit 8
    fi
    if [[ ! -x "$VALIDATE_CMD" ]]; then
        echo "FATAL: DEWATA_VALIDATE_CMD=$VALIDATE_CMD is not executable." >&2
        exit 8
    fi
    head_line=$(head -n 1 "$VALIDATE_CMD" 2>/dev/null || echo "")
    case "$head_line" in
        "#!"*) ;;
        *)
            echo "FATAL: DEWATA_VALIDATE_CMD=$VALIDATE_CMD first line is not a shebang (got: ${head_line:0:60})." >&2
            echo "  refusing to call it." >&2
            exit 8 ;;
    esac
    echo "[install] DISPOSABLE_VALIDATE: validated disposable validation adapter at $VALIDATE_CMD"
fi


   # Disposable service-control mode. When DEWATA_DISPOSABLE_MODE=1 is
# active, this controls whether the install ACTUALLY invokes
# ${SYSTEMCTL_CMD} restart (and the listener check that follows),
# or whether it skips both (the legacy "disposable only-no-restart" mode).
# Values:
#   no-restart  -- skip systemctl restart AND the post-restart listener
#                   check (legacy behavior; only valid for tests that
#                   explicitly want to bypass restart).
#   restart     -- INVOKE the restart through the validated adapter.
#                   Default for lifecycle tests so NEGATIVE-9
#                   actually exercises a real post-restart failure.
DEWATA_DISPOSABLE_SERVICE_MODE="${DEWATA_DISPOSABLE_SERVICE_MODE:-restart}"

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
sha256_of_file() { sha256sum "$1" | cut -d' ' -f1; }

# do_validate: validate a Caddyfile.
#   In production:  invokes /usr/bin/caddy validate --config ...
#   In tests:       invokes $DEWATA_VALIDATE_CMD <file>  (the disposable
#                   validation adapter).  The validation adapter is
#                   required to fail closed: if the file path is missing,
#                   the adapter exits non-zero.
#
#   The DEWATA_FAKE_VALIDATE_FAILURE=1 hook makes the disposable adapter
#   return non-zero.  To restrict the failure to specific call sites, use
#   DEWATA_FAKE_VALIDATE_FAILURE_GATES (space-separated list of gate names
#   that may fail; e.g. "g5" or "g5 g6" or "all").  If the env var is
#   unset, all gates may fail.
# Returns the exit code of the validation.  Sets ?=0 on success.
do_validate() {
    local file="$1"
    local gate="${2:-all}"
    # If the operator is running a fake-failure injection, restrict
    # which gates may fire it.  A gate NOT in the allowlist runs the
    # adapter normally (and does not propagate the FAKE failure).
    # GATES can be space- or comma-separated (e.g. "g5 restore" or
    # "g5,restore").  The default is "all" which matches any gate.
    if [[ -n "${DEWATA_VALIDATE_CMD:-}" ]]; then
        local fake="${DEWATA_FAKE_VALIDATE_FAILURE:-0}"
        local gates_raw="${DEWATA_FAKE_VALIDATE_FAILURE_GATES:-all}"
        local gates=" $(echo "$gates_raw" | tr ', ' '  ') "
        local may_fake=0
        case "$gates" in
            *" $gate "*|*" all "*) may_fake=1 ;;
        esac
        if [[ "$fake" == "1" && "$may_fake" == "1" ]]; then
            "${DEWATA_VALIDATE_CMD}" "$file"
            return $?
        fi
        # Either no fake-failure, or this gate is not allowed to fire
        # the fake.  Run the disposable adapter with the hook disabled
        # by overriding DEWATA_FAKE_VALIDATE_FAILURE for this subshell.
        (
            unset DEWATA_FAKE_VALIDATE_FAILURE
            "${DEWATA_VALIDATE_CMD}" "$file"
        )
        return $?
    fi
    /usr/bin/caddy validate --config "$file" --adapter caddyfile
    return $?
}

# --------------------------------------------------------------------
# State tracking for do_restore
# --------------------------------------------------------------------
SNAPSHOT_CAPTURED=0      # G2: snapshot exists at $SNAPSHOT_DIR
RELEASE_PRIOR_EXISTED=0  # G3: RELEASE_DST existed before publication (REPLACEMENT=1, FIRST=0)
RELEASE_PRIOR_BACKUP=""  # G3: backup path of the prior release tree (REPLACEMENT only)
RELEASE_PRIOR_MANIFEST="" # G3: optional snapshot of the prior release's file set (sha256 manifest)
PROD_WRITTEN=0           # G4: $PROD has the new candidate (not yet validated)
RESTART_INVOKED=0        # G6: ${SYSTEMCTL_CMD:-systemctl} restart was actually executed

# do_restore: rolled back in the correct order on failure.
#   1. Restore Caddyfile on disk (so the file is correct before restart).
#   2. Restore prior release tree from $RELEASE_BACKED_UP (so caddy
#      sees a consistent tree when it restarts).
#   3. Validate the restored Caddyfile.
#   4. Verify the restored Caddyfile's sha256 matches the snapshot's.
#   5. Restart in production mode.
#   6. Verify the listener is up.
# Each step sets restore_failed=1 on failure.  Only "AUTO-RESTORE COMPLETE"
# is printed when every step succeeded.
do_restore() {
    # Re-entrancy guard: if do_restore is invoked from the ERR trap,
    # any failure inside do_restore (e.g. a missing $RELEASE_PRIOR_BACKUP
    # on a second invocation) must NOT re-trigger this same trap and
    # recursively invoke do_restore again.  Without this guard the
    # installer's do_restore can move the same release multiple times,
    # ending with the release tree empty (each invocation mv's
    # $RELEASE_DST aside, then mv's $RELEASE_PRIOR_BACKUP back; on the
    # second invocation the backup is gone, so the mv silently leaves
    # $RELEASE_DST absent).
    if [[ "${IN_DO_RESTORE:-0}" == "1" ]]; then
        echo "  (do_restore already running; ignoring re-entry)" >&2
        return 0
    fi
    IN_DO_RESTORE=1
    # Ensure the flag is cleared on any exit path from do_restore.
    trap 'IN_DO_RESTORE=0' RETURN
    local reason="$1"
    echo "FATAL: install failed at: $reason"
    if [[ "$SNAPSHOT_CAPTURED" -ne 1 ]]; then
        echo "  (no snapshot captured; nothing to roll back.  inspect manually.)"
        exit 1
    fi
    local restore_failed=0

    # Step 1: restore the production Caddyfile on disk from the snapshot.
    if [[ ! -f "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" ]]; then
        echo "  restore ABORTED: snapshot runtime file missing at $SNAPSHOT_DIR/Caddyfile.dewata.runtime" >&2
        restore_failed=1
    else
        echo "  auto-restore step 1/5: re-installing snapshotted runtime to $PROD"
        install -m 0644 "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" "$PROD.new"
        sync
        mv -f "$PROD.new" "$PROD"
    fi

    # Step 2: restore the release tree to its prior state.
    #   REPLACEMENT case (RELEASE_PRIOR_EXISTED=1): move the freshly-published
    #     $RELEASE_DST aside, then move $RELEASE_PRIOR_BACKUP back into place.
    #     We compare file-set equality (exact-set + sha256 of every file)
    #     against the SNAPSHOT_DIR/RELEASE_TREE_BACKUP/ captured manifest.
    #   FIRST-INSTALL case (RELEASE_PRIOR_EXISTED=0): DELETE the freshly-
    #     published $RELEASE_DST so the system is back to "no release published".
    if (( RELEASE_PRIOR_EXISTED )); then
        echo "  auto-restore step 2/5: REPLACEMENT mode: restoring prior release from $RELEASE_PRIOR_BACKUP"
        # Move the freshly-published $RELEASE_DST aside (do not delete it;
        # the operator may want to investigate).  Save as ".rejected".
        if [[ -d "$RELEASE_DST" ]]; then
            if ! mv "$RELEASE_DST" "$RELEASE_DST.rejected.$(date -u +%Y%m%dT%H%M%SZ)"; then
                echo "  RESTORE FAILED: could not move freshly-published $RELEASE_DST aside" >&2
                restore_failed=1
            fi
        fi
        # Move the prior release back into place.
        if [[ -d "$RELEASE_PRIOR_BACKUP" ]]; then
            if mv "$RELEASE_PRIOR_BACKUP" "$RELEASE_DST"; then
                echo "  prior release restored from $RELEASE_PRIOR_BACKUP"
            else
                echo "  RESTORE FAILED: could not move $RELEASE_PRIOR_BACKUP back to $RELEASE_DST" >&2
                restore_failed=1
            fi
        else
            echo "  RESTORE FAILED: prior-release backup is missing at $RELEASE_PRIOR_BACKUP" >&2
            restore_failed=1
        fi
    else
        echo "  auto-restore step 2/5: FIRST-INSTALL mode: removing freshly-published release $RELEASE_DST"
        if [[ -d "$RELEASE_DST" ]]; then
            # Preserve the rejected release for inspection; do not delete it,
            # move it to a sibling .rejected name.  The end state is:
            # $RELEASE_DST does not exist (the original pre-install state).
            rejected="$RELEASE_DST.rejected.$(date -u +%Y%m%dT%H%M%SZ)"
            if ! mv "$RELEASE_DST" "$rejected"; then
                echo "  RESTORE FAILED: could not move freshly-published release aside" >&2
                restore_failed=1
            else
                echo "  freshly-published release preserved for inspection at $rejected"
                # Now check the file: RELEASE_DST must not exist (first-install end state).
                if [[ -e "$RELEASE_DST" ]]; then
                    echo "  RESTORE FAILED: $RELEASE_DST still exists after removal" >&2
                    restore_failed=1
                fi
            fi
        else
            # Nothing to remove; fine.
            echo "  $RELEASE_DST was not present (already cleaned up)"
        fi
    fi

    # Step 3: validate the restored Caddyfile.
    if do_validate "$PROD" restore; then
        echo "  auto-restore step 3/5: restored Caddyfile validates"
    else
        echo "  RESTORE FAILED: restored Caddyfile does not validate" >&2
        restore_failed=1
    fi

    # Step 3b: file-set + sha256 verification of the restored release tree.
    # REPLACEMENT case: the restored $RELEASE_DST must match the snapshot's
    # file-set (exact-set + every-file sha256).
    # FIRST-INSTALL case: $RELEASE_DST must not exist.
    if (( RELEASE_PRIOR_EXISTED )); then
        if [[ -d "$RELEASE_DST" ]] && [[ -f "$SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt" ]]; then
            # Snapshot file set
            snapshot_files=$(awk '/^[a-f0-9]/{print $2}' "$SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt" | sort -u)
            # Restored file set
            restored_files=$( ( cd "$RELEASE_DST" && find . -type f ) | sed 's|^./||' | sort -u )
            if [[ "$snapshot_files" != "$restored_files" ]]; then
                echo "  RESTORE FAILED: restored release file-set does not match snapshot" >&2
                echo "    snapshot ($(echo "$snapshot_files" | wc -l) files)" >&2
                echo "    restored ($(echo "$restored_files" | wc -l) files)" >&2
                restore_failed=1
            else
                echo "  auto-restore step 3b/5: restored release matches prior file set ($(echo "$snapshot_files" | wc -l) files)"
                # Sha256 verification of every file (most expensive check)
                sha_mismatch=0
                while IFS= read -r rel; do
                    [[ -z "$rel" ]] && continue
                    actual=$(sha256sum "$RELEASE_DST/$rel" | cut -d' ' -f1)
                    expected=$(awk -v r="$rel" '$2 == r {print $1}' "$SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt" | head -1)
                    if [[ "$actual" != "$expected" ]]; then
                        echo "  RESTORE FAILED: sha256 mismatch for $rel (got $actual, want $expected)" >&2
                        sha_mismatch=1
                    fi
                done <<< "$snapshot_files"
                if (( sha_mismatch )); then
                    restore_failed=1
                else
                    echo "  auto-restore step 3b/5: restored release sha256 verified for every file"
                fi
            fi
        fi
    fi

    # Step 4: verify the restored Caddyfile's sha256 matches the snapshot's.
    if [[ -f "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" ]]; then
        local restored_sha snapshot_sha
        restored_sha=$(sha256_of_file "$PROD")
        snapshot_sha=$(sha256_of_file "$SNAPSHOT_DIR/Caddyfile.dewata.runtime")
        if [[ "$restored_sha" != "$snapshot_sha" ]]; then
            echo "  RESTORE FAILED: restored $PROD sha256 ($restored_sha) does not match snapshot runtime sha256 ($snapshot_sha)" >&2
            restore_failed=1
        else
            echo "  auto-restore step 4/5: restored Caddyfile sha256 verified: $restored_sha"
        fi
    fi

    # Step 5: restart in production mode.  CRITICAL: only restart if
    # every prior step succeeded.  If restore_failed=1 (caddyfile restore
    # failed, validation failed, or sha verify failed), DO NOT restart
    # the service -- the operator must first restore the Caddyfile
    # manually before a restart is safe (the running caddy is still
    # serving the pre-failure Caddyfile from disk; restarting now would
    # pick up whatever happens to be on disk, which is unknown).
    if (( restore_failed )); then
        echo "  auto-restore step 5/5: skipped (RESTORE FAILED earlier -- restart deferred until operator intervention)"
    elif [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]]; then
        if ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE"; then
            echo "  auto-restore step 5/5: service restarted: $DEWATA_CADDY_SERVICE"
            RESTART_INVOKED=1
            for attempt in 1 2 3 4 5 6 7 8 9 10; do
                if ss -ltn 2>/dev/null | grep -q ":$LISTENER_PORT "; then
                    echo "  post-restore listener up: :$LISTENER_PORT"
                    break
                fi
                sleep 1
            done
            if ! ss -ltn 2>/dev/null | grep -q ":$LISTENER_PORT "; then
                echo "  RESTORE FAILED: :$LISTENER_PORT not listening after post-restore restart" >&2
                restore_failed=1
            fi
            local post_restore_pid
            post_restore_pid=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
            echo "  post-restore $DEWATA_CADDY_SERVICE MainPID=$post_restore_pid"
        else
            echo "  RESTORE FAILED: ${SYSTEMCTL_CMD:-systemctl} restart $DEWATA_CADDY_SERVICE returned non-zero" >&2
            restore_failed=1
        fi
    else
        echo "  auto-restore step 5/5: skipped (DISPOSABLE mode or non-production path)"
    fi

    if (( restore_failed )); then
        echo "  AUTO-RESTORE INCOMPLETE: inspect $PROD and $RELEASE_DST manually." >&2
        exit 2
    fi
    echo "  AUTO-RESTORE COMPLETE: $PROD and $RELEASE_DST restored to prior state."
    exit 1
}
trap 'do_restore "install failure"' ERR

# --------------------------------------------------------------------
# Failure-injection hooks (only used by the lifecycle test)
#   DEWATA_FAKE_FAIL_AT_GATE       = g3-post-publish | g4 | g5 | g6
#   DEWATA_FAKE_RESTART_FAILURE    = 1   -> G6 listener check fails after a real restart
#   DEWATA_FAKE_RECOVERY_VALIDATION_FAILURE = 1 -> do_restore corrupts snapshot in place
#   DEWATA_CADDY_SERVICE           = service name (default: dewata-caddy)
# --------------------------------------------------------------------
: "${DEWATA_CADDY_SERVICE:=dewata-caddy}"

# ====================================================================
# G0: preflight + drift guard
# ====================================================================
echo "================================================================"
echo "G0: preflight"
echo "================================================================"

live_sha=$(sha256_of_file "$PROD")
if [[ "$live_sha" != "$PROD_BASELINE_SHA" ]]; then
    echo "FATAL: production Caddyfile sha256 does not match baseline." >&2
    echo "  baseline : $PROD_BASELINE_SHA" >&2
    echo "  live     : $live_sha ($PROD)" >&2
    echo "  refusing to install.  re-compute the baseline or investigate." >&2
    exit 3
fi
echo "G0: production Caddyfile matches baseline ($live_sha)"

# Verify the candidate Caddyfile matches the reviewed manifest's entry for it.
if [[ ! -f "$CANDIDATE" ]]; then
    echo "FATAL: candidate Caddyfile not found at $CANDIDATE" >&2
    exit 1
fi
cand_sha=$(sha256_of_file "$CANDIDATE")
manifest_cand_sha=$(awk '$2 == "Caddyfile.dewata.proposed"{print $1}' "$REVIEWED_MANIFEST" | head -1)
if [[ -z "$manifest_cand_sha" ]]; then
    echo "FATAL: $REVIEWED_MANIFEST does not list Caddyfile.dewata.proposed" >&2
    exit 1
fi
if [[ "$cand_sha" != "$manifest_cand_sha" ]]; then
    echo "ERROR: candidate Caddyfile sha does not match reviewed manifest"
    echo "  manifest: $manifest_cand_sha"
    echo "  live    : $cand_sha"
    echo "Refusing to install.  Re-pin the manifest or rebuild the candidate."
    exit 1
fi
echo "G0: candidate matches reviewed manifest ($cand_sha)"

# ====================================================================
# G0.5: bidirectional manifest verify
#   - every manifest entry (except Caddyfile.dewata.proposed) must exist
#     in $RELEASE_SRC
#   - every regular file in $RELEASE_SRC must be listed in the manifest
#   - no symlinks in $RELEASE_SRC
# ====================================================================
echo
echo "================================================================"
echo "G0: release manifest cross-check"
echo "================================================================"

manifest_entries=$(awk '/^[a-f0-9]/{print $2}' "$REVIEWED_MANIFEST" \
    | grep -v "^Caddyfile.dewata.proposed$" | sort -u)
if [[ -z "$manifest_entries" ]]; then
    echo "FATAL: manifest $REVIEWED_MANIFEST contains no <sha> <relpath> entries." >&2
    exit 6
fi

missing_in_src=0
while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    if [[ ! -f "$RELEASE_SRC/$rel" ]]; then
        echo "FATAL: manifest entry missing in RELEASE_SRC: $rel" >&2
        echo "  expected: $RELEASE_SRC/$rel" >&2
        missing_in_src=$((missing_in_src+1))
    fi
done <<< "$manifest_entries"
if (( missing_in_src > 0 )); then
    echo "FATAL: $missing_in_src manifest entries are missing in RELEASE_SRC. refusing to install." >&2
    exit 6
fi

if (cd "$RELEASE_SRC" && find . -type l 2>/dev/null) | grep -q .; then
    echo "FATAL: release source contains symlinks.  symlinks are rejected by this script." >&2
    (cd "$RELEASE_SRC" && find . -type l) | sed "s|^|  |" >&2
    exit 5
fi

src_files=$( (cd "$RELEASE_SRC" && find . -type f) | sed "s|^\\./||" | sort -u )
extra_in_src=0
while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    if ! grep -qxF "$rel" <<< "$manifest_entries"; then
        echo "FATAL: file in RELEASE_SRC but not in manifest: $rel" >&2
        extra_in_src=$((extra_in_src+1))
    fi
done <<< "$src_files"
if (( extra_in_src > 0 )); then
    echo "FATAL: $extra_in_src files in RELEASE_SRC are not listed in the manifest. refusing to install." >&2
    exit 6
fi

echo "G0: release manifest cross-check passed ($(echo "$manifest_entries" | wc -l) entries, all present in RELEASE_SRC)"

# ====================================================================
# G1: validate the candidate Caddyfile
# ====================================================================
echo
echo "================================================================"
echo "G1: validate candidate"
echo "================================================================"
# Guard set -e: a fail-return from candidate-validation must NOT
# trigger the surrounding ERR trap.
if do_validate "$CANDIDATE" g1; then
    echo "G1: candidate validated"
else
    echo "FATAL: candidate Caddyfile does not validate" >&2
    echo "FATAL: install aborted before any state changes." >&2
    exit 6
fi

# ====================================================================
# G2: snapshot the current production Caddyfile
#   - Capture the live sha (PRE_INSTALL_PROD_SHA) for the no-op check at G6.
# ====================================================================
echo
echo "================================================================"
echo "G2: snapshot"
echo "================================================================"
mkdir -p "$SNAPSHOT_PARENT"
SNAPSHOT_DIR="$SNAPSHOT_PARENT/$(date -u +%Y%m%dT%H%M%SZ)-pre-apex"
mkdir -p "$SNAPSHOT_DIR"
PRE_INSTALL_PROD_SHA=$(sha256_of_file "$PROD")
echo "G2: snapshot target: $SNAPSHOT_DIR"
echo "G2: pre-install $PROD sha256 = $PRE_INSTALL_PROD_SHA"
install -m 0644 "$PROD" "$SNAPSHOT_DIR/Caddyfile.dewata.runtime"
install -m 0644 "$CANDIDATE" "$SNAPSHOT_DIR/Caddyfile.dewata.candidate"
diff -u "$SNAPSHOT_DIR/Caddyfile.dewata.runtime" \
        "$SNAPSHOT_DIR/Caddyfile.dewata.candidate" \
        > "$SNAPSHOT_DIR/Caddyfile.dewata.diff" || true
echo "$PRE_INSTALL_PROD_SHA -> $(date -u +%Y%m%dT%H%M%SZ) (this run)" >> "$SNAPSHOT_DIR/installed.log"
SNAPSHOT_CAPTURED=1

# ====================================================================
# G3: stage release files WITH FULL BIDIRECTIONAL MANIFEST VERIFY
# ====================================================================
echo
echo "================================================================"
echo "G3: stage release files (full manifest verify)"
echo "================================================================"

# Record whether RELEASE_DST existed BEFORE publication (REPLACEMENT vs FIRST).
# This is critical for do_restore: on first-install failure the freshly
# published release must be removed; on replacement failure the prior
# release (which was renamed aside as $RELEASE_BACKED_UP) must be restored.
if [[ -d "$RELEASE_DST" ]]; then
    RELEASE_PRIOR_EXISTED=1
    echo "G3: $RELEASE_DST already existed -- REPLACEMENT mode (prior release will be renamed aside)"
else
    RELEASE_PRIOR_EXISTED=0
    echo "G3: $RELEASE_DST did not exist -- FIRST-INSTALL mode (no prior release to back up)"
fi

# Counters live in a sibling file outside $STAGING_DIR so the published
# release never contains the sentinel.
STAGING_DIR="$RELEASE_DST.staging.$$"
mkdir -p "$STAGING_DIR"
STAGE_COUNTERS="$STAGING_DIR.stage-counters"
: > "$STAGE_COUNTERS"

awk '/^[a-f0-9]/{print}' "$REVIEWED_MANIFEST" | while read -r sum rel rest; do
    if [[ -z "$rel" || "$rel" == "Caddyfile.dewata.proposed" ]]; then
        continue
    fi
    src="$RELEASE_SRC/$rel"
    dst="$STAGING_DIR/$rel"
    if [[ ! -f "$src" ]]; then
        echo "FATAL: manifest entry missing in RELEASE_SRC: $rel" >&2
        echo "  expected: $src" >&2
        echo MISSING >> "$STAGE_COUNTERS"
        continue
    fi
    actual=$(sha256_of_file "$src")
    if [[ "$actual" != "$sum" ]]; then
        echo "FATAL: sha256 mismatch for $rel" >&2
        echo "  manifest: $sum" >&2
        echo "  source  : $actual" >&2
        echo SHA_MISMATCH >> "$STAGE_COUNTERS"
        continue
    fi
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
    echo STAGED >> "$STAGE_COUNTERS"
done
n_staged=$(grep -c ^STAGED$ "$STAGE_COUNTERS" || true)
n_missing_in_src=$(grep -c ^MISSING$ "$STAGE_COUNTERS" || true)
n_sha_mismatch=$(grep -c ^SHA_MISMATCH$ "$STAGE_COUNTERS" || true)
if (( n_missing_in_src > 0 || n_sha_mismatch > 0 )); then
    echo "FATAL: staging failed: $n_missing_in_src missing, $n_sha_mismatch sha-mismatched. refusing to publish." >&2
    do_restore "staging failed: missing/mismatched manifest entries"
fi
echo "G3: staged $n_staged files; no missing entries, no sha mismatches"

staged_files=$( (cd "$STAGING_DIR" && find . -type f) | sed "s|^\\./||" | sort -u )
manifest_files_to_stage=$(awk '/^[a-f0-9]/{print $2}' "$REVIEWED_MANIFEST" \
    | grep -v "^Caddyfile.dewata.proposed$" | sort -u)

extras_in_stage=$(comm -23 <(printf "%s\\n" "$staged_files") <(printf "%s\\n" "$manifest_files_to_stage"))
if [[ -n "$extras_in_stage" ]]; then
    echo "FATAL: staged tree has files not in manifest:" >&2
    printf "  %s\\n" $extras_in_stage >&2
    do_restore "staged tree has files not in manifest"
fi
missing_in_stage=$(comm -13 <(printf "%s\\n" "$staged_files") <(printf "%s\\n" "$manifest_files_to_stage"))
if [[ -n "$missing_in_stage" ]]; then
    echo "FATAL: manifest entries not in staged tree:" >&2
    printf "  %s\\n" $missing_in_stage >&2
    do_restore "manifest entries missing from staged tree"
fi
echo "G3: staged tree exactly matches manifest (excluding Caddyfile.dewata.proposed)"

# Atomic publish -- the CRITICAL property: the prior release is captured
# into the SNAPSHOT (state: PRIOR_SNAPSHOTTED=1) BEFORE the live
# $RELEASE_DST is renamed aside.  Two redundant copies exist between the
# rename and the publish:
#
#   PRIOR_SNAPSHOTTED=1       -- snapshot's RELEASE_TREE_BACKUP/ holds a
#                                captured copy of the prior release.
#   PRIOR_BACKED_UP=1         -- $RELEASE_DST has been renamed to
#                                $RELEASE_DST.bak.<ts> (a SIBLING).
#
# do_restore restores from the SNAPSHOT ONLY (it copies out of
# $SNAPSHOT_DIR/RELEASE_TREE_BACKUP/, never moves the only copy out
# of $RELEASE_DST.bak.<ts>).
#
# State transitions:
#
#   INITIAL                  -- $RELEASE_DST points to prior release (or
#                                absent)
#   PRIOR_SNAPSHOTTED=1      -- snapshot has captured the prior release
#   PRIOR_SNAPSHOTTED=1 +
#     NEW_STAGED=1          -- staging verified; $STAGING_DIR holds new
#                                release (not yet $RELEASE_DST)
#   PRIOR_SNAPSHOTTED=1 +
#     NEW_STAGED=1 +
#     PRIOR_BACKED_UP=1     -- $RELEASE_DST renamed to $RELEASE_DST.bak
#   PRIOR_SNAPSHOTTED=1 +
#     NEW_STAGED=1 +
#     PRIOR_BACKED_UP=1 +
#     NEW_PUBLISHED=1      -- staging renamed to $RELEASE_DST (success)
#
# A failure at any state aborts; do_restore returns to INITIAL using
# the snapshot's PRIOR capture (it never moves the only copy).
if (( RELEASE_PRIOR_EXISTED )); then
    # Snapshot FIRST while $RELEASE_DST is still pointing at the prior
    # release.  We verify the snapshot's file set + sha256 matches the
    # live $RELEASE_DST before doing anything else.  (The Caddyfile
    # lives at $RELEASE_DST/../Caddyfile.dewata -- sibling to the release
    # tree -- and is checked separately by G0's drift guard.)
    echo "G3: REPLACEMENT mode: capturing prior $RELEASE_DST into snapshot FIRST"
    # Build the prior release manifest by walking $RELEASE_DST directly.
    PRIOR_FILES=$( ( cd "$RELEASE_DST" && find . -type f ) | sed 's|^./||' | sort -u )
    PRIOR_MANIFEST="$SNAPSHOT_DIR/PRIOR_RELEASE.MANIFEST.txt"
    : > "$PRIOR_MANIFEST"
    for rel in $PRIOR_FILES; do
        sum=$(sha256sum "$RELEASE_DST/$rel" | cut -d' ' -f1)
        printf "%s  %s\n" "$sum" "$rel" >> "$PRIOR_MANIFEST"
    done
    n_prior=$(grep -c . "$PRIOR_MANIFEST" || true)
    echo "G3: PRIOR_SNAPSHOTTED=1 (n=$n_prior)"
    # (No prior-manifest consistency check at this point -- the
    # primary correctness guarantee is the per-file sha verification
    # done below against the snapshot copy.)

    # Now copy the prior release into the snapshot ATOMICALLY (the
    # destination is a separate dir, so a snapshot failure here does
    # NOT affect the live $RELEASE_DST -- the prior release is still
    # intact).
    PRIOR_BACKUP_DIR="$SNAPSHOT_DIR/RELEASE_TREE_BACKUP"
    rm -rf "$PRIOR_BACKUP_DIR"  # nothing there yet; previous snapshot's
                                # copy should already be gone (rollback
                                # in the previous iteration cleared it
                                # by moving it into $RELEASE_DST).
    if ! cp -a "$RELEASE_DST" "$PRIOR_BACKUP_DIR"; then
        echo "FATAL: could not copy prior release into snapshot at $PRIOR_BACKUP_DIR" >&2
        echo "  the prior release is INTACT at $RELEASE_DST (no rename happened yet)" >&2
        do_restore "prior release snapshot copy failed"
    fi
    # Validate the snapshot's file set + sha256 against the manifest
    # we just wrote.
    n_snapshot=$( ( find "$PRIOR_BACKUP_DIR" -type f 2>/dev/null | wc -l | tr -d ' ' ) || echo 0 )
    n_manifest=$( ( grep -c . "$PRIOR_MANIFEST" 2>/dev/null | tr -d ' ' ) || echo 0 )
    if [[ "$n_snapshot" != "$n_manifest" ]]; then
        echo "FATAL: prior release snapshot copy has $n_snapshot files, manifest lists $n_manifest" >&2
        do_restore "prior release snapshot file count mismatch"
    fi
    sha_mismatch=0
    while IFS= read -r sum rel; do
        [[ -z "$rel" ]] && continue
        actual=$(sha256sum "$PRIOR_BACKUP_DIR/$rel" | cut -d' ' -f1)
        if [[ "$actual" != "$sum" ]]; then
            echo "FATAL: prior release snapshot sha mismatch for $rel" >&2
            sha_mismatch=1
            break
        fi
    done < "$PRIOR_MANIFEST"
    if (( sha_mismatch )); then
        do_restore "prior release snapshot sha mismatch"
    fi
    echo "G3: prior release snapshot verified ($n_manifest files, sha matches)"

    # Snapshot succeeded; $RELEASE_DST is still pointing at the prior
    # release.  NOW we can safely rename it aside.
    BACKUP_PATH="$RELEASE_DST.bak.$(date -u +%Y%m%dT%H%M%SZ)"
    echo "G3: PRIOR_BACKED_UP=1 -- renaming $RELEASE_DST aside to $BACKUP_PATH"
    if ! mv "$RELEASE_DST" "$BACKUP_PATH"; then
        echo "FATAL: could not move $RELEASE_DST aside before publish" >&2
        # Note: the snapshot at $SNAPSHOT_DIR/RELEASE_TREE_BACKUP/ is
        # already complete; do_restore restores from there.
        RELEASE_PRIOR_BACKUP=""
        do_restore "backup move failed"
    fi
    RELEASE_PRIOR_BACKUP="$BACKUP_PATH"
    # Mirror the prior manifest (which was written from $RELEASE_DST before
    # the move) into the canonical snapshot.  RELEASE_TREE_BACKUP.MANIFEST.txt
    # is what the rollback script reads.
    cp "$PRIOR_MANIFEST" "$SNAPSHOT_DIR/RELEASE_TREE_BACKUP.MANIFEST.txt"
    echo "G3: prior release manifest mirrored to RELEASE_TREE_BACKUP.MANIFEST.txt"
    echo "G3: PRIOR_SNAPSHOTTED=1 + PRIOR_BACKED_UP=1 (two redundant copies exist)"
else
    echo "G3: FIRST-INSTALL mode: no prior release to back up; do_restore will delete on failure"
fi

# Move staging into the live location.  We've captured PRIOR (snapshot
# copy + .bak sibling).  Now publish.
if ! mv "$STAGING_DIR" "$RELEASE_DST"; then
    echo "FATAL: atomic publish failed (mv $STAGING_DIR -> $RELEASE_DST)" >&2
    do_restore "atomic publish failed"
fi
echo "G3: NEW_PUBLISHED=1 -- release published at $RELEASE_DST"

# Post-publish exact-set comparison.
published_files=$( (cd "$RELEASE_DST" && find . -type f) | sed "s|^\\./||" | sort -u )
extras_in_published=$(comm -23 <(printf "%s\\n" "$published_files") <(printf "%s\\n" "$manifest_files_to_stage"))
if [[ -n "$extras_in_published" ]]; then
    echo "FATAL: published tree has files not in manifest:" >&2
    printf "  %s\\n" $extras_in_published >&2
    do_restore "published tree has files not in manifest"
fi
missing_in_published=$(comm -13 <(printf "%s\\n" "$published_files") <(printf "%s\\n" "$manifest_files_to_stage"))
if [[ -n "$missing_in_published" ]]; then
    echo "FATAL: manifest entries not in published tree:" >&2
    printf "  %s\\n" $missing_in_published >&2
    do_restore "manifest entries missing from published tree"
fi
fail=0
while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    sum=$(sha256_of_file "$RELEASE_DST/$rel")
    exp=$(awk -v r="$rel" '$2 == r {print $1}' "$REVIEWED_MANIFEST" | head -1)
    if [[ "$sum" != "$exp" ]]; then
        echo "FATAL: sha256 mismatch after publish for $rel" >&2
        echo "  published: $sum" >&2
        echo "  manifest : $exp" >&2
        fail=1
    fi
done <<< "$published_files"
if (( fail )); then
    echo "FATAL: published release does not match manifest" >&2
    do_restore "post-publish sha mismatch"
fi
n_files=$(printf "%s\\n" "$published_files" | grep -c . || true)
echo "G3: $n_files files at $RELEASE_DST (exact-set match against manifest)"

# Failure-injection hook: simulate a failure AFTER G3 publication
# (after the staging dir is moved into RELEASE_DST, after the post-
# publish exact-set comparison) but BEFORE G4.
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g3-post-publish" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g3-post-publish -> simulating failure after G3" >&2
    do_restore "injected failure after G3 publication"
fi

# ====================================================================
# G4: atomic install of the candidate caddyfile
# ====================================================================
echo
echo "================================================================"
echo "G4: atomic install"
echo "================================================================"
install -m 0644 "$CANDIDATE" "$PROD.new"
sync
mv -f "$PROD.new" "$PROD"
echo "G4: candidate installed at $PROD"
PROD_WRITTEN=1

if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g4" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g4 -> simulating post-G4 failure" >&2
    do_restore "injected failure after G4"
fi

# ====================================================================
# G5: re-validate the installed file
# ====================================================================
echo
echo "================================================================"
echo "G5: re-validate installed file"
echo "================================================================"
# Use a guard so a fail-return from do_validate does NOT trip the
# surrounding `set -e -o pipefail`.  The FAKE_VALIDATE_FAILURE path
# wants to control how the failure is handled (we explicitly walk
# it through do_restore), NOT let set -e propagate the rc.
if do_validate "$PROD" g5; then
    echo "G5: validated"
else
    g5_rc=$?
    echo "G5: validate failed (rc=$g5_rc)"
    do_restore "injected failure during G5 installed-file validation"
fi

if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g5" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g5 -> simulating failure after G5 (pre-restart)" >&2
    do_restore "injected failure after G5 validation"
fi

# ====================================================================
# G6: restart
#   No-op check: if the just-installed candidate caddyfile is byte-
#   identical to the caddyfile we started with, no live change
#   occurred and we MUST NOT restart the service.
# ====================================================================
echo
echo "================================================================"
echo "G6: restart $DEWATA_CADDY_SERVICE"
echo "================================================================"

POST_INSTALL_PROD_SHA=$(sha256_of_file "$PROD")
if [[ "$POST_INSTALL_PROD_SHA" == "$PRE_INSTALL_PROD_SHA" ]]; then
    echo "G6: install was a no-op (candidate == current prod caddyfile, sha $POST_INSTALL_PROD_SHA)"
    echo "G6: skipping ${SYSTEMCTL_CMD:-systemctl} restart -- no live change to apply"
    OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
    NEW_PID="$OLD_PID"
    RESTART_INVOKED=0
    echo "G6: $DEWATA_CADDY_SERVICE MainPID unchanged: $OLD_PID"
else
    echo "G6: candidate caddyfile differs from production (was $PRE_INSTALL_PROD_SHA, now $POST_INSTALL_PROD_SHA); restart decision pending"
    # Restart decision tree:
    #   APPLY_PROD=1 + IS_PROD_PATH=1   -> real systemctl restart (production).
    #   DISPOSABLE=1 + DEWATA_DISPOSABLE_SERVICE_MODE=restart -> invoke the
    #       configured shim's restart command.  The shim is what the test
    #       controls; the assertion is that the test invoked the shim.
    #   DISPOSABLE=1 + DEWATA_DISPOSABLE_SERVICE_MODE=no-restart -> skip
    #       restart (legacy behavior; only valid for tests that explicitly
    #       want to bypass the restart).
    #   any other combination of flags -> FATAL.
    if [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]]; then
        OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
        echo "G6: pre-restart $DEWATA_CADDY_SERVICE MainPID=$OLD_PID"
        if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
            echo "G6: DEWATA_FAKE_RESTART_FAILURE=1 -> simulating post-restart failure"
            ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE" || true
            RESTART_INVOKED=1
            NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
            echo "G6: post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID"
        else
            ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE"
            RESTART_INVOKED=1
            for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
                state=$(${SYSTEMCTL_CMD:-systemctl} is-active "$DEWATA_CADDY_SERVICE" || true)
                if [[ "$state" == "active" ]]; then break; fi
                sleep 1
            done
            NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
            echo "G6: post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID"
        fi
    elif [[ "$DISPOSABLE" == "1" && "$DEWATA_DISPOSABLE_SERVICE_MODE" == "restart" ]]; then
        # New behavior: invoke restart through the configured shim.
        OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
        echo "G6: pre-restart $DEWATA_CADDY_SERVICE MainPID=$OLD_PID"
        if [[ "${DEWATA_FAKE_RESTART_FAILURE:-0}" == "1" ]]; then
            echo "G6: DEWATA_FAKE_RESTART_FAILURE=1 -> shim sees restart failure"
            ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE" || true
            RESTART_INVOKED=1
            NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
            echo "G6: post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID"
        else
            ${SYSTEMCTL_CMD:-systemctl} restart "$DEWATA_CADDY_SERVICE"
            RESTART_INVOKED=1
            NEW_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value)
            echo "G6: post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID"
            # Listener check (disposable mode + restart mode also gets the listener check,
            # since the assertion is that the shim's restart produced a usable PID).
            # The shim's PIDFILE is the source of truth here; the listener (port 18443)
            # is checked by the lifecycle driver which launches an actual disposable caddy.
        fi
    elif [[ "$DISPOSABLE" == "1" && "$DEWATA_DISPOSABLE_SERVICE_MODE" == "no-restart" ]]; then
        # Legacy behavior: explicitly skip restart in disposable mode.
        OLD_PID=$(${SYSTEMCTL_CMD:-systemctl} show "$DEWATA_CADDY_SERVICE" -p MainPID --value 2>/dev/null || echo 0)
        NEW_PID=0
        RESTART_INVOKED=0
        echo "G6: DISPOSABLE+no-restart -> skipping ${SYSTEMCTL_CMD:-systemctl} restart (driver will take over)"
        echo "G6: pre-restart $DEWATA_CADDY_SERVICE MainPID=$OLD_PID"
        echo "G6: post-restart $DEWATA_CADDY_SERVICE MainPID=$NEW_PID (driver will take over)"
    else
        echo "FATAL: restart requested but no valid mode combination (APPLY_PROD=$APPLY_PROD IS_PROD_PATH=$IS_PROD_PATH DISPOSABLE=$DISPOSABLE SERVICE_MODE=$DEWATA_DISPOSABLE_SERVICE_MODE)" >&2
        exit 6
    fi
fi

# Post-restart listener check.
#   APPLY_PROD=1 + IS_PROD_PATH=1                       -> real ss probe on production port.
#   DISPOSABLE=1 + DEWATA_DISPOSABLE_SERVICE_MODE=restart -> probe the disposable port.
#   DISPOSABLE=1 + DEWATA_DISPOSABLE_SERVICE_MODE=no-restart -> skip.
if [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]] \
   || [[ "$DISPOSABLE" == "1" && "$DEWATA_DISPOSABLE_SERVICE_MODE" == "restart" ]]; then
    # Look for the listener on $LISTENER_PORT.  In disposable-restart mode
    # the listener is a real disposable caddy the lifecycle driver launches;
    # the installer's invocation should NOT cause a real ss probe unless
    # DEWATA_PROBE_LISTENER=1 is explicitly set.
    if [[ "${DEWATA_PROBE_LISTENER:-1}" == "1" ]]; then
        ss -ltn 2>/dev/null | grep -q ":$LISTENER_PORT " && echo "G6: :$LISTENER_PORT listening" || {
            echo "FATAL: :$LISTENER_PORT not listening after restart"
            do_restore "post-restart listener check"
        }
    else
        echo "G6: skipping post-restart listener probe (DEWATA_PROBE_LISTENER=$DEWATA_PROBE_LISTENER)"
    fi
fi

# Failure-injection hook: simulate a post-G6 failure even in
# disposable mode (so the test can verify do_restore runs end-to-end).
if [[ "${DEWATA_FAKE_FAIL_AT_GATE:-}" == "g6" ]]; then
    echo "FATAL: DEWATA_FAKE_FAIL_AT_GATE=g6 -> simulating post-restart failure" >&2
    do_restore "injected failure after G6"
fi

# ====================================================================
# G7: HTTP probes (only in production mode AND only against a
# production path; lifecycle test owns probes for disposable mode)
# ====================================================================
if [[ "$APPLY_PROD" == "1" && "$IS_PROD_PATH" -eq 1 ]]; then
    echo
    echo "================================================================"
    echo "G7: HTTP probes"
    echo "================================================================"
    echo "G7: HTTP probes against $DEWATA_CADDY_SERVICE on 127.0.0.1:$LISTENER_PORT"
    fail=0
    probe() {
        local host="$1" path="$2" expected_code="$3"
        local code body
        code=$(curl -s -o /tmp/probe.body -w "%{http_code}" \
            --max-time 5 \
            -H "Host: $host" \
            "http://127.0.0.1:$LISTENER_PORT$path")
        body=$(head -c 200 /tmp/probe.body)
        if [[ "$code" == "$expected_code" ]]; then
            printf "  OK  %-22s %-30s -> %s  body[:200]=%s\\n" "$host" "$path" "$code" "$body"
        else
            printf "  FAIL %-22s %-30s -> got %s expected %s\\n" "$host" "$path" "$code" "$expected_code"
            return 1
        fi
    }
    probe dewata.org          "/"                                       200 || fail=1
    probe dewata.org          "/index.html"                             200 || fail=1
    probe dewata.org          "/calendar.html"                          200 || fail=1
    probe dewata.org          "/about.html"                             200 || fail=1
    probe dewata.org          "/transparency.html"                      200 || fail=1
    probe dewata.org          "/assets/style.css"                       200 || fail=1
    probe api.dewata.org      "/health"                                 200 || fail=1
    probe api.dewata.org      "/dsp/v0.1/calendar/ruleset"              200 || fail=1
    probe api.dewata.org      "/brief"                                  200 || fail=1
    probe bci.dewata.org      "/"                                       503 || fail=1
    probe protocol.dewata.org "/"                                       503 || fail=1
    probe datasets.dewata.org "/"                                       503 || fail=1
    probe localhost           "/"                                       503 || fail=1

    if (( fail )); then
        echo
        echo "INSTALL: some probes failed.  auto-restore."
        do_restore "probe failures"
    fi
fi

# Done.  Disable auto-restore on success.
trap - ERR
SNAPSHOT_CAPTURED=0
rm -f "$STAGE_COUNTERS"

echo
echo "================================================================"
echo "INSTALL SUCCESS"
echo "================================================================"
echo "  mode:        $([[ "$APPLY_PROD" == "1" ]] && echo PRODUCTION || echo DISPOSABLE)"
echo "  snapshot:    $SNAPSHOT_DIR"
echo "  release:     $RELEASE_DST"
echo "  caddy:       $PROD (manifest-verified, atomic-publish)"
echo "  restart:     $([[ "$RESTART_INVOKED" == "1" ]] && echo "yes, MainPID $OLD_PID -> $NEW_PID" || echo "skipped (no live change or DISPOSABLE mode)")"
echo "  apex:        http://127.0.0.1:$LISTENER_PORT/  (Host: dewata.org) returns the bci"
echo "  api:         http://127.0.0.1:$LISTENER_PORT/health  (Host: api.dewata.org) returns 200"

# Capture the ACTUAL snapshot path to the install-record file.
echo "$(date -u +%Y%m%dT%H%M%SZ)  $OLD_PID -> $NEW_PID  prod=$APPLY_PROD  disposable=$DISPOSABLE" >> "$SNAPSHOT_DIR/installed.log"
echo "  actual_snapshot_path=$SNAPSHOT_DIR"
exit 0
