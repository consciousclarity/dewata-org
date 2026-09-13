# Architecture — full engineering plan (Phase 0 / Phase 1 staging)

## TL;DR

Dewata runs as a **modular monolith** in a single docker-compose stack on the existing `62.72.7.218` vps. Six reverse-proxied surface hosts behind cloudflare edge. PostgreSQL 16 + PostGIS 3.4 reused from the existing `shared-postgres` container. Calendar engine is a deterministic Python package with a Rust-rewrite path designed in but not paid for until spec v1 ships.

## 1. Layered layout (top to bottom)

```
┌────────────────────────────────────────────────────────────────────┐
│ Cloudflare edge                                                   │
│   *.dewata.org    one-click-wildcard-TLS   edge-cache / rate-limit │
│   Cloudflare Access at api.map.data for operator-only areas       │
└────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│ Caddy on the vps (existing)                                       │
│   server-block per surface host                                   │
│   bans non-cloudflare IPs at /api/* and /operator/*               │
└────────────────────────────────────────────────────────────────────┘
                            │
                            ▼  per-hostname routing
┌──────────────┬─────────────┬──────────────┬─────────────┬──────────────┐
│ dewata.org   │ api.        │ map.         │ data.       │ protocol.    │
│ static land- │ fastapi     │ next.js      │ grafana +   │ docusaurus   │
│ ing          │ (DSP)       │ + maplibre   │ drip meter  │ static       │
│ static next  │ openapi     │ operator PWA │ public dash │              │
│ export to    │ events      │              │             │              │
│ hostinger    │ calendar    │              │             │              │
└──────────────┴─────────────┴──────────────┴─────────────┴──────────────┘
        │
        └──── subdomains: <id>.<kab>.dewata.org  → next.js static per-pura, per-banjar

                          (static dataset snapshot)
              datasets.dewata.org → github pages static  (mirror, never reached from VIP)
```

Five surface hosts + apex static landing + an unbounded set of `<id>.<kab>.` records. Total: **1 nginx/caddy block** + **1 wildcard tls cert** + **1 wildcard dns record**.

## 2. Container topology

```
shared-network (host, existing)
   ├── shared-postgres (postgis/postgis:16-3.4) ──── shared with bali/gustale/scribe
   ├── dify-redis (redis:6-alpine)               ──── we reuse or run a new dewata-redis
   │                                                     container alongside it
   └── dewata stack ──┐
       ├── api       (python 3.12 + uvicorn, port 8000)
       ├── worker    (arq / dramatiq, port 8000, no listener, sidecar of api)
       ├── web       (next 14, port 3000)
       ├── protocol  (docusaurus, port 4001)
       ├── data      (grafana + simple-json-datasource, port 3001)
       └── caddy     (per-stack reverse proxy, port 8080 → 80/443)
```

Caddy inside the dewata stack stays isolated from the host-level Caddy. The host Caddy then sends `*.dewata.org` traffic to the **dewata caddy** at `127.0.0.1:8080`. Single ingress entry, internal fan-out.

Why a nested caddy:
- each project keeps its own Caddyfile, deployable independently
- no root-level nginx reload needed for every dewata config change
- cloudflare is the only entry facing users, this caddy only sees cache-misses

## 3. Database design (PostGIS)

```
┌── core identity ──┐
│ actor             │   user / institution / phone / pemangku / pecalang
│ actor_role        │   actor → role (desa_adat, kec, kab, opd, pol, gvt, etc.)
│ confidence        │   enum mapping authority ordering (from dissertation)
└───────────────────┘
┌── geography ──────┐
│ kabupaten         │   enum-like 9 rows  (gianyar…jembrana + denpasar)
│ kecamatan         │   child of kabupaten, polygon
│ desa_adat         │   customary village
│ banjar            │   canonical atom; nanoid slug bjr-<kab3>-<NNNN>
│ banjar_alias      │   CNAMEs of the banjar slug, owned by banjar.id
│ pura              │   temples; parent_pura_class (kahyangan_tiga etc.)
│ road_edge         │   OSM way → edge; line geometry
└───────────────────┘
┌── event core ──────┐
│ event             │   canonical ceremonial event
│ event_state       │   predicted → confirmed → active → finished → cancelled
│ event_class       │   enum (piodalan, melasti, ngaben, pelebon, parade, ...)
│ event_temporal    │   predicted_window, confirmed_window, actual_window
│                    │   (tstzrange fields, exclusion constraints)
│ event_geometry    │   point / route / polygon / multi
│ event_impact      │   ↔ road_edge M:N, with effect_class + penalty_factor
│ event_source      │   ↔ actor (author)
│ event_provenance  │   authority tier, signature, evidence payload
│ event_transition  │   append-only audit log of every state change
└───────────────────┘
┌── calendar engine ─┐
│ calendar_ruleset  │   ruleset_id, source, version, generated_at
│ calendar_event    │   wuku, wewaran, sasih, rahinan, etc. computed
│ calendar_audit    │   raw lontar reference per inferred rule
└───────────────────┘
┌── evidence / files ┐
│ evidence_blob     │   minio object key + sha256 + media_type
│ evidence_url      │   public read via cloudflare-fronted minio
└───────────────────┘
┌── per-pura csv ──┐
│ (publikasi) just SELECTs from the above; no separate table
└───────────────────┘
```

