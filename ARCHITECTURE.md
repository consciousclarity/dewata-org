# Architecture — full engineering plan

> scope = adat & customary practice, **not** tourism & navigation.
> for v0.1 dewata is a bali-sovereign protocol for recording, certifying,
> and preserving customary ceremony and cultural record. see [[Concept]]
> and [[Roadmap]].

## TL;DR

Dewata runs as a **modular monolith** in a single docker-compose stack on the existing `62.72.7.218` vps. Six reverse-proxied surface hosts behind cloudflare edge. PostgreSQL 16 + PostGIS 3.4 reused from the existing `shared-postgres` container. Calendar engine is a deterministic Python package with a Rust-rewrite path designed in but not paid for until spec v1 ships.

the spec is built around five **adat** primitives: *piodalan*, *odalan*, *ngayah*, *paruman*, *pecalang-coverage*. the **root categories** of the protocol are these, not navigation.

---

## 0. scope

**in scope**:
- banjar, pura, desa adat identity & registry
- piodalan / odalan prediction + recording
- calendar engine (pawukon, saka, wewaran, rahinan)
- signed cultural streams per banjar / pura
- mirror-redundant cultural archive
- offline-indonesian + bali language interfaces
- USSD / voice hotline for elders without smartphones
- pemangku + bendesa authority ordering

**out of scope** (will not ship in v0.1):
- tourism map layer (no "what's open" feature for visitors)
- routing engines (osrm / valhalla / graphhopper)
- hotel concierge / tour operator integrations
- travel agencies, navigation providers, "tourist-friendly" APIs
- card-matching / way-finding UX
- payment for adat-reciprocation services
- location-aware advertising of any kind

the protocol is for **bali institutions and cultural observers**. visitors are welcome to read the public tier; they are not the audience.

---

## 1. Layered layout

```
┌────────────────────────────────────────────────────────────────────┐
│ Cloudflare edge                                                   │
│   *.dewata.org    one-click-wildcard-TLS   edge-cache / rate-limit │
│   Cloudflare Access at api.reg / cert / well-known for operator   │
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
┌──────────────┬─────────────┬───────────────┬──────────────┬──────────────┐
│ dewata.org   │ api.        │ bci.          │ datasets.    │ protocol.    │
│ static land- │ fastapi     │ next.js       │ static       │ docusaurus   │
│ ing          │ (DSP)       │ custom+maplbr │ signed tar   │ spec site    │
│ static next  │ openapi     │ ceremony view │ + age sigs   │              │
│ export       │ calendar    │ no tourism UX │             │              │
│              │ banjar      │               │             │              │
└──────────────┴─────────────┴───────────────┴──────────────┴──────────────┘
        │
        └──── subdomains: <id>.<kab>.dewata.org → static SSG per banjar / per pura
                                 (NOT for navigation; for cultural profile pages)

                          (static dataset snapshot, signed)
              datasets.dewata.org → github pages static  (mirror, never reachable from VIP)
```

five surface hosts + apex static landing + an unbounded set of `<id>.<kab>.` records. total: **1 caddy block** + **1 wildcard TLS cert** + **1 wildcard DNS record**.

**surface host renaming** (this version):

| old | new | why |
|---|---|---|
| `map.dewata.org` | `bci.dewata.org` (Bali Cultural Index) | avoid "map" = tourists |
| `data.dewata.org` | `datasets.dewata.org` | +1 char, more explicit |
| `api.dewata.org` | `api.dewata.org` (unchanged) | fine |

---

## 2. Container topology

```
shared-network (host, existing)
   ├── shared-postgres (postgis/postgis:16-3.4) ──── shared
   ├── dify-redis (redis:6-alpine)               ──── shared
   └── dewata stack ──┐
       ├── api       (python 3.12 + uvicorn, port 8000)
       ├── worker    (arq / dramatiq, port 8000, no listener)
       ├── bci       (next 14, port 3000)   ← was `web`
       ├── protocol  (docusaurus, port 4001)
       ├── datasets  (static, port 3001)
       └── caddy     (per-stack reverse proxy, port 8080 → 80/443)
```

caddy inside the dewata stack stays isolated from the host-level caddy. the host caddy sends `*.dewata.org` traffic to the **dewata caddy** at `127.0.0.1:8080`. single ingress entry, internal fan-out.

