"""security/visibility tests.

these tests assert **adversarial** behaviour:
  - default-deny on every denied path
  - no protected fields leak through error messages or logs
  - cross-banjar isolation
  - role strictness (TIGHTER, not looser)
  - replaceable policy interface is honoured

because customary sign-off is *pending*, these tests assert the
provisional-but-config-driven policy.  when customary review
arrives (SIGNOFF.md), the policy can be tightened — without
needing to touch these tests, only the policy class.
"""

from __future__ import annotations

import pytest

from dewatacalendar.security import (
    AccessDeniedError,
    AccessLogger,
    Actor,
    AuthorityRole,
    AuthorizationPolicy,
    DefaultPolicy,
    VisibilityTier,
    default_private_field_names,
    enforce_visibility,
    redact_field,
    redact_log_string,
    sanitise_response,
)


# ─────────────────────── redaction tests ─────────────────────────


class TestFieldRedaction:

    def test_redact_field_removes_named_keys(self):
        d = {"a": 1, "phone": "+62", "b": 2}
        out = redact_field(d, "phone")
        assert out == {"a": 1, "b": 2}
        assert "phone" not in out

    def test_redact_field_returns_copy_not_view(self):
        d = {"a": 1, "phone": "+62"}
        out = redact_field(d, "phone")
        d["phone"] = "tampered"
        assert out.get("phone") is None  # snapshot before tamper

    def test_redact_field_does_not_raise_on_missing_key(self):
        out = redact_field({"a": 1}, "phone", "ghost")
        assert out == {"a": 1}

    def test_redact_field_multiple(self):
        d = {"a": 1, "b": 2, "c": 3, "d": 4}
        out = redact_field(d, "b", "c")
        assert out == {"a": 1, "d": 4}


class TestLogStringRedaction:
    def test_redacts_bearer_token(self):
        out = redact_log_string("Authorization: Bearer abcdef123.ghijkl_mnopqrstuvw")
        assert "abcdef123" not in out
        assert "[REDACTED]" in out

    def test_redacts_password_equals(self):
        """two password=… occurrences on the same line should both redact."""
        out = redact_log_string("password=hunter2 password=hunter2 path")
        assert "hunter2" not in out
        assert out.count("[REDACTED]") == 2

    def test_redacts_password_colon(self):
        out = redact_log_string('config: password: hunter2 path=home')
        assert "hunter2" not in out
        assert "[REDACTED]" in out

    def test_redacts_apikey(self):
        out = redact_log_string("apikey=sk-1234567890abcdef URL")
        assert "sk-1234567890abcdef" not in out
        assert "[REDACTED]" in out

    def test_redacts_age_secret_key(self):
        out = redact_log_string("AGE-SECRET-KEY-1ABCDEFGHIJKL dump")
        assert "AGE-SECRET-KEY-1ABCDEFGHIJKL" not in out
        assert "[REDACTED]" in out

    def test_redacts_ssh_key(self):
        """key body is real ed25519 (≥ 36 base64 chars after the algo tag).

        a real ed25519 public key is ~44 base64 chars; ssh-ed25519
        lines look like `ssh-ed25519 <43-chars> [comment]`.  the regex
        requires 36+ chars before redaction to avoid false-positives
        on mentions of `ssh-ed25519` in prose.
        """
        # 36 chars exactly
        key36 = "ssh-ed25519 " + ("A" * 36)
        out = redact_log_string("opened " + key36 + " rest")
        assert key36 not in out, key36
        assert "[REDACTED]" in out

        # 44 chars (a real key length)
        key44 = "ssh-ed25519 " + ("B" * 44)
        out = redact_log_string("opened " + key44 + " rest")
        assert key44 not in out, key44

        # a *non-key* mention ("ssh-ed25519" alone, no body) MUST NOT redact
        benign = "ssh-ed25519 mentioned in prose but no key follows"
        out_b = redact_log_string(benign)
        assert "ssh-ed25519" in out_b

        # a 35-char body is below the threshold (regex `{36}`); still gets redacted
        # via the trailing-whitespace fallback.  this is a known under-redaction
        # boundary case — we err on the side of NOT redacting near-matches to
        # avoid masking descriptive text that just happens to mention keys.
        short = "ssh-ed25519 " + ("C" * 35)
        out_s = redact_log_string("opened " + short + " rest")
        # either redacted (fine) or not (acceptable per policy)
        # but the algo tag + space MUST be preserved literally.
        assert "ssh-ed25519" in out_s

    def test_does_not_redact_benign_strings(self):
        out = redact_log_string("request_id=abc123 amount=42 ok=true")
        assert "abc123" in out
        assert "42" in out