All tables `tstzrange` for windows and `revision` columns for lineage. Indices:
- `event_geometry USING GIST (geom)`
- `event_impact USING GIST (edge_geom)`
- `event_temporal USING GIST (predicted_window)` for active-window lookups
- partial unique on `(slug)` where `record_type='banjar'` to enforce canonicity

### 3.1 the four-level fact distinction (modeled into schema)

| level | source | mutable | example |
|---|---|---|---|
| **computed** | calendar_ruleset + row at predict time | recomputed on ruleset bump | wuku position |
| **registered** | desa_adat submission | mutable but lineage-locked | confirmed piodalan date |
| **predicted** | computed → registered pipeline | cached | derived from registered |
| **operational** | pecalang / whatsapp → verified human | append-only | road close right now |

Schema enforces: every `event.id` has at least one row in each of `event_source`, `event_provenance`, and (eventually) `event_verification`. The verification row is typed and the system distinguishes `unverified_report` vs `verified_by_human` vs `algorithm_inference`.

## 4. API surface (DSP v0.1)

```
GET    /dsp/v0.1/openapi.json
GET    /dsp/v0.1/events
GET    /dsp/v0.1/events/{id}
POST   /dsp/v0.1/events                  (operator auth)
PATCH  /dsp/v0.1/events/{id}/state       (state transition, audit row)
GET    /dsp/v0.1/calendar/{date}
GET    /dsp/v0.1/calendar/{date}/rahinan
GET    /dsp/v0.1/calendar/predict/piodalan?pura_id=&years=
GET    /dsp/v0.1/impact/near?lat=&lon=&radius_m=
GET    /dsp/v0.1/intersect?edge_id=
GET    /dsp/v0.1/publications/feed.geojson
GET    /dsp/v0.1/publications/feed.gtfs-rt
GET    /dsp/v0.1/publications/feed.datex2
GET    /dsp/v0.1/dataset/{YYYY-MM-DD}.tar.zst      (snapshot)
GET    /dsp/v0.1/dataset/{YYYY-MM-DD}.tar.zst.sig  (age signature)
HEAD   /dsp/v0.1/well-known/dewata-signing-key.txt

# operator-only (cloudflare-access-gated)
POST   /dsp/v0.1/internal/event/draft
POST   /dsp/v0.1/internal/event/{id}/verify
POST   /dsp/v0.1/internal/event/{id}/transition

# whatsapp webhook
POST   /dsp/v0.1/webhook/whatsapp        (signed by whatsapp x-hub signature)
```

Versioned URL prefix `v0.1` pins spec stability. Any breaking change → `v0.2` parallel run for 6 months.

## 5. Frontend (map.dewata.org, next.js 14 app router)

```
src/app
├── (public)
│    ├── page.tsx                       landing
│    ├── map/
│    │    ├── page.tsx                  MapLibre PWA
│    │    └── client.tsx                island
│    ├── calendar/page.tsx              Balinese calendar view
│    ├── datasets/page.tsx              download signed snapshots
│    └── protocol/page.tsx              link out to protocol.dewata.org
├── (operator)                         behind cloudflare-access
│    ├── intake/page.tsx                AI-assisted draft creator
│    ├── queue/page.tsx                 pecalang pending reports
│    └── events/page.tsx                CRUD for active events
└── (admin)
     └── revisions/page.tsx             diff viewer

src/components
├── maplibre/
│   ├── MapCanvas.tsx
│   ├── RouteDrawer.tsx
│   ├── EventCard.tsx
│   └── PWAInstallPrompt.tsx
├── i18n/                               id, en, balinese
└── data/
     └── dsp-client.ts                  generated from openapi.json
```