why a nested caddy:
- each project keeps its own Caddyfile, deployable independently
- no root-level nginx reload needed for every dewata config change
- cloudflare is the only edge facing the world; this caddy only sees cache-misses

---

## 3. Database design (PostGIS)

```
┌── core identity ────────────┐
│ actor                       │   user / institution / phone
│                             │     / pemangku / pecalang / klian / bendesa
│ actor_role                  │   actor → role
│                             │     (desa_adat, kec, kab, pemangku, pecalang,
│                             │      klian_adat, bendesa, opd, pol, gvt)
│ confidence                  │   enum mapping the authority ordering
│ authority_chain             │   signed delegation chain (pemangku→bendesa→banjar→desa)
└─────────────────────────────┘
┌── geography ────────────────┐
│ kabupaten                   │   9 rows + denpasar (bali-only)
│ kecamatan                   │   child of kabupaten
│ desa_adat                   │   customary village (≠ kelurahan)
│ desa_dinas                  │   administrative village
│ banjar                      │   canonical atom; nanoid bjr-<kab3>-<NNNN>
│ banjar_alias                │   CNAMEs of the banjar slug
│ pura                        │   temples; parent_pura_class
│ pura_relationship           │   pura.parent_pura_class → kahyangan_tiga, sad_kahyangan, etc.
│ path_segment                │   ceremonial procession path (geometry)
└─────────────────────────────┘
┌── cultural core ────────────┐
│ ceremony_class              │   enum: piodalan, odalan_utama, odalan_madya,
│                             │         melasti, ngaben, pelebon, ngiring,
│                             │         tumpek_*, upaca_rajah, paruman,
│                             │         kerama, mabisu, metatah, mecukur
│ ceremony                    │   canonical ceremonial event
│ ceremony_state              │   predicted → announced → confirmed
│                             │     → occurring → completed → cancelled
│ ceremony_temporal           │   predicted_window, confirmed_window, actual_window
│                             │   (tstzrange fields, exclusion constraints)
│ ceremony_geometry           │   point / route / polygon / multi
│ ceremony_source             │   ↔ actor (the customary authority that records it)
│ ceremony_provenance         │   authority chain, signatures, evidence refs
│ ceremony_transition         │   append-only audit log of every state change
│ ceremony_obligation         │   ngayah assignment table (who owes what when)
└─────────────────────────────┘
┌── calendar engine ──────────┐
│ calendar_ruleset            │   ruleset_id, source, version, generated_at
│ calendar_event              │   wuku, wewaran, sasih, rahinan computed
│ calendar_audit              │   raw lontar reference per inferred rule
└─────────────────────────────┘
┌── evidence ─────────────────┐
│ evidence_blob               │   minio object key + sha256 + media_type
│ evidence_url                │   public read via cloudflare-fronted minio
│ evidence_visibility         │   per-evidence visibility tier
└─────────────────────────────┘
```

all tables `tstzrange` for windows and `revision` columns for lineage. indices:
- `ceremony_geometry USING GIST (geom)`
- `path_segment USING GIST (segment_geom)`
- `ceremony_temporal USING GIST (predicted_window)`
- partial unique on `(slug)` where `record_type='banjar'` to enforce canonicity

### 3.1 the four-level fact distinction (modeled into schema)

| level | source | mutable | example |
|---|---|---|---|
| **computed** | calendar_ruleset + row at predict time | recomputed on ruleset bump | wuku position |
| **registered** | bendesa adat submission | mutable but lineage-locked | confirmed piodalan date |
| **predicted** | computed → registered pipeline | cached | derived from registered |
| **operational** | pemangku / pecalang verified human | append-only | ceremony currently underway |

schema enforces: every `ceremony.id` has at least one row in each of `ceremony_source`, `ceremony_provenance`, and `ceremony_transition`. the transition row is typed and the system distinguishes `unverified_report` vs `verified_by_human` vs `algorithm_inference`.

### 3.2 visibility tier system (cultural sovereignty)

every record carries one of these tiers, with default `banjar`:

| tier | audience | example |
|---|---|---|
| `public` | world | "piodalan utama pura saraswati on 23 sep, public observance" |
| `banjar` (default) | banjar members | "pemangku keramas conducting brata" |
| `desa_adat` | customary village | "paruman vote — bendesa resolution 12" |
| `restricted` | family / pemangku | "ngaben family — name list" |
| `private` | single actor | self-reference, drafts, drafts-of-drafts |

**the platform NEVER promotes a record to higher visibility than its source actor declared.** mirror partners and consumers see only the tier they subscribed to. an `restricted` event is invisible to all visibility-sublevels except explicit `restricted` subscribers.

---

## 4. API surface (DSP v0.1)

### 4.1 read endpoints (public, rate-limited)

```
GET    /dsp/v0.1/openapi.json
GET    /dsp/v0.1/ceremonies
GET    /dsp/v0.1/ceremonies/{id}
GET    /dsp/v0.1/banjar/{slug}
GET    /dsp/v0.1/pura/{slug}
GET    /dsp/v0.1/desa-adat/{slug}
GET    /dsp/v0.1/calendar/{date}
GET    /dsp/v0.1/calendar/{date}/rahinan
GET    /dsp/v0.1/calendar/predict/piodalan?pura_id=&years=
GET    /dsp/v0.1/calendar/predict/odalan?pura_id=
GET    /dsp/v0.1/visibility/tiers                 # tier system reference

GET    /dsp/v0.1/publications/feed.geojson
GET    /dsp/v0.1/publications/feed.jsonl-signed
GET    /dsp/v0.1/publications/discovery/{kab}.json
GET    /dsp/v0.1/dataset/{YYYY-MM-DD}.tar.zst
GET    /dsp/v0.1/dataset/{YYYY-MM-DD}.tar.zst.sig
HEAD   /dsp/v0.1/well-known/dewata-signing-key.txt

GET    /dsp/v0.1/mesh/peers
GET    /dsp/v0.1/mesh/peer/{banjar_id}
```

### 4.2 write endpoints (operator-grade auth)

```
POST   /dsp/v0.1/ceremonies                          (pemangku + bendesa + banjar)
PATCH  /dsp/v0.1/ceremonies/{id}/state               (signed transition)
POST   /dsp/v0.1/banjar/{slug}/manifest               (signed manifest publish)
POST   /dsp/v0.1/banjar/{slug}/mirror                 (mirror subscription)

# banjar-internal (mesh)
POST   /dsp/v0.1/mesh/peers                          (peer sign-up)
POST   /dsp/v0.1/mesh/heartbeat                      (signed keepalive)
POST   /dsp/v0.1/webhook/whatsapp                    (signed by whatsapp x-hub)
```

versioned URL prefix `v0.1` pins spec stability. any breaking change → `v0.2` parallel run for 6 months.

### 4.3 explicitly dropped from v0.1

```
- /dsp/v0.1/impact/near?lat=&lon=&radius_m=        # navigation feature
- /dsp/v0.1/intersect?edge_id=                    # navigation feature
- /dsp/v0.1/publications/feed.gtfs-rt              # transit
- /dsp/v0.1/publications/feed.datex2               # road-traffic-mgmt DATEX
- /dsp/v0.1/wallet/pass                            # apple/google wallet
- /dsp/v0.1/notify/subscribe                       # webpush
```

these may revive in v0.2+ if a banjar explicitly requests them. absence in v0.1 is intentional.

---

## 5. Frontend (`bci.dewata.org`, next.js 14 app router)

### 5.1 routes

```
src/app
├── (public)
│    ├── page.tsx                       landing (bali-language first, id second)
│    ├── calendar/page.tsx              Balinese calendar — wuku, wewaran, rahinan
│    ├── banjar/page.tsx                banjar index (read-only)
│    ├── banjar/[kab]/[slug]/page.tsx   per-banjar cultural profile
│    ├── pura/[kab]/[slug]/page.tsx     per-pura cultural profile
│    ├── datasets/page.tsx              download signed snapshots
│    └── protocol/page.tsx              link to protocol.dewata.org
├── (operator)                         behind cloudflare-access
│    ├── intake/page.tsx                AI-assisted draft creator for bendesa
│    ├── queue/page.tsx                 pemangku pending reports
│    ├── ceremony/page.tsx              CRUD for ceremonies
│    └── audit/page.tsx                 lineage / audit log
└── (admin)
     └── reconciliation/page.tsx        mirror-chain reconciliation tools

src/components
├── calendar/
│   ├── WukuWheel.tsx
│   └── WewaranMatrix.tsx
├── cultural/
│   ├── CeremonyCard.tsx
│   ├── BanjarProfile.tsx
│   └── PuraProfile.tsx
├── i18n/                               id, ban (balinese), en (collator-priority)
└── data/
     └── dsp-client.ts                  generated from openapi.json
```