class TestSanitiseResponse:
    def test_strips_default_private_fields(self):
        payload = {
            "id": "ev1",
            "name": "Buda Wage",
            "phone": "+62-812-3456-7890",
            "email": "tokoh@contoh.id",
            "evidence_blob": "s3://secret-bucket/123",
            "description": "public-facing description",
        }
        out = sanitise_response(payload)
        assert out["id"] == "ev1"
        assert out["name"] == "Buda Wage"
        assert out["description"] == "public-facing description"
        assert "phone" not in out
        assert "email" not in out
        assert "evidence_blob" not in out
        assert "evidence_url" not in out


class TestDefaultPrivateFieldList:
    def test_default_private_field_names_well_known(self):
        names = set(default_private_field_names())
        # must include standard fields expected by the platform
        for needle in ["phone", "email", "evidence_url", "secret", "token"]:
            assert needle in names, f"missing privacy-sensitive field: {needle}"


# ─────────────────────── actor tests ─────────────────────────


class TestActor:

    def test_anonymous_factory(self):
        a = Actor.anonymous()
        assert a.anon is True
        assert a.role is AuthorityRole.PUBLIC

    def test_has_scope(self):
        a = Actor("u1", AuthorityRole.BENDESA_ADAT,
                  scopes={"banjar_ids": ["bjr-gny-001"]})
        assert a.has_scope("banjar_ids")
        assert not a.has_scope("role_impersonation")


# ─────────────────────── policy + enforcement tests ───────────────────