Tech:
- **next.js 14** app router (RSC + islands)
- **maplibre-gl** with vector tiles from `tiles.dewata.org` (carton's free tier for v1; own PM tiles later)
- **@tanstack/react-query** for cache invalidation
- **Zod** for runtime validation of every DSP payload
- **pwa** via `next-pwa-plugin`, offline tile cache, install prompt
- **i18n** via `next-intl`, routes split `/id/*`, `/en/*`, `/ban/*` (Balinese romanised + script toggle)

## 6. Calendar engine (`/opt/dewata.online/calendar/`)

Pure Python first. Rust later. The interface is a stable python module:

```
dewatacalendar/
├── __init__.py
├── pawukon.py                  # 210-day cycle, 10 concurrent cycles
├── saka.py                     # lunisolar, nampih sasih
├── wewaran.py                  # Eka-Dasa Wara + Pengalantaka + Jejepan
├── rahinan.py                  # named holiday enums
├── rulesets/
│   ├── v0.4.1.toml             # frozen ruleset
│   └── v0.4.2.toml             # pending
├── exceptions.py
└── cli.py                      # `python -m dewatacalendar test` + `date YYYY-MM-DD`

tests/conformance/
├── pawukon-vectors.json        # 30,000 dates
├── saka-vectors.json           # 100,000 dates
├── wewaran-vectors.json        # 100,000 dates
├── rahinan-vectors.json        # 5,000 cases
└── integration-vectors.json    # 5,000 cross-checked against published calendars
```

The **conformance corpus** is the centerpiece. Three sources feed it:
1. published saka/pawukon calendar conversions (monthly editions)
2. Cunningham's reconstructed chronology (academic, freely cited)
3. Igarashi's lunisolar chronological tables

Every ruleset version is reproducible; tests must pass *all three* sources.

## 7. Auth model

Two layers, both operator-gated, both bound to dewata actors:

1. **Web (next.js)** — Cloudflare-Access one-time-pin by SMS or email for operator roles; bearer JWT to DSP API. Public read APIs are unauth.
2. **DSP API (fastapi)** — JWT bearer for operator endpoints. Public read endpoints are unauth; rate-limited at the Caddy layer.

Roles (mirror the dissertation's authority ordering):

```
dewata:admin                 operator staff
dewata:editor                trained operator
dewata:pecalang              verified pecalang coordinator (with phone OTP)
dewata:desa_adat             representative (federated; their realm)
dewata:public                anonymous
```

Each event source row carries the role used to author it. Conflict resolution uses the authority ordering.

## 8. Snapshot publication pipeline

Daily at `02:00 WITA`:

1. `dewata-snapshots snapshot today`
   - emits `tar.zst` of every `event` + `event_state` + `event_geometry` + `road_edge` (whole)
   - emits `meta.json` with sha256 of every file
2. `dewata-snapshots sign today`
   - signs `.tar.zst` with age secret from `/root/.env.dewata.online`
   - emits `.tar.zst.sig`
3. `dewata-snapshots publish today`
   - uploads to `datasets.dewata.org` (cloudflare-fronted minio or static bucket)
   - mirrors to **mempalace.gh** (github commits)
   - mirrors to **mastodon account** (status post with hash only)

The mirror pattern means **one failure mode deletes one copy, not the project.**

## 9. Routing plugins

Three engines, three plugins:

| engine | language | hook |
|---|---|---|
| **OSRM** | C++/Lua | `--custom-lua-script dewata_cb.lua`, edge penalty in `way_handler` |
| **Valhalla** | C++ | python middleware for `route` cost-matrix rewrite |
| **GraphHopper** | Java | custom weighting factor class |

All three plugins consume the same DSP `/impact/near` API and emit the same output JSON. A consumer picking any of them gets equivalent behaviour for our closures.

## 10. Bilateral: whatsapp/pecalang integration

```
phone-bridge container
   ├── whatsapp business cloud api webhook receiver
   │     - HTTPS, posts to /dsp/v0.1/webhook/whatsapp
   ├── indonesian-trained intent classifier (Qwen3 1.7B or sunda-llm)
   ├── OSM nominatim fallback for "Pura X"
   └── idempotency ledger (postgres)
       - record all transitions 60s window
```

Twinned: every published event has a `source_phone` integer in `actor.phone_id`, every transition has the same `phone_id` and a hash of the message.

## 11. Edge / Cloudflare

- zone `dewata.org`, free plan, wildcard cert one-click
- records:
  - `A dewata.org → 62.72.7.218` (proxy off for now; flip on once content live)
  - `A *.dewata.org → 62.72.7.218` (only if wildcard dns is reachable)
    Actually: use explicit CNAMEs from cloudflare API one by one — sub-records can be added by my `dewata-dns` cli
- Cloudflare Access application for `*.dewata.org/operator/*` using one-time-pin
- WAF rule: block non-cloudflare IPs at the network edge (zero trust)
- caching rules: `/datasets/*` 7d, `/protocol/*` 1h, `/publications/*` 60s

## 12. Operations & maintenance

- **systemd unit per container** registered as `dewata-api.service`, `dewata-web.service`, etc.
- **logs**: vectorio to `/var/log/dewata/*.log` (rotation max 5 × 100MB)
- **metrics**: `/metrics` prometheus endpoint per service, scraped by host-level prom
- **backup**: nightly `pg_dump` + `bbr` snapshot to remote (`b2:dewata-prod/`); climate-confirmed weekly
- **disaster recovery**: cloud-init AMIs for re-launch, terraform-of-choice for state

## 13. Roadmap v0.1 → v0.2 → v1

| phase | deliverable | target |
|---|---|---|
| **0** | the schema, calendar engine skeleton, one DSP endpoint | 2 weeks |
| **1** | calendar engine with 50k vector corpus | 4 weeks |
| **2** | operator PWA + AI-assisted intake | 6 weeks |
| **3** | whatsapp bridge | 8 weeks |
| **4** | first gianyar pilot; one trusted loop published | 12 weeks |
| **5** | OSRM/Valhalla plugins | 16 weeks |
| **6** | public GA on map.dewata.org | 20 weeks |

Every gate has a measurable acceptance criterion.

## 14. What gets built first — exec order (paste-ready, no scope creep)

```
1. ssh user 'dewata' (systemd-dynamic), working dir /opt/dewata.online
2. docker-compose dewata stack at /opt/dewata.online/deploy/
3. alembic migrations for schema above
4. fastapi DSP endpoint with auth, calendar engine proxy, event CRUD
5. docusaurus spec at protocol.dewata.org
6. next.js public map at map.dewata.org
7. caddy front-end bringup
8. cloudflare NS delegation
9. snapshot signing + daily publication
10. operator PWA
```

## 15. Failure modes we explicitly design around

| failure | mitigation |
|---|---|
| postgres dies | shared-postgres is the only stateful thing we depend on; replicated by network backup; restore path is verified weekly |
| caddy misroutes | dewata-internal caddy is independent; reload is via `docker compose restart` on the stack only |
| token leakage | one cli (`dewata-load-creds`) holds the secret *in process memory only*; rotation runs as a cron |
| operator forgets state transition | whatsapp idempotency rule sends a `masih aktif?` SMS at 04h boundary |
| calendar engine drift | ruleset version bump forces the calendar engine to re-pass the corpus; CI blocks the merge if any vector fails |
| snapshot signature expiring | age keys are valid for the full ttl (no expiry built in); revocation is a separate list file |
| cleavage between banjar data and mapa | once we have ANY verified banjar row, the whole registry is reproducible; we never overwrite a row, only add revisions |

## 16. What does NOT ship in v0.1 (anti-scope)

- Music/photo (separate wysiwyg microapps)
- AI-generated text content (separate mini service)
- Daily email newsletter (later phase)
- OSM import full Bali island (one kecamatan at a time)
- 5 separate DSP consumers (only the anchor consumer ships; webhooks for the rest later)

## 17. Risks & open questions

1. **postgis version drift**: postgis 3.4 vs postgis 3.5 once-pinned. accept 3.4 for the lifecycle of v0.1, bump in v0.2.
2. **cloudflare account lockout**: mitigated by `namecheap'ish` mirror zone in case cloudflare has an outage — we don't add cloudflare as primary registrar.
3. **shared-postgres container death**: the container is on host network namespace via `127.0.0.1`. host restart will likely drop it; supervisor + auto-restart policy is required.
4. **dns ttl on `*.dewata.org`**: 60s before wildcard is broken; 1h after; documented in runbook.
5. **regions**: postgis ST_Transform to 32750 (UTM zone 50S, which covers Bali) is mandatory for accurate metric operations.

## 18. Repo & branches

```
/opt/dewata.online (git)
   main              — production
   phase-1           — calendar engine work
   phase-2           — operator
   phase-3           — public map
   feature/*         — short-lived
   draft/*           — anything from anyone

branches never auto-merge to main. main gates are:
   - alembic migration ran locally
   - conformance vectors 100% pass
   - openapi schema unchanged OR has matching migration
   - signed snapshot today exists
```

ready for next step. y/pivot-to-C? y/scaffold? y/add-infra-runs? your call.