### 5.2 tech

- **next.js 14** app router (RSC + islands)
- **maplibre-gl** is used **only** for ceremony-trail-path visualisation in `bci.dewata.org/pura/.../ceremonies`. no routing-engine integration. no "directions to" anywhere in code.
- **@tanstack/react-query** for cache invalidation
- **Zod** for runtime validation of every DSP payload
- **pwa** via `next-pwa-plugin`, offline tile cache, install prompt
- **i18n** via `next-intl`. default route is **`/ban/`** (balinese romanised + script toggle). Indonesian second. English third if present.

### 5.3 explicit anti-features

- ❌ no "directions from X to Pura Y" anywhere
- ❌ no "current road closures due to ceremony" UX (ceremony record is public; consequences are emergent, not editorial)
- ❌ no "best of bali this week" hero
- ❌ no tour booking anywhere

---

## 6. Calendar engine (`/opt/dewata.online/phase-1/src/dewatacalendar/`)

✓ phase 1 shipped. see `[[phase1.engine_release_0.1]]` for status.

pure Python first. Rust later. the interface is a stable python module:

```
dewatacalendar/
├── __init__.py
├── pawukon.py                  # 210-day cycle, 10 concurrent cycles
├── saka.py                     # lunisolar, nampih sasih
├── wewaran.py                  # Eka-Dasa Wara + Pengalantaka + Jejepan
├── rahinan.py                  # named ceremony enums
├── rulesets/
│   └── v0.1.toml               # frozen ruleset
├── exceptions.py
└── cli.py
```

the **conformance corpus** is the centerpiece. three sources feed it:

1. published saka/pawukon calendar conversions (monthly editions)
2. Cunningham's reconstructed chronology (academic, freely cited)
3. Igarashi's lunisolar chronological tables

every ruleset version is reproducible; tests must pass *all three* sources. currently 75,608 generated vectors and 27k spot-checked at high confidence.

---

## 7. Auth model

two layers, both bound to dewata actors:

1. **Web (next.js)** — Cloudflare-Access one-time-pin by SMS or email for operator roles; bearer JWT to DSP API. Public read APIs are unauth.
2. **DSP API (fastapi)** — JWT bearer for operator endpoints. Public read endpoints are unauth; rate-limited at the caddy layer.

### 7.1 roles (mirror the dissertation's authority ordering)

```
dewata:admin                 operator staff
dewata:editor                trained banjar operator
dewata:bendesa               bendesa adat representative
dewata:pemangku              temple pemangku (signed-credential issuance)
dewata:klian_adat            banjar klian / customary head
dewata:pecalang              verified pecalang coordinator (phone OTP)
dewata:desa_adat             customarily-delegated
dewata:public                anonymous
```

each ceremony source row carries the role used to author it. conflict resolution uses the authority ordering; the **most senior valid signature wins**.

### 7.2 actor-onboarding principle

**no one authorises a record unless their authority chain is signed.** signing identity is bound to:
- an SMS-verified phone number (pemangku, klian, pecalang)
- an SMS-verified + government-ID verified number (bendesa, opd delegates)
- a hardware-token-bound certificate (admin / pemangku of major pura)

this is heavier than typical "email + password" but appropriate for cultural work where signing carries civic weight.

---

## 8. Snapshot publication pipeline

daily at `02:00 WITA`:

1. `dewata-snapshots snapshot today`
   - emits `tar.zst` of every `ceremony` + `ceremony_state` + `ceremony_geometry` + `path_segment`
2. `dewata-snapshots sign today`
   - signs `.tar.zst` with age secret from `/root/.env.dewata.online`
   - emits `.tar.zst.sig`
3. `dewata-snapshots publish today`
   - uploads to `datasets.dewata.org` (cloudflare-fronted minio or static bucket)
   - mirrors to **mempalace.gh** (github commits)
   - mirrors to **mastodon account** (status post with hash only)

