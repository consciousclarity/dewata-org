# dewata.org — complete use-case inventory

Sources: `ARCHITECTURE.md` (§0, 3.1, 3.2, 4.1, 4.2, 4.3, 5.1, 7.1, 7.2, 8, 9, 10, 10.1, 16),
`docs/PROTOCOL.md`, `registry/*.tsv`, `phase-1/src/`, `wiki/`.
Verified against `main` @ `f675b28`, 2026-09-21.

## Why this covers more than a running-code inventory

An inventory drawn from what is **live** comes out read-only: a calendar engine, a
wiki, and two registry files. That yields a read-heavy list with almost nothing on
the write side.

But dewata.org is specified as a system for **recording and certifying** customary
record. Writing is the product; reading is how the record gets back out. `ARCHITECTURE.md
§0` puts "piodalan / odalan prediction **+ recording**", "signed cultural streams per
banjar / pura", and "mirror-redundant cultural archive" in scope. §4.2 defines seven
write endpoints, §5.1 defines a whole operator UI, §10 a WhatsApp bridge, §10.1 a USSD
hotline. None of it is built. A use-case list drawn only from running code will miss
roughly 90% of what the project is for.

One correction to carry forward: `docs/PROTOCOL.md §0` forbidding the ingestion of
"real people / banjar / pura / ceremony / phone / location / authority records" is a
boundary on **the agents working on the repo**, not a design limit on the platform.
The platform is specified to hold exactly that data — `actor.phone_id` (§10),
`restricted`-tier family name lists (§3.2), signed authority chains (§7.2). Agents may
not put real records in. That is a very different statement from "the platform only
holds institutional identifiers."

## Status legend

- **LIVE** — running in production today
- **SPEC** — specified in the repo, not built
- **OUT** — explicitly excluded, with the clause that excludes it

---

# PART A — Putting data IN

## A1. By record type

| # | Use case | Who | Status |
|---|---|---|---|
| 1 | Author a ceremony record (piodalan, odalan, ngaben, wedding, ngayah, paruman) | pemangku + bendesa + banjar | SPEC §4.2 |
| 2 | Advance a ceremony's state through a signed transition | pemangku / pecalang | SPEC §4.2 |
| 3 | Mark a ceremony **currently underway** (operational, append-only) | pemangku / pecalang, human-verified | SPEC §3.1 |
| 4 | Register a **confirmed** piodalan date that overrides computation | bendesa adat | SPEC §3.1 |
| 5 | Declare a record's visibility tier at authoring time | any authoring actor | SPEC §3.2 |
| 6 | Publish a signed banjar manifest | klian adat / banjar operator | SPEC §4.2 |
| 7 | Declare a mirror partner (**mandatory** — at least one) | banjar | SPEC §4.2, §9 |
| 8 | Join the federation mesh as a peer, send signed heartbeats | banjar / pura | SPEC §4.2, §9 |
| 9 | Record institutional identity (banjar / pura / desa adat, slug + subdomain) | operator | LIVE (2 pilot TSVs) |
| 10 | Bind a signing identity to an authority chain (SMS / gov-ID / hardware token) | all authoring roles | SPEC §7.2 |
| 11 | File or resolve a calendrical dispute | any reviewer | LIVE (`disputes.json`, 27 records) |
| 12 | Record a **customary sign-off** on a ruleset | bendesa / pemangku of standing | LIVE surface, **0 entries** (`SIGNOFF.md`) |
| 13 | Contribute or review a wiki term, per language | translator / customary reviewer | LIVE (302 term/stub pages) |
| 14 | Emit audit lineage rows (`source` + `provenance` + `transition`) | automatic on every write | SPEC §3.1 |

## A2. By channel — how the data physically arrives

| # | Channel | Serves | Status |
|---|---|---|---|
| 15 | DSP write API, JWT bearer, operator-grade | integrators, trained operators | SPEC §4.2 |
| 16 | Operator web UI — `/intake` AI-assisted draft creator | bendesa | SPEC §5.1 |
| 17 | Operator web UI — `/queue` pending-report triage | pemangku | SPEC §5.1 |
| 18 | Operator web UI — `/ceremony` CRUD, `/audit` lineage view | trained operator | SPEC §5.1 |
| 19 | Admin UI — `/reconciliation` mirror-chain repair | admin | SPEC §5.1 |
| 20 | WhatsApp bridge — intent classifier + idempotency ledger | pemangku by phone | SPEC §10 |
| 21 | **USSD / voice hotline** `*888*xxxx#` — confirm a paruman, record a ngaben | elders with no smartphone | SPEC §10.1 |
| 22 | Mesh SSE publishing from a banjar's own subdomain | self-hosting banjar | SPEC §9 |
| 23 | Git contribution to wiki / disputes / conformance corpora | technical contributors | LIVE |