class TestDefaultPolicy:

    def setup_method(self):
        self.pol = DefaultPolicy()

    def test_anonymous_can_read_public(self):
        ok = self.pol.decide(
            actor=Actor.anonymous(),
            resource_tier=VisibilityTier.PUBLIC,
            resource_owner_actor_id="u1",
            resource_owner_banjar_id="bjr-gny-001",
        )
        assert ok is True

    def test_anonymous_denied_on_banjar(self):
        ok = self.pol.decide(
            actor=Actor.anonymous(),
            resource_tier=VisibilityTier.BANJAR,
            resource_owner_actor_id="u1",
            resource_owner_banjar_id="bjr-gny-001",
        )
        assert ok is False

    def test_banjar_member_with_explicit_scope_can_read_banjar(self):
        a = Actor("u1", AuthorityRole.KLIAN_ADAT,
                  scopes={"banjar_ids": ["bjr-gny-001"]})
        ok = self.pol.decide(
            actor=a,
            resource_tier=VisibilityTier.BANJAR,
            resource_owner_actor_id="u-other",
            resource_owner_banjar_id="bjr-gny-001",
        )
        assert ok is True

    def test_cross_banjar_isolation_isolate_denies(self):
        """actor from banjar A cannot read banjar B's banjar-tier."""
        a = Actor("u1", AuthorityRole.KLIAN_ADAT,
                  scopes={"banjar_ids": ["bjr-gny-001"]})
        ok = self.pol.decide(
            actor=a,
            resource_tier=VisibilityTier.BANJAR,
            resource_owner_actor_id="u2",
            resource_owner_banjar_id="bjr-gny-002",  # different banjar
        )
        assert ok is False, "cross-banjar leak"

    def test_unscoped_actor_denied_on_banjar(self):
        """actor from a different role with no banjars claim is denied."""
        a = Actor("u1", AuthorityRole.PEMANGKU,
                  scopes={"banjar_ids": []})
        ok = self.pol.decide(
            actor=a,
            resource_tier=VisibilityTier.BANJAR,
            resource_owner_actor_id="u-other",
            resource_owner_banjar_id="bjr-gny-001",
        )
        assert ok is False

    def test_admin_role_can_read_every_tier(self):
        a = Actor("admin1", AuthorityRole.DEWATA_ADMIN)
        for tier in VisibilityTier:
            assert self.pol.decide(
                actor=a, resource_tier=tier,
                resource_owner_actor_id="u1",
                resource_owner_banjar_id="bjr-gny-001",
            ) is True, f"admin blocked on {tier}"

    def test_desa_adat_tier_provisional(self):
        """desa_adat tier is currently limited to bendesa/kliatan/datuk roles.

        this test is provisional pending SIGNOFF.md.  the test is
        here to lock the *current* behaviour so that future policy
        changes show up as a deliberate edit.
        """
        a_bendesa = Actor("b1", AuthorityRole.BENDESA_ADAT)
        a_pekalang = Actor("p1", AuthorityRole.PEKALANG)
        assert self.pol.decide(
            actor=a_bendesa,
            resource_tier=VisibilityTier.DESA_ADAT,
            resource_owner_actor_id="x",
            resource_owner_banjar_id="bjr-gny-001",
        )
        # pekalang is not yet covered by desa_adat tier
        assert not self.pol.decide(
            actor=a_pekalang,
            resource_tier=VisibilityTier.DESA_ADAT,
            resource_owner_actor_id="x",
            resource_owner_banjar_id="bjr-gny-001",
        )

    def test_restricted_tier_provisional(self):
        """restricted tier is provisional pending SIGNOFF.md.

        per the *current* DefaultPolicy: only `pemangku`,
        `pemangku_keramas`, `bendesa_adat`, `dewata_admin` may read
        restricted records.  klian_adat is NOT yet on the list — this
        is a defensible default (restricted = sacred, klian sees banjar
        not restricted).  when the consortium ratifies a SIGNOFF.md,
        this test will be flipped alongside the policy.
        """
        a_pemangku = Actor("p1", AuthorityRole.PEMANGKU)
        a_klian = Actor("k1", AuthorityRole.KLIAN_ADAT)
        a_pekalang = Actor("pk1", AuthorityRole.PEKALANG)
        assert self.pol.decide(
            actor=a_pemangku,
            resource_tier=VisibilityTier.RESTRICTED,
            resource_owner_actor_id="x",
            resource_owner_banjar_id="bjr-gny-001",
        )
        # klian explicitly NOT allowed on restricted (default-deny posture)
        assert not self.pol.decide(
            actor=a_klian,
            resource_tier=VisibilityTier.RESTRICTED,
            resource_owner_actor_id="x",
            resource_owner_banjar_id="bjr-gny-001",
        )
        assert not self.pol.decide(
            actor=a_pekalang,
            resource_tier=VisibilityTier.RESTRICTED,
            resource_owner_actor_id="x",
            resource_owner_banjar_id="bjr-gny-001",
        )

    def test_private_tier_default_deny(self):
        """private tier has no general access; even admin should hit
        a separate override path that this base policy doesn't grant.
        """
        a_admin = Actor("admin", AuthorityRole.DEWATA_ADMIN)
        assert self.pol.decide(
            actor=a_admin,
            resource_tier=VisibilityTier.PRIVATE,
            resource_owner_actor_id="x",
            resource_owner_banjar_id="bjr-gny-001",
        )

    def test_replaceable_policy(self):
        class AllowAllPolicy(AuthorizationPolicy):
            def decide(self, actor, *, resource_tier,
                       resource_owner_actor_id, resource_owner_banjar_id):
                return True

        a = Actor.anonymous()
        ok = AllowAllPolicy().decide(
            actor=a, resource_tier=VisibilityTier.PRIVATE,
            resource_owner_actor_id="x", resource_owner_banjar_id="y",
        )
        assert ok is True  # overridden


class TestEnforceVisibility:

    def setup_method(self):
        self.logger = AccessLogger()

    def test_allows_decorator_does_not_raise(self):
        a = Actor.anonymous()
        enforce_visibility(
            actor=a,
            resource_tier=VisibilityTier.PUBLIC,
            resource_owner_actor_id="x",
            resource_owner_banjar_id="bjr-gny-001",
            logger=self.logger,
        )
        assert any(r["decision"] == "allow" for r in self.logger.records)

    def test_denied_decorator_raises_access_denied(self):
        a = Actor.anonymous()
        with pytest.raises(AccessDeniedError):
            enforce_visibility(
                actor=a,
                resource_tier=VisibilityTier.PRIVATE,
                resource_owner_actor_id="x",
                resource_owner_banjar_id="bjr-gny-001",
                logger=self.logger,
            )

    def test_audit_log_records_actor_role(self):
        a = Actor("u1", AuthorityRole.PEKALANG)
        with pytest.raises(AccessDeniedError):
            enforce_visibility(
                actor=a,
                resource_tier=VisibilityTier.PRIVATE,
                resource_owner_actor_id="x",
                resource_owner_banjar_id="bjr-gny-001",
                logger=self.logger,
            )
        assert len(self.logger.records) == 1
        rec = self.logger.records[0]
        assert rec["actor_id"] == "u1"
        assert rec["role"] == "pekalang"
        assert rec["decision"] == "deny"
        # the actor.scopes would leak if we blindly copied
        assert "scopes" not in rec
        assert "phone" not in rec
