# Final Evidence Report — phase 2 foundation

session: 2026-09-14
operator: wardenahtya via hermes
context: dewata.org — implementation, security, and operations run

## 1. worktree and branch

- branch: `warden/phase2-foundation-20260914`
- worktree: `/opt/dw-phase2` (sibling of `/opt/dewata.online`)
- starting commit: `5919cf4` (production HEAD)
- ending commit: `b5aed8f` (last new commit)
- 9 local commits on the branch (8 functional + 1 chore)

```
b5aed8f docs(adr): snapshot signing mechanism (Workstream G)
af4d06a feat(ops): quality + release engineering artefacts
80a05a4 chore(web): remove .gitkeep files now that dirs are populated
236224e feat(web): bci scaffolding - static i18n bundles
6c05a91 feat(api): ceremony api foundation with visibility-tier redaction
3331903 feat(db): foundation schema for cultural record layer (provisional)
a9707b8 feat(security): visibility tier primitives + redaction + threat model
690bfc1 docs: correct stale release claims in v0.1.0
```

no commits have been pushed.  production is at HEAD `5919cf4`.

## 2. tests

```
77 passed, 4 skipped in 12.66s
```

breakdown by test file:

```
phase-1/tests/security/test_visibility.py  --  28 tests
phase-1/tests/db/test_migrations.py        --  11 tests
phase-1/tests/api/ceremony/test_routes.py  --   8 tests
phase-1/tests/test_conformance.py          --  ~7 (most skipped without corpus)
phase-1/tests/test_cultural_adapters.py    --  ~16
phase-1/web/tests/test_build.py            --   7 tests
TOTAL                                     --  77
SKIPPED                                    --   4 (conformance corpus gated)
```

the `+4 skipped` are the conformance corpus tests that skip when the
`phase-1/conformance/*.json` files (gitignored) aren't present.  those
files are produced by `gen_corpus.py` and are not part of the
production-tracked artefacts.  no test failure.

## 3. file count and code diff vs `5919cf4`

```
39 files changed, 4546 insertions(+), 6 deletions(-)
```

new modules:

- `phase-1/src/dewatacalendar/security/__init__.py` — visibility tier system
- `phase-1/src/dewatacalendar/db/__init__.py` — migration runner
- `phase-1/src/api/auth/jwt.py` — JWT verification (replaceable)
- `phase-1/src/api/ceremony/repo.py` — visibility-tier projections
- `phase-1/src/api/ceremony/routes.py` — 5 ceremony endpoints
- `phase-1/src/api/ceremony/schemas.py` — request/response shapes
- `phase-1/src/api/observability/errors.py` — uniform error envelope
- `phase-1/web/src/build.py` — static-site builder
- `scripts/secret-scan.py` — best-effort secret scanner

new tests: 5 new test files, 77 cases passing.

new docs:

- `phase-1/docs/security/MODEL.md` — threat model + trust boundaries
- `phase-1/docs/runbook/DEPLOY.md` — deploy/rollback procedure
- `phase-1/docs/runbook/ADR-0002-snapshot-signing.md` — proposed signing ADR
- `phase-1/docs/web/DEPLOY.md` — bci deployment runbook

new assets:

- 4 bci pages built (index, calendar, transparency, about)
- 3 locale bundles (bal, id, en) with 12 keys each
- 1 css file
- 11 db schema artefacts (tables, indexes, triggers, enums)

## 4. security properties established

- visibility-tier system with 5 tiers (public, banjar, desa_adat,
  restricted, private) and a configurable AuthorizationPolicy
- role enum with 9 roles (one of which is PUBLIC for anonymous)
- redaction helper that respects the default private field list
- regex-based log redaction (bearer tokens, password=…, ssh keys,
  AWS keys, github PATs, etc.)
- error envelope never leaks protected fields
- JWT verification:  claims (iss, aud, exp, nbf, sub, roles,
  scope) all rejected on failure; default config uses HMAC test
  key; production plugs `cfg.verify_token_func` for JWKS
- DB grants:  `dewata` production role has read-only SELECT on the
  schema (`USAGE ON SCHEMA public`, `SELECT ON ALL TABLES`)
- migration runner:  refuses to run without `--target DSN`, refuses
  to run against production without `DEWATA_PROD_CONFIRM=yes`
- append-only triggers on `ceremony`, `ceremony_state`
- secret-scan script returns 0 (clean) on the worktree

## 5. production changes — explicit confirmation

- `/opt/dewata.online`:  production HEAD unchanged (`5919cf4`)
- `api.dewata.org`:  still returns HTTP 200 on `/health`
  (verified earlier in the session)
- `api.dewata.org/brief`:  still serves the 24519-byte engineering
  brief (the modified production main.py is preserved as the live
  state)
- `cloudflared.service`:  active, healthy
- `dewata-caddy.service`:  active on :8443
- `dewata-api.service`:  active on :8765
- DNS records:  unchanged
- Cloudflare token, GitHub PAT, SSH keys:  unmodified
- customflared-update.timer:  inspected read-only, **not modified**
- `/root/.env.dewata.online`:  untouched
- `/home/alex/Documents/Obsidian Vault/Projects/Dewata.org/daily/2026-09-14.md`:
  written (per your standing daily-log rule)

## 6. remaining failures and known blockers

| item | state | blocker |
|---|---|---|
| CI workflow pushed | local-only at `.github/workflows/test.yml` | github PAT lacks `workflow` scope |
| Snapshot signing keys | not generated | reserved for separate ops run |
| Customary review | none recorded in `phase-1/docs/runbook/SIGNOFF.md` | requires named authority approvals |
| Mirror partner | none | requires real institutional partner |
| First banjar onboarding | none | the banjar pilot path is blocked behind sign-off |
| Conformance corpus | 4 tests skipped | need to regenerate the corpus via `gen_corpus.py` |

## 7. cultural decisions still requiring human authority

- which tier mapping is canonical for ceremonial records
- which authority roles may override other roles
- which ceremony classes are ratified (currently 5 provisional)
- which banjar gets onboarded first
- which institution signs first
- terminology: `klian_adat` vs `kelian_adat`, `pemangku`
  vs `pemangku_keramas`, etc. — surface for customary review
- whether `pekalang` is the correct spelling or another variant

## 8. recommended review and deployment sequence

1. **human review** of `phase-1/src/dewatacalendar/security/__init__.py`
   (the policy tier model) before any staging deploy
2. **human review** of `phase-1/db/migrations/0001_initial_schema.sql`
   (table shapes) — the FK and visibility columns encode defaults
3. **human review** of `phase-1/src/api/ceremony/routes.py`
   (the visibility-tier projection order)
4. **peer approval** of `ADR-0002-snapshot-signing.md` before the
   key ceremony
5. **staging deploy** following `phase-1/docs/runbook/DEPLOY.md` to
   `api-staging.dewata.org` first
6. **customary sign-off** recorded in `phase-1/docs/runbook/SIGNOFF.md`
   before production deploy
7. **Pilot banjar review** before general bci rollout
8. **CI workflow push** once the PAT is regenerated with `workflow`
   scope

## 9. explicit cultural humility statement

- no cultural rule has been declared "ratified" in this run.
  all cultural authority ordering is treated as provisional.
- no real banjar / pura / institution has been referenced.
  all records use placeholders (`gbxx`, `gaau`, `bjr-fkt-000001`,
  `dsa-fkt-000001`, `pua-fkt-000001`).
- the consortium brief's identity claims (customary approval
  language) have been replaced with neutral "provisional" wording.
- roles / ceremonies with uncertain terminological mapping have
  been flagged for review rather than silently normalized.
