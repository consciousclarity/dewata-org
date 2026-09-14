# Threat Model & Trust Boundaries — Dewata.org

> this document is **provisional** until customary sign-off exists in
> `phase-1/docs/runbook/SIGNOFF.md`.  no cultural authority ordering
> claimed here is ratified.

## 1. actors

a request reaching `api.dewata.org` carries one of:

- an **anonymous caller** (HTTP only, no JWT)
- an **authenticated actor** (JWT with `iss`, `aud`, `exp`, `sub`, `roles`,
  `scope` claims).  the JWT is treated as **untrusted input** and is
  validated by a config-driven verifier before any claim is acted on.
- a **service caller** (e.g. a banjar-side mirror daemon) with a
  long-lived API token presented as `Authorization: Bearer`.

a *deny-by-default* posture is in effect.  an anonymous caller
**may not write**.  a JWT without a recognised actor claim
**may not write**.  a JWT with a recognised claim **may write
within the resource-tier-and-actor-bounds** the policy says.

## 2. trust boundaries

| zone | protects | threats considered |
|---|---|---|
| **edge (cloudflare)** | origin exposure, transport | TLS, DDoS, geographic routing |
| **cloudflare tunnel** | service exposure to internet | the tunnel ingress replaces port-80/443 listening.  no public ingress on origin. |
| **origin host (62.72.7.218)** | caddy, dewata-api, postgis, systemd | local-root compromise via misconfiguration |
| **services** | dewata-api (uvicorn), postgis (shared container) | auth bypass, sql injection, log leak |
| **operator console (future)** | bendesa committee access | UI-level social engineering, password reuse |

## 3. assets worth protecting

a) **records**

ceremonies carry cultural-sensitive fields.  the visibility tier
declared on the record governs who sees what:

- `public`: world
- `banjar`: members of the banjar (provisional — see DefaultPolicy)
- `desa_adat`: customary village scope (provisional)
- `restricted`: family / pemangku / sacred scope (provisional)
- `private`: per-actor

b) **identity**

actor phones, emails, signatures, and key fingerprints are scoped
private.  agent records (provisional): `actor_id`,
`actor_phone_id`, `actor_scopes`, `delegation_chain` are not visible
in public endpoints.

c) **calendar-rule evidence**

disputes captured in `phase-1/docs/runbook/disputes.json` carry
`source` and `page` provenance.  those are documented publicly.

d) **signing material**

**not yet used.**  the project carries an `Age encryption identity`
placeholder in `phase-1/src/dewatacalendar/__init__.py`-adjacent doc-comments.
Age is an **encryption tool**, not a digital-signature system; do
not rely on the placeholder.  see `docs/security/SIGNING-ADR.md` for
the dedicated decision record.

## 4. threat inventory

| id | threat | mitigation today | mitigation owner |
|---|---|---|---|
| T-01 | misclassified records (e.g. `restricted` field exposed on `public`) | `redact_field` + `sanitise_response` + `default_private_field_names()` enforcement layer | code-author |
| T-02 | cross-banjar leak (banjar A reads banjar B's banjar-tier) | `DefaultPolicy._actor_in_banjar` test + cross-banjar isolation assertion | code-author |
| T-03 | over-confident policy toward un-ratified cultural rules | all cultural decisions provisional; `DefaultPolicy` is config-driven; SIGNOFF.md placeholder empty | consortium |
| T-04 | JWT forgery (forged issuer-claim) | JWT verifier: iss, aud, exp, sub, roles, scope — fail-closed | api-author |
| T-05 | logging secret leakage | `redact_log_string()`; surface redaction in CI | code-author |
| T-06 | admin-token sprawl | admin role grants every tier BUT every other role denies-by-default.  ops reads through one named token; no one-time admin grants. | ops |
| T-07 | db injection | SQLAlchemy/Pydantic + parameter binding (when we integrate postgis) | code-author |
| T-08 | static key exfiltration via `/brief`-style routes | `DOWNLOADS_DIR` exposed via `/brief` is a temporary one-shot; future attachments hashed-and-pinned | code-author |
| T-09 | "evidence_blob" fields leak via API | those keys are auto-redacted by `sanitise_response` | code-author |
| T-10 | role-mixup via actor claim | role is enum; mismatch against scopes raises in `enforce_visibility` | code-author |
| T-11 | growable attack surface via "operator PWA" | PWA is not yet shipped; threat model updated when shipped | future |
| T-12 | "smart" pattern matching that masks what it claims to mask | unit-tested with both expected-replacement AND expected-preservation cases (see `test_redacts_benign_strings`) | code-author |
| T-13 | camera/phone recording leak | features that touch media (USSD/IVR voice) are out-of-scope for v0.1 | n/a |
| T-14 | conspiracy of two mirror partners | at least one mirror required; mirror-to-mirror attestation is feature-flagged behind mesh signature | not active |
| T-15 | production baseline drift | worktree at `/opt/dw-phase2` tracks `5919cf4`; `main` is production | consortium |

## 5. trust-boundary matrix

| data | at rest | in transit | logged | durable |
|---|---|---|---|---|
| ceremony records (future) | postgis | TLS → cloudflare → application | redaction in-flight | mirror-redundant |
| actor records (future) | postgis | same | redaction in-flight | n/a |
| dispute records | `phase-1/docs/runbook/disputes.json` (committed) | n/a | n/a | git |
| signing-key material | **not yet used** | n/a | n/a | n/a |

## 6. security assumptions

- `cloudflared`-managed tunnel (Cloudflare auth) is the trust front
  edge.  a breach of cloudflare's edge auth is out-of-band for this
  project.  we accept this because the platform does not generate
  certs / does not run TLS at origin for v0.1.
- postgis database ACLs assume `postgres` superuser access is
  privileged.  the `dewata` role is least-privileged within the
  shared instance.
- log redaction is regex-based and **known incomplete**.  it
  protects against the most-common shapes.  consumers of structured
  logs must still review.

## 7. what's NOT in this threat model

- AI-/LLM-driven reasoning: out of scope (the platform has no LLM
  features in v0.1).
- Mobile/desktop clients: not yet shipped.
- Cryptographic snapshot signing: see ADR (separate document).
- Phone-SMS flow for pemangku: feature, not threat-model item.

## 8. operational checklist (on changes)

whenever a code change touches:

1. `phase-1/src/dewatacalendar/security/`
2. `phase-1/src/dewatacalendar/i18n.py`
3. any DSP endpoint or payload shape
4. any postgis migration or seeding logic
5. the visibility tier labels

…please run the visible-tier test suite:

    python -m pytest phase-1/tests/security/ -v

and append to this document if a new threat class is introduced.

## 9. review cadence

every 90 days.  next review: 13 December 2026.

## 10. open questions for the consortium

| | |
|---|---|
| Q-S-1 | which actor type records *the official customary witness* of a record? | pending consortium review |
| Q-S-2 | does banjar-tier require SMS-OTP per request, or is signed JWT enough? | pending consortium review |
| Q-S-3 | which authorities may declare a record **public** without going through `banjar` first? | pending SIGNOFF.md |

— the consortium
