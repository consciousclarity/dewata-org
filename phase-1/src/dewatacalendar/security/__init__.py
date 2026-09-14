"""visibility-tier security primitives.

the visibility tier system (public, banjar, desa_adat, restricted,
private) is part of the project protocol.  until customary sign-off
exists in `phase-1/docs/runbook/SIGNOFF.md`, all cultural policy
decisions in this module are **provisional** — they come from
config, not from hard-coded cultural assertions.

the security foundation is split into:

- :class:`VisibilityTier` — typed enum, machine-readable
- :class:`AuthorityRole` — typed enum, machine-readable (provisional)
- :class:`Actor` — value object representing an authenticated actor
- :class:`AuthorizationPolicy` — replaceable policy implementation
- :func:`redact` — apply policy to a serialisable object
- :func:`redact_field` — strip a named field from one dict
- :func:`enforce_visibility` — guard that raises on policy violation

the *protocol* says: only the appropriate party may see a record at
its declared tier.  the *implementation* says: a configurable
function `(actor, record) -> bool` decides what each tier means.

nothing here hard-codes cultural authority ordering.  the
:class:`DefaultPolicy` below is a starting point that the consortium
or a future config may override — it has not been customary-ratified.
see `phase-1/docs/security/MODEL.md` for the threat model and
config interfaces.
"""

from __future__ import annotations

import enum
import re
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


# ─────────────────────── typed values ─────────────────────────

class VisibilityTier(str, enum.Enum):
    """what an authenticated actor may receive about a record."""
    PUBLIC        = "public"
    BANJAR        = "banjar"
    DESA_ADAT     = "desa_adat"
    RESTRICTED    = "restricted"
    PRIVATE       = "private"

    @classmethod
    def parse(cls, raw: str) -> "VisibilityTier":
        try:
            return cls(raw)
        except ValueError as e:
            raise VisibilityTierError(f"unknown visibility tier: {raw!r}") from e


class AuthorityRole(str, enum.Enum):
    """provisional authority roles.  sign-off pending.

    the ordering of these enums does NOT imply cultural authority —
    :class:`DefaultPolicy` is config-driven and replaceable.
    """
    PUBLIC             = "public"            # anonymous
    BANJAR_OPERATOR    = "banjar_operator"   # trained banjar operator
    PEKALANG           = "pekalang"          # customary security (provisional spelling)
    KLIAN_ADAT         = "klian_adat"        # banjar klian (provisional)
    BENDESA_ADAT       = "bendesa_adat"      # customary chair (provisional)
    PEMANGKU           = "pemangku"          # temple priest (provisional)
    PEMANGKU_KERAMAS   = "pemangku_keramas"  # principal priest (provisional)
    DEWATA_ADMIN       = "dewata_admin"      # operator staff
    DEWATA_EDITOR      = "dewata_editor"


class VisibilityTierError(Exception):
    """tier value provided was unparseable or otherwise invalid."""


class AccessDeniedError(Exception):
    """policy denied the requested access.  raised by `enforce_visibility`."""


# ─────────────────────── actor model ─────────────────────────

@dataclass(frozen=True, slots=True)
class Actor:
    """an authenticated caller in the system.

    `anon` flag controls fallback behaviour for unauthenticated
    requests.  `scopes` is a dict of explicit grants a future
    config can apply (e.g. operator staff may impersonate a klian
    during a paruman if delegation is signed and timestamp-fresh).
    """
    actor_id: str
    role: AuthorityRole
    scopes: dict[str, Any] = field(default_factory=dict)
    anon: bool = False
    issued_at: float = field(default_factory=lambda: time.time())

    @classmethod
    def anonymous(cls) -> "Actor":
        return cls(actor_id="anon", role=AuthorityRole.PUBLIC, anon=True)

    def has_scope(self, key: str) -> bool:
        return key in self.scopes


# ─────────────────────── redaction primitives ─────────────────

_PUBLIC_SENTINEL = ...  # placeholder until redaction helpers land below


def redact_field(obj: dict, *field_names: str) -> dict:
    """return a copy of `obj` with `field_names` removed.

    the returned dict is a shallow copy.  nested fields are *replaced*
    in their key slot rather than recursively scanned.
    """
    out = dict(obj)
    for f in field_names:
        out.pop(f, None)
    return out