USSD is worth singling out. A cultural-record system whose contributors are often
elderly and often without smartphones either has a no-app channel or it excludes its
most authoritative sources. §10.1 is an access-equity decision, not a nice-to-have.

---

# PART B — Getting data OUT

## B1. Calendar and computation

| # | Use case | Status |
|---|---|---|
| 24 | Full calendar state for a Gregorian date (pawukon, wewaran, saka, rahinan) | **LIVE** |
| 25 | Calendar state across a date range | **LIVE** |
| 26 | Ruleset version + metadata, for pinning and reproducibility | **LIVE** |
| 27 | Rahinan-only lookup for a date | SPEC §4.1 |
| 28 | **Predict piodalan for a pura, N years ahead** | SPEC §4.1 |
| 29 | **Predict odalan for a pura** | SPEC §4.1 |
| 30 | Read which observances the engine does **not** compute | **LIVE** (`unimplemented_observances`) |

#29 and #28 are the single most load-bearing unbuilt read features. "When is our
temple's next odalan" is the question the institution actually has; everything in
the engine today is the substrate for answering it.

## B2. Institutional records

| # | Use case | Status |
|---|---|---|
| 31 | List / filter ceremonies | SPEC §4.1 |
| 32 | Fetch one ceremony with full provenance | SPEC §4.1 |
| 33 | Banjar profile by slug | SPEC §4.1 |
| 34 | Pura profile by slug | SPEC §4.1 |
| 35 | Desa adat profile by slug | SPEC §4.1 |
| 36 | Visibility-tier reference (what each tier means) | SPEC §4.1 |

## B3. Feeds, datasets, archive

| # | Use case | Status |
|---|---|---|
| 37 | GeoJSON publication feed | SPEC §4.1 |
| 38 | Signed JSONL feed | SPEC §4.1 |
| 39 | Per-kabupaten discovery document | SPEC §4.1 |
| 40 | Daily signed dataset snapshot (`.tar.zst` + `.sig`) | SPEC §4.1, §8 |
| 41 | Fetch the well-known signing key to verify any of the above | SPEC §4.1 |
| 42 | Consume the mirror chain — GitHub commits, Mastodon hash posts | SPEC §8 |
| 43 | Subscribe to a single banjar's signed SSE stream | SPEC §9 |
| 44 | Enumerate mesh peers / inspect one peer | SPEC §4.1 |

## B4. Knowledge and evidence

| # | Use case | Status |
|---|---|---|
| 45 | Look up a calendrical term in Balinese / Indonesian / English | **LIVE** |
| 46 | Read a term's citation trail into engine source | **LIVE** |
| 47 | Read a term's customary-review and translation status | **LIVE** |
| 48 | Inspect open disputes and their evidence | **LIVE** |
| 49 | Inspect conformance corpora, eligibility, cross-validation runs | **LIVE** |
| 50 | Audit a record's lineage / authority chain | SPEC §5.1 |

## B5. Public web journeys

| # | Use case | Status |
|---|---|---|
| 51 | Landing page, Balinese first | **LIVE** (static stub) |
| 52 | Browse the calendar visually (wuku wheel, wewaran matrix) | SPEC §5.1 |
| 53 | Browse the banjar index | SPEC §5.1 |
| 54 | View a banjar / pura cultural profile | SPEC §5.1 |
| 55 | Download signed snapshots from a page | SPEC §5.1 |
| 56 | Offline use as an installable PWA | SPEC §5.2 |

---

# PART C — Capabilities that are themselves use cases

| # | Capability | Why it is a use case |
|---|---|---|
| 57 | **Provenance interrogation** — ask of any fact: computed, registered, predicted, or human-verified? | §3.1. Lets an institution distinguish "the algorithm thinks" from "the bendesa confirmed" — the core trust question |
| 58 | **Visibility sovereignty** — one record, five audiences, never auto-promoted | §3.2. A ngaben family name list and a public observance coexist without leaking |
| 59 | **Authority ordering** — most senior valid signature wins on conflict | §7.1. Encodes customary hierarchy as a conflict-resolution rule |
| 60 | **Federation resilience** — platform certifies, does not own | §9. If dewata.org dies, banjars continue; if a banjar goes dark, its mirror holds |
| 61 | **Tamper-evident archive over time** — signed daily snapshots, multi-mirror | §8. "One failure mode deletes one copy, not the project" |
| 62 | **Declared incapacity** — the engine publishes what it cannot compute | LIVE. A reviewer can see purnama/tilem/nyepi are absent rather than trusting a fabricated value |
| 63 | **Reproducible calendrical claims** — every output pinned to a ruleset version | LIVE. Two parties can verify they computed the same thing |

