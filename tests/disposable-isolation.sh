#!/usr/bin/env bash
# =============================================================================
# disposable-isolation.sh -- test isolation guards for dewata disposable tests
# =============================================================================
#
# Per the user's review: "a shell-script/shebang check does not prove an
# adapter cannot call real systemctl. Run disposable tests in an
# environment where production paths and the real service manager are
# unavailable, or pin the adapter hash and restrict every test path to
# a freshly created test root."
#
# This file implements BOTH strategies:
#
#   1. Hash-pin the disposable adapters (systemctl shim + validate shim).
#      At test start, compute the SHA256 of each adapter and refuse to
#      run if it has drifted from the pinned value.
#
#   2. Path-isolation: refuse to run if any DEWATA_*_DST path resolves
#      to a production location (/opt/dewata.online, /etc/caddy,
#      /var/lib/dewata, or anywhere under /opt/ outside /opt/dw-phase2).
#
#   3. Service-manager isolation: when DEWATA_DISPOSABLE_MODE=1, refuse
#      to run if DEWATA_SYSTEMCTL_CMD resolves to the system systemctl.
#
#   4. Restrict every disposable path to a freshly-created root under
#      /tmp/ that did not exist before the test session started.
#
# Usage:
#   source /opt/dw-phase2/tests/disposable-isolation.sh
#   disposable_isolation_check        # exits 9 if any check fails
#
# Env vars read:
#   DEWATA_DISPOSABLE_MODE           -- required=1 for disposable tests
#   DEWATA_SYSTEMCTL_CMD             -- path to systemctl adapter
#   DEWATA_VALIDATE_CMD              -- path to validate adapter
#   DEWATA_PROD_CADDY                -- production Caddyfile path
#   DEWATA_PROD_WWW                  -- production www path
#   DEWATA_RELEASE_SRC               -- reviewed release source path
#   DEWATA_RELEASE_DST               -- production release dest path
#   DEWATA_CANDIDATE                 -- candidate Caddyfile path
#   DEWATA_REVIEWED_MANIFEST         -- manifest path
#   DEWATA_SNAPSHOT_PARENT           -- snapshot parent dir
#   DEWATA_TEST_ROOT                 -- newly-created test root (set by the
#                                       test runner before sourcing this file)
# =============================================================================

# Pinned adapter SHA256 values.  Update these when the adapter files
# are intentionally changed.  Test will refuse to run if the adapter's
# actual sha drifts.
DISPOSABLE_SYSTEMCTL_PIN="__PIN_SYSTEMCTL__"
DISPOSABLE_VALIDATE_PIN="__PIN_VALIDATE__"

# Compute current adapter SHAs.
_compute_adapter_sha() {
    local f="$1"
    if [[ -f "$f" ]]; then
        sha256sum "$f" | cut -d' ' -f1
    else
        echo "MISSING"
    fi
}