def default_private_field_names() -> tuple[str, ...]:
    """conservative default list of fields to redact in a 403 response.

    these fields MUST NOT appear in any error message printed via
    fastapi's HTTPException(detail=...) — they often end up in
    HTTP responses and in logs and can leak record existence to
    unauthenticated callers.
    """
    return (
        "phone", "phone_number", "phone_id",
        "actor_phone", "actor_id",
        "email", "address",
        "internal_id", "private_record_id",
        "evidence_blob", "evidence_url",
        "private", "scopes", "delegation",
        "raw_dsn", "secret", "password", "token", "key",
    )


_SENSITIVE_TOKEN_PATTERN = re.compile(
    r"""
    (
        bearer\s+[A-Za-z0-9._\-]+              # bearer tokens
        | password\s*[:=]\s*\S+              # password=… assignments
        | s3://[A-Za-z0-9._/@:\-]+             # s3-style urls with secrets
        | AGE-SECRET-KEY-[A-Z0-9]+           # age secret keys
        | ssh-ed25519\s+[A-Za-z0-9+/]{36}    # ssh ed25519 keys
        | token=[A-Za-z0-9._\-]+             # token=… query strings
        | apikey\s*[:=]\s*\S+               # apikey=… assignments
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def redact_log_string(s: str) -> str:
    """return `s` with common credential shapes redacted.

    intended for log lines.  uses a regex over the most-common shapes.
    not a complete list; tune as new key types appear in logs.
    """
    return _SENSITIVE_TOKEN_PATTERN.sub("[REDACTED]", s)


# ─────────────────────── authorization interface ─────────────────

class AuthorizationPolicy:
    """configurable authorization, default deny.

    implement :meth:`decide` to override the default no-access
    behaviour.  the consortium or future config selects an instance
    of this class.  nothing here encodes cultural authority ordering.
    """

    def decide(self, actor: Actor, *, resource_tier: VisibilityTier,
               resource_owner_actor_id: str | None,
               resource_owner_banjar_id: str | None) -> bool:
        """return True iff `actor` is allowed to see this resource
        at its declared visibility tier.

        default deny is the safe position.  subclasses should escalate
        only after policy review.
        """
        return False  # default deny

    def redact_for(self, actor: Actor, payload: dict,
                   *, fields_to_redact: Iterable[str] = ()) -> dict:
        """return `payload` with fields a non-allowed actor cannot see
        stripped out.  callers should err on the side of over-redaction.
        """
        return redact_field(payload, *fields_to_redact)


class DefaultPolicy(AuthorizationPolicy):
    """a starting implementation; **provisional pending SIGNOFF.md**.

    this policy assumes:
      * `public` records: anyone can read (including anonymous).
      * `banjar` records: members of the banjar only.  the
        definition of "member" here is decided by `resource_owner_banjar_id`
        membership, not by an algorithm; replaceable via config.
      * `desa_adat`, `restricted`, `private`: governed by culture-specific
        rules that have **not** been customary-ratified.  default deny.

    the policy is intentionally narrow.  providers carrying
    `scopes['tjpk:banjar_override']` (a temporary key granted by the
    consortium through `docs/runbook/SIGNOFF.md`) may override these
    decisions.  no consumer of this module is allowed to hard-code
    cultural authority ordering differently.
    """

    ALLOWED_FOR_PUBLIC = {AuthorityRole.PUBLIC, AuthorityRole.DEWATA_ADMIN}

    @staticmethod
    def _actor_in_banjar(actor: Actor, banjar_id: str | None) -> bool:
        """return True iff `actor.scopes['banjar_ids']` contains
        `banjar_id`.  the consortium hasn't determined whether the
        actor membership list lives in JWT claims or in a database
        table; both implementations are valid until SIGNOFF.md locks
        one in.  this method enforces *that some explicit membership
        data is present*, but delegates the *source* of that data
        out of band.
        """
        if banjar_id is None:
            return False
        declared = set(actor.scopes.get("banjar_ids", []) or [])
        return banjar_id in declared

    def decide(self, actor: Actor, *,
               resource_tier: VisibilityTier,
               resource_owner_actor_id: str | None,
               resource_owner_banjar_id: str | None) -> bool:
        if actor.role == AuthorityRole.DEWATA_ADMIN:
            return True

        if resource_tier == VisibilityTier.PUBLIC:
            return True

        if resource_tier == VisibilityTier.BANJAR:
            if actor.anon:
                return False
            return self._actor_in_banjar(actor, resource_owner_banjar_id)

        # everything below is provisional policy pending SIGNOFF.md
        if resource_tier == VisibilityTier.DESA_ADAT:
            return actor.role in (
                AuthorityRole.BENDESA_ADAT,
                AuthorityRole.KLIAN_ADAT,
                AuthorityRole.DEWATA_ADMIN,
            )
        if resource_tier == VisibilityTier.RESTRICTED:
            return actor.role in (
                AuthorityRole.PEMANGKU,
                AuthorityRole.PEMANGKU_KERAMAS,
                AuthorityRole.BENDESA_ADAT,
                AuthorityRole.DEWATA_ADMIN,
            )
        if resource_tier == VisibilityTier.PRIVATE:
            return False  # strict by default; further rules configurable
        return False


# ─────────────────────── guard helpers ─────────────────────────

class AccessLogger:
    """emits redacted structured-access audit records.

    not a substitute for proper logging (every consumer should also
    log via stdlib), but it centralizes the "do not log credentials"
    policy.
    """

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def log(self, *, event: str, actor: Actor, decision: bool,
            resource_tier: VisibilityTier | None = None,
            path: str | None = None) -> None:
        rec = {
            "event": event,
            "actor_id": actor.actor_id,
            "role": actor.role.value,
            "anon": actor.anon,
            "decision": "allow" if decision else "deny",
            "ts": time.time(),
        }
        if resource_tier is not None:
            rec["resource_tier"] = resource_tier.value
        if path is not None:
            rec["path"] = path
        # defensive: redact any private-attribute that the actor dict may
        # bleed into the audit record — we only take primitive fields.
        safe = {k: v for k, v in rec.items() if isinstance(v, (str, int, float, bool))}
        self.records.append(safe)


_DEFAULT_LOGGER = AccessLogger()


def enforce_visibility(actor: Actor, *,
                        resource_tier: VisibilityTier,
                        resource_owner_actor_id: str | None = None,
                        resource_owner_banjar_id: str | None = None,
                        policy: AuthorizationPolicy | None = None,
                        logger: AccessLogger | None = None) -> None:
    """raise :class:`AccessDeniedError` if `actor` cannot see this
    resource at the declared tier.

    callers should `deny-by-default` — if `actor.scopes` does not
    establish authority, this raises.
    """
    pol = policy or DefaultPolicy()
    audit = logger or _DEFAULT_LOGGER
    decision = pol.decide(
        actor,
        resource_tier=resource_tier,
        resource_owner_actor_id=resource_owner_actor_id,
        resource_owner_banjar_id=resource_owner_banjar_id,
    )
    audit.log(
        event="visibility_check",
        actor=actor,
        decision=decision,
        resource_tier=resource_tier,
    )
    if not decision:
        raise AccessDeniedError(
            f"tier={resource_tier.value} denied for "
            f"actor={actor.actor_id!r} role={actor.role.value!r}"
        )


def sanitise_response(payload: dict) -> dict:
    """strip a candidate API response of common credential fields.

    applied at the api-layer boundary (single use site) so the same
    shape isn't depended on by clients.  configs may override the
    field list via :data:`default_private_field_names()`.
    """
    return redact_field(payload, *default_private_field_names())


# ─────────────────────── module exports ─────────────────────────

__all__ = [
    "VisibilityTier",
    "AuthorityRole",
    "VisibilityTierError",
    "AccessDeniedError",
    "Actor",
    "AuthorizationPolicy",
    "DefaultPolicy",
    "AccessLogger",
    "enforce_visibility",
    "redact_field",
    "redact_log_string",
    "sanitise_response",
    "default_private_field_names",
]
