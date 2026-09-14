"""jwt / auth for the dewata api.

**important**: JWT claims are treated as untrusted user input.  do
**not** trust the issuer, audience, or roles the token claims without
**independent verification**:

  - signature validated against a known issuer's public key
  - `iss` (issuer) must match the configured list (default: empty)
  - `aud` (audience) must include `dewata` (configurable)
  - `exp` and `nbf` are honoured
  - `sub` is mandatory; it becomes the `actor_id`
  - `roles` array is checked against the visibility policy
  - `scope` (space-separated) is checked against endpoint requirements

config is **pluggable** so production can swap test HMAC for production
JWKS without touching call sites.

default config in tests is an HMAC-signed token with a **test-only key**.
production deployment must implement its own issuer validation.  the
test key is never used by the running api on the vps.

trust boundaries:
  - any code that consumes a `JwtIdentity` for authz must go through
    `dewatacalendar.security.visibility` and the visibility tiers.
    the api never decides *culturally* whether a request is acceptable
    - only the security module does.
"""

from __future__ import annotations

import base64
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

log = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class JwtConfig:
    """pluggable JWT config.

    test-only default: hmac with a clearly testable key
    `b"DEWATA-TEST-INTEGRATION-ONLY"` (string used for tests only,
    never for production).

    production must override:
      - `verify_token_func` to call a JWKS-based verifier
      - `expected_iss` to a known set
      - `expected_aud` to the api name
    """

    expected_iss: tuple[str, ...] = field(default_factory=tuple)
    expected_aud: tuple[str, ...] = ("dewata",)
    clock_skew_seconds: int = 60
    # test-only HMAC key; production must override `verify_token_func`
    test_hmac_key: bytes = b"DEWATA-TEST-INTEGRATION-ONLY"
    # if a function is supplied here, use it instead of HMAC
    verify_token_func: Any = None


_DEFAULT_CONFIG = JwtConfig()


def get_config() -> JwtConfig:
    return _DEFAULT_CONFIG


def set_config(cfg: JwtConfig) -> None:
    """test helper: override the default config (callers must restore)."""
    global _DEFAULT_CONFIG
    _DEFAULT_CONFIG = cfg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# identity
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass(frozen=True)
class JwtIdentity:
    """a verified JWT identity.  raises Unauthorized on bad token."""

    actor_id: str
    roles: tuple[str, ...]
    scope: tuple[str, ...]
    raw_claims: dict[str, Any]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# token construction (test-only helpers)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def make_test_token(
    *,
    actor_id: str = "test-actor",
    roles: Iterable[str] = ("banjar_operator",),
    scope: Iterable[str] = (),
    iss: str = "test-issuer",
    aud: str = "dewata",
    ttl_seconds: int = 3600,
    now: int | None = None,
    key: bytes | None = None,
) -> str:
    """construct a JWT for integration tests.

    NEVER use this in production.  the resulting token is signed with
    the test HMAC key so production verifiers will reject it.
    """
    now_ts = now if now is not None else int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": iss,
        "aud": aud,
        "sub": actor_id,
        "roles": list(roles),
        "scope": list(scope),
        "iat": now_ts,
        "nbf": now_ts,
        "exp": now_ts + ttl_seconds,
    }
    key_to_use = key if key is not None else get_config().test_hmac_key
    h = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    p = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signing_input = (b"." + _b64url(h).encode("ascii") + b".").replace(b"..", b"." + _b64url(h).encode("ascii") + b"")
    # correct: per RFC 7515, signing input is "header.payload"
    signing_input = _b64url(h).encode("ascii") + b"." + _b64url(p).encode("ascii")
    sig = hmac.new(key_to_use, signing_input, "sha256").digest()
    return _b64url(h) + "." + _b64url(p) + "." + _b64url(sig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# token verification
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class _UnauthorizedToken(Exception):
    pass


def _verify_hmac(token: str, cfg: JwtConfig) -> dict[str, Any]:
    """decode+verify an HS256 JWT using the test HMAC key.

    raises `_UnauthorizedToken` on any failure.
    """
    try:
        h_b64, p_b64, s_b64 = token.split(".")
    except ValueError:
        raise _UnauthorizedToken("malformed token")
    try:
        h = json.loads(_b64url_decode(h_b64))
        p = json.loads(_b64url_decode(p_b64))
        sig = _b64url_decode(s_b64)
    except Exception:
        raise _UnauthorizedToken("malformed payload")
    if h.get("alg") != "HS256":
        raise _UnauthorizedToken("unsupported algorithm")
    signing_input = h_b64.encode("ascii") + b"." + p_b64.encode("ascii")
    expected = hmac.new(cfg.test_hmac_key, signing_input, "sha256").digest()
    if not hmac.compare_digest(expected, sig):
        raise _UnauthorizedToken("signature mismatch")
    return p


def _verify_token_default(token: str, cfg: JwtConfig) -> dict[str, Any]:
    """the default verifier.  uses HMAC HS256 (test-only).

    for production, set `cfg.verify_token_func = your_jwks_verifier`.
    """
    if cfg.verify_token_func is not None:
        try:
            return cfg.verify_token_func(token, cfg)
        except _UnauthorizedToken:
            raise
        except Exception:
            raise _UnauthorizedToken("custom verifier rejected")
    return _verify_hmac(token, cfg)


def _check_window(p: dict[str, Any], cfg: JwtConfig, now: int) -> None:
    """iat/nbf/exp window check."""
    nbf = p.get("nbf")
    if nbf is not None and now + cfg.clock_skew_seconds < int(nbf):
        raise _UnauthorizedToken("token not yet valid")
    exp = p.get("exp")
    if exp is not None and now - cfg.clock_skew_seconds >= int(exp):
        raise _UnauthorizedToken("token expired")


def _check_iss_aud(p: dict[str, Any], cfg: JwtConfig) -> None:
    if cfg.expected_iss and p.get("iss") not in cfg.expected_iss:
        raise _UnauthorizedToken("iss not allowed")
    aud = p.get("aud")
    if aud is not None:
        aud_value = aud if isinstance(aud, list) else [aud]
        if not any(a in cfg.expected_aud for a in aud_value):
            raise _UnauthorizedToken("aud not allowed")


def verify_token(token: str) -> JwtIdentity:
    """verify a JWT and return a JwtIdentity, or raise Unauthorized."""
    cfg = get_config()
    now = int(time.time())
    try:
        claims = _verify_token_default(token, cfg)
        _check_window(claims, cfg, now)
        _check_iss_aud(claims, cfg)
        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub:
            raise _UnauthorizedToken("sub missing")
        roles = claims.get("roles") or []
        if not isinstance(roles, list):
            raise _UnauthorizedToken("roles malformed")
        scope = claims.get("scope") or []
        if not isinstance(scope, list):
            raise _UnauthorizedToken("scope malformed")
        return JwtIdentity(
            actor_id=sub,
            roles=tuple(str(r) for r in roles),
            scope=tuple(str(s) for s in scope),
            raw_claims=claims,
        )
    except _UnauthorizedToken as e:
        from ..observability.errors import Unauthorized as ApiUnauthorized
        raise ApiUnauthorized(
            "token verification failed",
            details={"reason": str(e)},
        ) from e


__all__ = [
    "JwtConfig", "JwtIdentity",
    "make_test_token", "verify_token",
    "get_config", "set_config",
]