#62 is unusual and worth naming as a product property. Most calendar software answers
every question. This one is built to say "I do not compute that" — which for
institutional use is the more valuable answer.

---

# PART D — Explicitly NOT use cases

Not oversights. Each has a clause.

- Tourism: maps, "near me", "what's open", recommendations, "best of Bali this week" — §0, §5.3, §16
- Routing / navigation: OSRM, Valhalla, GraphHopper, "directions to Pura Y" — §0, §5.2, §16
- Transit feeds: GTFS-rt, DATEX II — §4.3, §16
- Hotel concierge, tour operators, travel agencies, tour booking — §0, §16
- Payment, adat-reciprocation payments, ad-supported anything, location-aware advertising — §0, §16
- Apple / Google Wallet passes — §4.3
- Web-push notification subscriptions — §4.3
- Proximity and edge-intersection queries — §4.3
- "Ceremony of the day" galleries — §16
- Ceremony scheduling **as a recommendation product** — couples may author their own event; the platform does not recommend dates — §16
- Personal astrology / nativity charts — day-level state only, no such computation exists
- *Dewasa ayu* auspicious-day ranking — would require customary rules the project does not encode
- Hanacaraka keyboard UI; docx→html ceremonial text pipeline — §16, separate projects

Visitors may read the `public` tier. They are not the audience — §0.

---

# PART E — Honest status

**Live:** three calendar endpoints plus health and root (`phase-1/src/dewatacalendar/dsp.py`
on `f675b28`); the wiki (302 term and stub pages across three languages, per
`wiki/build-artifacts/coverage.json`; 327 markdown files in total once section
indexes and site pages are included); two pilot registry files holding **5 banjar
and 3 pura records** (`registry/banjar.gianyar.tsv:18-22`,
`registry/pura.gianyar.tsv:8-10` — the file's own header calls it "a placeholder
seed" and says rows are not authoritative until they reach `verification_state >=
desk_only`); and the repo's governance artifacts (27 disputes, conformance corpora,
empty sign-off log). A static landing page.

Note on the registry figures: "22 banjar + 10 pura" appears in `docs/CURRENT_STATE.md`
and in earlier summaries. Those are whole-file line counts, and both TSVs open with a
long prose header. The record counts are 5 and 3.

**Not built:** every write endpoint, every ceremony and institution read endpoint,
both prediction endpoints, all feeds and snapshots, the entire mesh, the whole
operator and admin UI, the WhatsApp bridge, the USSD hotline, the PWA.

That is roughly 6 of 63 use cases in production. The gap is not drift — §14 sets a
build order and the calendar engine is deliberately first, since ceremony prediction
depends on it. But anyone asking "what is dewata.org useful for **today**" should
hear: computing Balinese calendar dates, looking up calendrical terminology, and
auditing the project's own evidence. Everything institutional is ahead of it.

**Two structural blockers on that path**, both already on the record:

1. Ceremony prediction (#28, #29) depends on Saka/sasih semantics that three open
   disputes currently leave unresolved, and resolving them needs customary sign-off.
2. `SIGNOFF.md` records zero sign-offs (`phase-1/docs/runbook/SIGNOFF.md:23`) and
   `can_promote_ruleset_using()` returns False unconditionally
   (`corpus_status.py:464`), so under the project's own rules there is presently no
   path to a released ruleset.

   This is **not** for want of an identified candidate. A reviewer is already
   named and argued for:
   `phase-1/docs/audit/AUTHORITY_VALIDATION_PACKET_wuku_epoch_2026-09-16.md:3`
   proposes Prof. I Wayan Nuarsa, PhD (Universitas Udayana), on the stated basis
   that he is the named compiler of Kalender Bali Digital and an identifiable
   university academic. That packet's own status line reads "prepared only; not
   sent; no endorsement claimed."

   So the gap is narrower and more actionable than "nobody has been identified":
   a candidate is named and a packet is drafted, for the **wuku epoch** question.
   What is missing is (a) sending it, and (b) an equivalent packet for the three
   `sasih_index_drift` disputes that gate ceremony prediction. Nothing here
   asserts that Prof. Nuarsa has agreed, been contacted, or endorsed anything.

Neither is an engineering problem.