the mirror pattern means **one failure mode deletes one copy, not the project.**

---

## 9. Cultural federation layer (the "mesh")

a mesh is the **federation pattern** where data is owned by signing banjars, not by dewata:

```
banjar-X.kab.dwata.org → signed SSE feed
banjar-Y.kab.dwata.org → signed SSE feed
pura-Z.kab.dwata.org   → signed SSE feed
                           │
                           ▼
                    dewata.org (index only)
                           │
                           ▼
                    mirror chain (Bali cultural archives)
```

each banjar:
- publishes its own signed cultural records via SSE
- subscribes to at least one mirror partner (signing constraint: **must** declare at least one mirror)
- is discoverable via `bci.dewata.org/<kab>/<slug>`

the platform **certifies** signed records, does not own them. if dewata.org is unreachable, banjars continue; if a banjar is offline, its mirror partner remains.

---

## 10. Bilateral: whatsapp/pemangku integration (adat-first)

```
phone-bridge container
   ├── whatsapp business cloud api webhook receiver
   │     - HTTPS, posts to /dsp/v0.1/webhook/whatsapp
   ├── indonesian-trained intent classifier (Qwen3 1.7B)
   ├── id-nlp + balinese-trained dictionary fallback
   ├── pencocokan geometri sederhana (path/postal lookup, NO routing)
   └── idempotency ledger (postgres)
       - record all transitions 60s window
```

twinned: every published ceremony has a `source_phone` integer in `actor.phone_id`, every transition has the same `phone_id` and a hash of the message.

**anti-feature removed**: OSM nominatim was used for routing; we replace with **geographic lookup by postal code + desa adat** which is the culturally-appropriate addressing layer. whether a street passes through a ceremonial path is *not* the system's authority.

### 10.1 SMS / USSD for elders without smartphones

```
tel *888*xxxx# → "press 1 for ceremonies affecting your banjar this week"
             → "press 2 to confirm tomorrow's paruman"
             → "press 3 to record a ngaben in your family"
```

backed by indosat / telkomsel USSD shortcode. cheap, no app, voice-callable.

---

## 11. Edge / Cloudflare

- zone `dewata.org`, free plan, wildcard cert one-click
- records:
  - `A dewata.org → 62.72.7.218` (proxy off for now; flip on once content live)
  - `A api.dewata.org → 62.72.7.218`
  - `A bci.dewata.org → 62.72.7.218`
  - `A datasets.dewata.org → 62.72.7.218`
  - `A protocol.dewata.org → 62.72.7.218`
  - per-banjar / per-pura CNAMEs added via `dewata-dns`
- **Cloudflare Access** application for `*.dewata.org/operator/*` using one-time-pin
- WAF rule: block non-cloudflare IPs at the network edge (zero trust)
- caching rules: `/datasets/*` 7d, `/protocol/*` 1h, `/publications/*` 60s
- **NO cloudflare-routing marketing**; no `<banjar>.kab.dwata.org` GeoJSON optimisation beyond `Cache-Control: public, max-age=600, immutable`

---

## 12. Operations & maintenance

- **systemd unit per container** registered as `dewata-api.service`, `dewata-bci.service`, etc.
- **logs**: to `/var/log/dewata/*.log` (rotation max 5 × 100MB)
- **metrics**: `/metrics` prometheus endpoint per service, scraped by host-level prom
- **backup**: nightly `pg_dump` + archive snapshot to remote (`b2:dewata-prod/`); climate-confirmed weekly
- **disaster recovery**: docker-compose templates; rotation runbooks; mirror-chain guides

---

## 13. Roadmap v0.1 → v0.2 → v1

| phase | deliverable | target |
|---|---|---|
| **0** | schema, calendar engine skeleton, one DSP endpoint | 2 weeks |
| **1** | calendar engine with 50k vector corpus | 4 weeks — **shipped** |
| **2** | banjar / pura identity model | 6 weeks |
| **3** | ceremony CRUD + visibility tier system | 8 weeks |
| **4** | first gianyar pilot; one trusted loop published | 12 weeks |
| **5** | mesh sse feeds + mirror subscriptions | 16 weeks |
| **6** | whatsapp bridge | 20 weeks |
| **7** | USSD hotline | 26 weeks |
| **8** | time-machine cultural archive publication | 32 weeks |
| **9** | island-wide federation | year 2 |