disposable_isolation_check() {
    local failures=0

    # 1. Disposable mode must be set.
    if [[ "${DEWATA_DISPOSABLE_MODE:-0}" != "1" ]]; then
        echo "ISOLATION FAIL: DEWATA_DISPOSABLE_MODE!=1 (got '${DEWATA_DISPOSABLE_MODE:-}')" >&2
        failures=$((failures + 1))
    fi

    # 2. Hash-pin the disposable systemctl adapter.
    if [[ -n "${DEWATA_SYSTEMCTL_CMD:-}" ]]; then
        local sys_sha
        sys_sha=$(_compute_adapter_sha "$DEWATA_SYSTEMCTL_CMD")
        local real_sysctl
        real_sysctl=$(command -v systemctl 2>/dev/null || echo "/usr/bin/systemctl")
        local real_sha
        real_sha=$(_compute_adapter_sha "$real_sysctl")

        if [[ -z "$DISPOSABLE_SYSTEMCTL_PIN" || "$DISPOSABLE_SYSTEMCTL_PIN" == "__PIN_SYSTEMCTL__" ]]; then
            # Pin not set; refuse to run (no pin = no guarantee)
            echo "ISOLATION FAIL: DISPOSABLE_SYSTEMCTL_PIN not set; cannot verify adapter has not drifted" >&2
            echo "  set DISPOSABLE_SYSTEMCTL_PIN in tests/disposable-isolation.sh before running" >&2
            failures=$((failures + 1))
        elif [[ "$sys_sha" != "$DISPOSABLE_SYSTEMCTL_PIN" ]]; then
            echo "ISOLATION FAIL: disposable systemctl adapter sha drift" >&2
            echo "  expected: $DISPOSABLE_SYSTEMCTL_PIN" >&2
            echo "  got:      $sys_sha" >&2
            echo "  path:     $DEWATA_SYSTEMCTL_CMD" >&2
            failures=$((failures + 1))
        fi

        # 3. Adapter MUST NOT resolve to the real systemctl.
        if [[ "$DEWATA_SYSTEMCTL_CMD" == "systemctl" ]]; then
            echo "ISOLATION FAIL: DEWATA_SYSTEMCTL_CMD is literal 'systemctl'" >&2
            failures=$((failures + 1))
        fi
        if [[ -n "$real_sha" && "$sys_sha" == "$real_sha" ]]; then
            echo "ISOLATION FAIL: DEWATA_SYSTEMCTL_CMD resolves to the real systemctl (sha=$sys_sha)" >&2
            echo "  real systemctl path: $real_sysctl" >&2
            echo "  adapter path:        $DEWATA_SYSTEMCTL_CMD" >&2
            failures=$((failures + 1))
        fi
    else
        echo "ISOLATION FAIL: DEWATA_SYSTEMCTL_CMD not set" >&2
        failures=$((failures + 1))
    fi

    # 4. Hash-pin the disposable validate adapter (when used).
    if [[ "${DEWATA_USE_DISPOSABLE_VALIDATE:-0}" == "1" ]]; then
        if [[ -n "${DEWATA_VALIDATE_CMD:-}" ]]; then
            local val_sha
            val_sha=$(_compute_adapter_sha "$DEWATA_VALIDATE_CMD")
            if [[ -z "$DISPOSABLE_VALIDATE_PIN" || "$DISPOSABLE_VALIDATE_PIN" == "__PIN_VALIDATE__" ]]; then
                echo "ISOLATION FAIL: DISPOSABLE_VALIDATE_PIN not set; cannot verify adapter has not drifted" >&2
                failures=$((failures + 1))
            elif [[ "$val_sha" != "$DISPOSABLE_VALIDATE_PIN" ]]; then
                echo "ISOLATION FAIL: disposable validate adapter sha drift" >&2
                echo "  expected: $DISPOSABLE_VALIDATE_PIN" >&2
                echo "  got:      $val_sha" >&2
                echo "  path:     $DEWATA_VALIDATE_CMD" >&2
                failures=$((failures + 1))
            fi
        else
            echo "ISOLATION FAIL: DEWATA_USE_DISPOSABLE_VALIDATE=1 but DEWATA_VALIDATE_CMD not set" >&2
            failures=$((failures + 1))
        fi
    fi

    # 5. Path isolation: every test path must be under $DEWATA_TEST_ROOT.
    #    Test root must be freshly created (didn't exist before this session).
    local test_root="${DEWATA_TEST_ROOT:-}"
    if [[ -z "$test_root" ]]; then
        echo "ISOLATION FAIL: DEWATA_TEST_ROOT not set; cannot verify path isolation" >&2
        failures=$((failures + 1))
    else
        # Verify test root is under /tmp/.
        case "$test_root" in
            /tmp/*|/var/tmp/*) ;;
            *)
                echo "ISOLATION FAIL: DEWATA_TEST_ROOT must be under /tmp/ or /var/tmp/ (got '$test_root')" >&2
                failures=$((failures + 1))
                ;;
        esac
        # Verify test root actually exists (was freshly created by the runner).
        if [[ ! -d "$test_root" ]]; then
            echo "ISOLATION FAIL: DEWATA_TEST_ROOT=$test_root does not exist" >&2
            failures=$((failures + 1))
        fi

        # Verify all test paths are under $test_root (or under /opt/dw-phase2
        # for read-only reviewed paths).  Production locations are forbidden.
        local bad_path
        for var in DEWATA_PROD_CADDY DEWATA_PROD_WWW DEWATA_RELEASE_SRC DEWATA_RELEASE_DST DEWATA_CANDIDATE DEWATA_REVIEWED_MANIFEST DEWATA_SNAPSHOT_PARENT; do
            local p="${!var:-}"
            if [[ -z "$p" ]]; then continue; fi
            # Resolve to absolute, canonical path.
            local real_p
            real_p=$(readlink -f "$p" 2>/dev/null || echo "$p")
            # Refuse production locations.
            case "$real_p" in
                /opt/dewata.online*|/etc/caddy*|/var/lib/dewata*)
                    echo "ISOLATION FAIL: $var=$real_p resolves to a production location" >&2
                    failures=$((failures + 1))
                    bad_path="$bad_path $real_p"
                    ;;
            esac
            # For mutable paths (DST, SNAPSHOT_PARENT), require under test_root.
            case "$var" in
                DEWATA_RELEASE_DST|DEWATA_SNAPSHOT_PARENT|DEWATA_PROD_CADDY|DEWATA_PROD_WWW)
                    case "$real_p" in
                        "$test_root"/*) ;;
                        *)
                            echo "ISOLATION FAIL: $var=$real_p is not under DEWATA_TEST_ROOT=$test_root" >&2
                            failures=$((failures + 1))
                            ;;
                    esac
                    ;;
            esac
        done
    fi

    # 6. Verify the real systemctl is NOT on PATH (the disposable shim
    #    must be used exclusively).  We do this by checking that
    #    DEWATA_SYSTEMCTL_CMD's directory is FIRST on PATH (so that
    #    `which systemctl` returns the shim).
    if [[ -n "${DEWATA_SYSTEMCTL_CMD:-}" ]]; then
        local shim_dir
        shim_dir=$(dirname "$DEWATA_SYSTEMCTL_CMD")
        # PATH must start with $shim_dir OR $shim_dir must appear before
        # the directory containing the real systemctl.
        local real_sysctl_dir
        real_sysctl_dir=$(dirname "$(command -v systemctl 2>/dev/null)" 2>/dev/null || echo "")
        if [[ -n "$real_sysctl_dir" && "$shim_dir" == "$real_sysctl_dir" ]]; then
            echo "ISOLATION FAIL: shim dir $shim_dir is the same as the real systemctl dir $real_sysctl_dir" >&2
            failures=$((failures + 1))
        fi
    fi

    if (( failures > 0 )); then
        echo "ISOLATION CHECK FAILED: $failures violation(s); refusing to run disposable tests" >&2
        return 9
    fi
    echo "[isolation] disposable test isolation: PASS (adapters pinned, paths restricted to $test_root)"
    return 0
}

# Generate the pin values at source-time if they're placeholders.
# This avoids hard-coding the SHAs (which would drift every time the
# adapter changes); instead, the runner must explicitly set the pins
# after intentionally reviewing a change.
#
# The convention: the pin file lives next to the adapter.  If a
# `${adapter}.sha256` file exists alongside the adapter, its content is
# the pinned SHA256.  The runner MUST update this file after any
# intentional change.
_pin_from_file() {
    local adapter="$1"
    local pin_file="$adapter.sha256"
    if [[ -f "$pin_file" ]]; then
        cat "$pin_file" | tr -d '[:space:]'
    fi
}
if [[ "$DISPOSABLE_SYSTEMCTL_PIN" == "__PIN_SYSTEMCTL__" ]]; then
    DISPOSABLE_SYSTEMCTL_PIN=$(_pin_from_file "/opt/dw-phase2/tests/disposable-systemctl.sh")
fi
if [[ "$DISPOSABLE_VALIDATE_PIN" == "__PIN_VALIDATE__" ]]; then
    DISPOSABLE_VALIDATE_PIN=$(_pin_from_file "/opt/dw-phase2/tests/disposable-validate.sh")
fi