every gate has a measurable acceptance criterion. the mesh is **explicitly the v0.2+ framing**, not v0.1.

---

## 14. What gets built first — exec order

```
 1. ssh user 'dewata' (systemd-dynamic), working dir /opt/dewata.online
 2. docker-compose dewata stack at /opt/dewata.online/deploy/
 3. alembic migrations for the schema above
 4. fastapi DSP endpoint with auth, calendar engine proxy, ceremony CRUD
 5. docusaurus spec at protocol.dewata.org (cultural-protocol section)
 6. next.js public app at bci.dewata.org (no tourism framing)
 7. caddy front-end bringup
 8. cloudflare NS delegation
 9. snapshot signing + daily publication
10. operator console (no tourism, no card UX)
```

---

## 15. Failure modes we explicitly design around

| failure | mitigation |
|---|---|
| postgres dies | shared-postgres is the only stateful thing we depend on; replicated by network backup; restore path is verified weekly |
| caddy misroutes | dewata-internal caddy is independent; reload is via `docker compose restart` on the stack only |
| token leakage | one cli (`dewata-load-creds`) holds the secret *in process memory only*; rotation runs as a cron |
| pemangku forgets state transition | whatsapp idempotency rule sends a `masih aktif?` sms at 4h boundary (customary-finality prompt) |
| calendar engine drift | ruleset version bump forces the calendar engine to re-pass the corpus; CI blocks the merge if any vector fails |
| snapshot signature expiring | age keys are valid for the full ttl (no expiry built in); revocation is a separate list file |
| mirror partner outage | mesh requires at least one mirror declared per banjar; banjar itself becomes the fallback |
| cultural-sensitivity slip | every release goes through indonesian + bali-speaking reviewer who is not part of dewata |

---

## 16. What does NOT ship in v0.1 (anti-scope)

- any tourism features: maps, "near me" features, recommendations
- routing engines: OSRM, Valhalla, GraphHopper
- transit feeds: GTFS-rt, DATEX II
- hotel concierge / bot integrations: whatsappBusiness for hotels is OUT
- ngaben wedding scheduling as a product feature: couples can use the platform to author events, but the platform doesn't recommend
- payment integration
- ad-supported anything
- "ceremony of the day" galleries
- hanacaraka keyboard UI
- pandoc-driven html-from-docx for ceremonial texts (separate project)

---

## 17. Risks & open questions

1. **postgis version drift**: postgis 3.4 vs postgis 3.5 once-pinned. accept 3.4 for the lifecycle of v0.1, bump in v0.2.
2. **cloudflare account lockout**: mitigated by switching to a `namecheap`/spaceship mirror zone if cloudflare has an outage — we don't add cloudflare as primary registrar.
3. **shared-postgres container death**: the container is on host network namespace via `127.0.0.1`. host restart will likely drop it; supervisor + auto-restart policy is required.
4. **dns ttl on `*.dewata.org`**: 60s before wildcard is broken; 1h after; documented in runbook.
5. **regions**: postgis ST_Transform to 32750 (UTM zone 50S, which covers bali) is mandatory for accurate metric operations.
6. **cultural protocol drift**: changes to the way customary ceremony is recorded should never cause rupture in the time-machine. we use *append-only* with revisions.
7. **mirror-cooperation selection**: which pairs of banjars serve as each other's mirror is a *social* question, not technical. proceed cautiously in v0.2.
8. **pemangku Keramas class of data**: some sacred information requires stricter handling than `restricted`. designed as `pemangku-private` in v0.2.

---

## 18. Repo & branches

```
/opt/dewata.online (git)
   main              — production
   phase-1           — calendar engine work — complete
   phase-2           — banjar / pura / ceremony
   phase-3           — cultural mesh
   feature/*         — short-lived
   draft/*           — anything from anyone

branches never auto-merge to main. main gates:
   - alembic migration ran locally
   - conformance vectors 100% pass
   - openapi schema unchanged OR has matching migration
   - signed snapshot today exists
   - indonesian + bali-language strings present (no en-only UX)
```

**scope is culture-first.** anything that smells like navigation, tourism, or "what to do today" — out.
