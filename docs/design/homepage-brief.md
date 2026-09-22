# Design brief — dewata.org apex homepage and main navigation

> **Status: PROPOSAL.** Not ratified, not a decision record, carries no
> D-number. Nothing here changes calendar rules, ruleset versions,
> dispute state, or sign-off records, and nothing here asserts customary
> authority over any Balinese term, date, or practice.
>
> **date:** 2026-09-22
> **branch:** `design-idea`
> **scope:** the apex host `dewata.org` only. `bci.`, `protocol.`,
> `datasets.`, `api.`, and `wiki.` are referenced but not redesigned.
> **supersedes:** nothing.

---

## 1. What this brief is and is not

This is a design proposal for the public apex page and its navigation. It
is written to be argued with before any HTML exists.

It **is**: goals, audiences, a sitemap, text wireframes, tone direction,
i18n rules, and the open questions that remain.

It is **not**: a customary claim, a ruleset change, a translation
authority, or a deployment plan. Any Balinese-language string this design
eventually ships is subject to the customary sign-off workflow in
`phase-1/docs/runbook/SIGNOFF.md`, exactly as wiki pages are.

---

## 2. Goals

1. **Say what dewata is in one screen**, in the reader's language, without
   a visitor mistaking it for a travel site.
2. **Route, don't absorb.** Get each audience to the right surface —
   wiki, api, contribution path — in one hop.
3. **Show the project's real state.** Which surfaces are live, which are
   placeholders, which ruleset and candidate produced the output on
   screen.
4. **Make unavailability visible, not invisible.** A field the engine does
   not compute must read as *unavailable* on the page, never as blank,
   zero, or a plausible-looking substitute.
5. **Give a non-technical banjar reader a reachable next step** that is
   not a GitHub URL.

### Non-goals

- No "what's on today in Bali" framing, no discovery or recommendation UX.
- No ceremony browse/search on the apex — that is `bci.dewata.org`.
- No account, no personalisation, no notification signup.
- No photography of ceremony, pemangku, or identifiable people
  (`CONTRIBUTING.md` §privasi makes sourced imagery a consent question,
  not a design question).
- No claim of completeness for the Balinese-language surface.

---

## 3. Audience

Ordered by whose needs win when two conflict.

| # | Audience | Arrives wanting | Success |
|---|---|---|---|
| 1 | **Banjar / pura / desa adat** (klian, bendesa, pemangku) | to know what this is, whether it touches their pura, how to correct or register something | reaches `/connect` or a human contact route, not a PR form |
| 2 | **Balinese and Indonesian public readers** | to read the calendar for today and understand a term | reaches the calendar strip, then a wiki term page |
| 3 | **Academic / cultural researchers** | corpus, provenance, citation, disputes | reaches `CITATION.cff`, the conformance corpus, `disputes.json` |
| 4 | **Engineers / implementers** | the API contract and the repo | reaches `api.dewata.org` and the GitHub repo |

Audience 1 is the design's centre of gravity even though audience 4 is
loudest in the repository. Where an affordance serves 4 at the cost of 1
(jargon in nav labels, English-first copy, GitHub as the only contact
route), audience 1 wins.

---

## 4. Settled questions

These were decided by the governance owner on 2026-09-22 and are recorded
here as the brief's premises, not as independent decisions.

| # | Question | Settled as |
|---|---|---|
| 1 | Does the apex absorb bci / banjar content? | **No.** Apex stays a thin shim. No banjar or ceremony browse tree on the apex. |
| 2 | Static HTML or Next.js at the apex? | **Static HTML.** Next.js stays at `bci.dewata.org` per `ARCHITECTURE.md` §5. |
| 3 | Which language code is public? | **`ban`.** `_BAL` (repo filenames) and `balinese` (engine i18n keys) are internal/legacy spellings and stay where they are. |
| 4 | Is the calendar strip static or live? | **Live from the API**, with an explicit unavailable state. Never invent or cache-forward a day. |
| 5 | The `docs/runbook/` path mismatch | **Flag only.** See §11.1. No files are relocated by this change. |

---

## 5. Inherited constraints (verified in-repo, 2026-09-22)

The design has to sit on top of these. They are facts about the system as
it stands, not proposals.

**Surfaces.** Per `docs/CURRENT_STATE.md` (snapshot 2026-09-20):
`dewata.org`, `api.dewata.org`, `wiki.dewata.org` return 200.
`bci.`, `protocol.`, `datasets.` return **503 placeholders**. The
homepage must not present a 503 host as a working destination.

**The live API is calendar-only.** Three endpoints exist under
`/dsp/v0.1/calendar/`: `ruleset`, `date/{YYYY-MM-DD}`, `range`
(`phase-1/src/dewatacalendar/dsp.py`). `ARCHITECTURE.md` §4 specifies
roughly twenty more; none are deployed.

**What a day actually contains.** `CalendarDay`
(`phase-1/src/dewatacalendar/api.py`) carries `gregorian`, `ruleset`,
`candidate_id`, `saka`, `pawukon`, `wewaran`, `rahinan`,
`unimplemented_observances`, and a human-readable `note`.

**Nine rahinan, not twenty-four.** `IMPLEMENTED_RAHINAN_IDS`
(`phase-1/src/dewatacalendar/rulesets.py`) is `buda_wage`,
`buda_kliwon`, `saniscara_umanis`, `tumpek_landep`, `anggara_kliwon`,
`redite_paing`, `saraswati`, `galungan`, `kuningan`.
`UNIMPLEMENTED_RAHINAN_IDS` is `purnama`, `tilem`, `nyepi` — real terms
the engine does not compute. The API always returns that list, whether or
not the day has other rahinan.

**`saka_year` is unavailable by design.** The public field is `None`; the
raw January-rollover value survives only as
`saka_year_diagnostic_january_rollover`, which is unvalidated and not
customary-attested (decision D10). The page must render "unavailable" and
say why — it must not fall back to the diagnostic.

**Two identifiers, not one.** `RULESET_VERSION` is frozen at
`pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0`;
`CANDIDATE_ID` is `candidate-2026-09-20-strip-corrections-r2` (D9). Both
belong in the page footer. Showing only the ruleset would republish
changed output under an indistinguishable identity — the exact failure D9
exists to prevent.

**Basa Bali is primary in intent, unverified in fact.** Every
`wiki/docs/ban/` page carries `pending_customary_review`. The apex
inherits that status; it cannot out-run the wiki.

**Sasih indexing is disputed.** Three open `sasih_index_drift` disputes
are unresolved and `SIGNOFF.md` is empty (`docs/BACKLOG.md` B2, B3). The
page must not present sasih as settled.

---

## 6. Sitemap

Apex only. Flat, small, and translated three ways.

```
/                         redirect → /ban/  (Accept-Language may override to /id/ or /en/)
/ban/                     home — Basa Bali (primary)
/id/                      home — Bahasa Indonesia
/en/                      home — English (academic)

/{lang}/about             what dewata records, what it refuses to record, scope fence
/{lang}/status            surface status, ruleset + candidate identity, links to disputes
/{lang}/connect           how a banjar / pura / individu reaches a human
/{lang}/cite              LICENSE (MIT + cultural-sovereignty clause) and CITATION.cff

outbound (not apex pages):
  wiki.dewata.org         term definitions, three languages, parallel slugs
  api.dewata.org          DSP v0.1 calendar endpoints + openapi.json
  github.com/...          repository, CONTRIBUTING, disputes
  bci. / protocol. / datasets.   listed on /status as NOT YET LIVE, not linked as destinations
```

Seven page templates × three languages. No deeper tree. If a section
wants a child page, that is a signal it belongs on `bci` or the wiki.

### Primary navigation

Five items, same order in every language:

`Beranda · Kalender · Wiki · Adat & Lingkup · Hubungi`
(home · calendar · wiki · scope · contact)

"Kalender" is an in-page anchor to the calendar strip, not a separate
page — the apex has exactly one day view and does not become a calendar
browser. The language switcher sits at the far right of the nav, always
showing all three codes (`ban · id · en`) rather than hiding the current
one, so a reader can see the project is trilingual before choosing.

---

## 7. Wireframe notes

Text wireframes. Boxes are regions, not pixel dimensions.

### 7.1 Home (`/{lang}/`)

```
┌───────────────────────────────────────────────────────────────┐
│ ᬤᭂᬯᬢ  dewata.org                        ban · id · en          │
│ Beranda  Kalender  Wiki  Adat & Lingkup  Hubungi              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  [A] IDENTITY                                                 │
│  Protokol pencatatan, pensahan, miwah pelestarian             │
│  upacara adat Bali.                                           │
│                                                               │
│  Kanggen banjar, pura, miwah desa adat — nénten kanggen       │
│  turis.                                                       │
│                                                               │
│  ── status strip ──────────────────────────────────────────   │
│  v0.1 · engine kalender live · surface tiosan durung live     │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  [B] TODAY  (live from api.dewata.org)                        │
│                                                               │
│   Saniscara, 22 September 2026                                │
│                                                               │
│   Wuku          <wuku name>        → wiki                     │
│   Wewaran       <eka..dasa wara>   → wiki                     │
│   Sasih         <sasih name>  ⚠ durung kauji / unvalidated    │
│   Warsa Saka    — tan wénten / unavailable        [why?]      │
│                                                               │
│   Rahinan today:  <emitted ids, or "tan wénten rahinan">      │
│                                                               │
│   ⓘ Engine puniki nénten ngitung: purnama · tilem · nyepi     │
│     (istilah sujati, durung kaimplementasi)                   │
│                                                               │
│   [source: GET /dsp/v0.1/calendar/date/2026-09-22]            │
├───────────────────────────────────────────────────────────────┤
│  [C] THREE DOORS                                              │
│                                                               │
│   ┌──────────────┬──────────────┬──────────────┐             │
│   │ Banjar/pura  │ Peneliti     │ Engineer     │             │
│   │ Daftarang    │ Korpus,      │ API, repo,   │             │
│   │ upacara,     │ provenance,  │ openapi      │             │
│   │ koreksi      │ sitiran      │              │             │
│   │ → /connect   │ → /cite      │ → api.       │             │
│   └──────────────┴──────────────┴──────────────┘             │
├───────────────────────────────────────────────────────────────┤
│  [D] WHAT WE DO NOT RECORD                                    │
│   · wewenang adat — bendesa adat sané uning                   │
│   · putusan pribadi pemangku                                  │
│   · tanggal sané kausulang olih iraga padidi                  │
│   · rekomendasi bisnis / iklan                                │
│                              → selengkapnya /about            │
├───────────────────────────────────────────────────────────────┤
│  [E] FOOTER                                                   │
│   ruleset: pawukon-v0.4.1+saka-bali-v0.2.3+...                │
│   candidate: candidate-2026-09-20-strip-corrections-r2        │
│   status basa Bali: pending_customary_review                  │
│   MIT + cultural-sovereignty clause · CITATION.cff            │
│   wiki · api · github · status                                │
└───────────────────────────────────────────────────────────────┘
```

Notes on the regions:

- **[A]** is copy that already exists. The Balinese lines are adapted from
  `README_BAL.md`; the Indonesian from `README_ID.md`. No new claims are
  authored for the hero.
- **[B]** is the only live-data region on the site. Its rules are in §9.
- **[B] "why?"** opens an inline disclosure, not a new page: two sentences
  on why `saka_year` is unavailable, linking to the wiki sasih page and
  the open disputes. Do not paraphrase the dispute; link it.
- **[C]** deliberately has no fourth door for "visitors". Visitors read
  the same page everyone else does.
- **[D]** mirrors the "apa yang tidak boleh kami catat" list that already
  exists in both READMEs. It is placed above the footer because it is the
  clearest single signal that this is not a tourism site — it should be
  visible without following a link.
- **[E]** carries both identifiers, always.

### 7.2 Status (`/{lang}/status`)

One table, one paragraph, no marketing.

```
Surface              URL                        Status
apex                 dewata.org                 live
api (kalender)       api.dewata.org             live — calendar endpoints only
wiki                 wiki.dewata.org            live — ban pending_customary_review
bci                  bci.dewata.org             DURUNG LIVE / not yet shipped
protocol             protocol.dewata.org        DURUNG LIVE / not yet shipped
datasets             datasets.dewata.org        DURUNG LIVE / not yet shipped

Engine identity
  ruleset            <RULESET_VERSION>          frozen — bump requires customary sign-off
  candidate          <CANDIDATE_ID>             development identity, not a release

Open disputes        3 sasih_index_drift        → disputes.json
Customary sign-off   SIGNOFF.md is empty        no ruleset bump permitted
```

Not-yet-live rows render as plain text, not links. A reader should not be
able to click their way into a 503.

### 7.3 Language variant pages

Same template, same slugs, three languages — matching the wiki's parallel
structure so a reader can move between the two without re-learning the
URL shape. Where a `ban` block has no signed-off string, see §8.

### 7.4 Connect (`/{lang}/connect`)

Reflects `CONTRIBUTING.md` and nothing more: what to send (one pukulana,
a screenshot if any, your name and wewenang), what happens next
(verification by phone before anything is recorded), and the routes — wa,
ussd, operator note — each marked *akan diumumkan* until the real
channels exist. The GitHub route is listed last, not first.

An honest "not yet announced" is the correct content here. A contact form
that posts nowhere would be worse than the placeholder.

---

## 8. i18n rules

**Public codes are `ban`, `id`, `en`.** `ban` is the ISO 639-3 code for
Basa Bali and is what the wiki already uses for its directories. The repo
filenames (`README_BAL.md`) and the engine's i18n keys
(`lang="balinese"`, `phase-1/src/dewatacalendar/i18n.py`) are internal and
legacy; this brief does not propose renaming them. Any build step that
reads engine strings maps `balinese → ban` at the output layer, which is
where the engine already says language selection belongs.

**Default and ordering.** `/` resolves to `/ban/`. `Accept-Language` may
send a reader to `/id/` or `/en/` on first visit; an explicit click on the
switcher is sticky and always wins. English is reachable but never the
default, per `README_EN.md`: English "does not appear in any user-facing
UI" as a primary voice.

**Fallback rule — the important one.** When a `ban` string has not been
verified through the engine's i18n table or an existing signed-off source:

```
render the id string, in place, with a visible marker:
    [id] <text>   ⚠ pending_customary_review
```

Not machine translation. Not an empty block. Not silent substitution of
Indonesian styled as Balinese. A reader must be able to see which parts of
the Balinese surface are real and which are awaiting review — the same
contract `wiki/docs/ban/` pages already honour.

**Aksara Bali.** `ᬤᭂᬯᬢ` appears as the wordmark with the romanised
"dewata.org" always adjacent, never as a replacement. Webfont coverage for
Balinese script is unreliable across devices; the romanisation is the
fallback, and no navigation label depends on the script rendering.

**Translation status is page-level metadata**, mirroring the wiki's
front-matter (`translation_review_status`, `last_reviewed`), and surfaces
in the footer of each page rather than being tracked only in source.

---

## 9. How calendar, API, and wiki fit together

One loop, three roles:

> **the calendar states the fact · the wiki explains the term · the API is
> the receipt**

For a visitor this means: region [B] shows today's wuku and wewaran; each
term links to its wiki page at the matching language and slug; the footer
names the ruleset and candidate that produced those values, and the strip
prints the exact API call so a reader can fetch it themselves.

**Live-fetch rules** (settled Q4):

1. The strip fetches `GET /dsp/v0.1/calendar/date/{today}` client-side on
   load. Today is computed in **WITA**, not the visitor's local timezone.
2. **Unavailable is a rendered state, not an absence.** `saka_year: null`
   renders as "tan wénten / unavailable" with the disclosure link. Never
   blank, never `0`, never the January-rollover diagnostic.
3. **`unimplemented_observances` always renders**, even on a day with
   rahinan. The API returns it unconditionally and the page treats it the
   same way: purnama, tilem, and nyepi are named as terms the engine does
   not compute, so a reader never concludes from silence that today is not
   purnama.
4. **API unreachable → say so.** The strip renders "kalender nénten
   kasedia — API tan prasida kahubungin" with the failing endpoint and a
   retry. It does not fall back to a client-side computation, a cached
   day, or a hand-written date. There is no invented day on this site.
5. **Sasih carries its unvalidated marker** wherever it appears, per the
   three open disputes.
6. The strip is progressive: regions [A], [C], [D], [E] are static HTML
   and render fully without JavaScript. Only [B] depends on the fetch, and
   its no-JS state is the same honest "not available" message.

**A deployment caveat.** The corrections branch that introduced
`candidate_id`, `saka_year: null`, and `unimplemented_observances` is not
yet merged or deployed (`docs/CURRENT_STATE.md`, `docs/BACKLOG.md` B5).
The production API today still emits the pre-corrections shape — including
`saka_year: 48`. A homepage built against the corrected contract would
render today's production response wrongly. Either the front-end ships
after that deploy, or it detects the old shape and renders unavailable.
**Recommendation: ship after the deploy.** Writing a compatibility shim
for output the project has already decided is wrong would embed that wrong
output in a second place.

---

## 10. Visual tone

**Calm, textual, and evidently maintained.** The page should read like a
well-kept public record — closer to an institutional archive than to a
product landing page.

- **Typography carries the design.** One serif for headings with good
  diacritic coverage (á, é, ö appear throughout Balinese romanisation),
  one humanist sans for body and data. Generous measure, generous
  leading. No display weights above the wordmark.
- **Palette: warm paper and ink.** Light mode off-white rather than pure
  white; dark mode warm near-black rather than grey. A single restrained
  accent. The wiki's mkdocs-material indigo is a theme default, not a
  chosen identity — a colour drawn from *wastra* textile would sit better
  with the subject, but choosing it is §11.2, and it should be chosen with
  a Balinese reviewer rather than by the design alone. Until then the
  build uses a neutral placeholder accent.
- **No imagery of people or ceremony.** Consent obligations in
  `CONTRIBUTING.md` apply to the site as much as to the repo; stock
  photography of Balinese ritual would violate the spirit of that section
  even where it is technically licensed. Texture, rule lines, and the
  aksara wordmark carry the visual identity instead.
- **Status chips over hero imagery.** `live`, `durung live`,
  `pending_customary_review`, `durung kauji` are recurring UI objects with
  one consistent visual treatment, used identically on the home, status,
  and calendar regions. They are the site's most distinctive element and
  should look deliberate, not like error states.
- **Density is fine.** This audience reads. Two columns on wide screens,
  single column under 720px. Tables stay tables — they do not become cards.
- **Accessibility floor:** WCAG AA contrast in both themes, visible focus
  rings, full keyboard operability, `lang` attributes set correctly per
  block (including on mixed `[id]`-fallback blocks, so screen readers do
  not read Indonesian as Balinese), and a no-JavaScript render that keeps
  every non-[B] region intact.

---

## 11. Open questions

### 11.1 The `docs/runbook/` path mismatch (flag only, per Q5)

`CONTRIBUTING.md` points contributors at `docs/runbook/RULESET_VERSIONING.md`
and `docs/runbook/disputes.json`. Both files live at
`phase-1/docs/runbook/`. `README.md` repeats the same two references.
There is no `docs/runbook/` directory in the repository.

Consequence for this design: `/connect` and `/cite` must link the real
paths, or they will ship broken links on day one. **No files are relocated
by this change** and no README is edited here. Needs a decision:
relocate the runbooks, or correct the references. Whichever is chosen
should happen before the apex hard-codes URLs into published pages.

### 11.2 Accent colour and any *wastra*-derived palette

Proposed to be chosen with a Balinese reviewer rather than selected from
the design alone, given that textile colour carries meaning this brief has
no standing to assign. Blocked on: who reviews. Until resolved the build
uses a neutral placeholder.

### 11.3 `/dsp/v0.1/calendar/ruleset` does not expose `candidate_id`

The endpoint returns `{"version": RULESET_VERSION}` only
(`phase-1/src/dewatacalendar/dsp.py`), while `compose_day` returns both
identifiers. A footer that wants the candidate id must currently read it
from a `date/` response, which is awkward and breaks when the date fetch
fails. Should `ruleset` also return `candidate_id`? That is an API change,
out of scope for this brief, but the design depends on the answer.

### 11.4 Who operates `/connect` before the wa/ussd channels exist?

`CONTRIBUTING.md` says operators verify authority by phone before
anything is recorded. Until a channel and an operator exist, `/connect`
can only say "akan diumumkan". Is there an interim route — a monitored
address, a named person — or does the page stay a placeholder?

### 11.5 Does the apex need a `/disputes` view?

Disputes are arguably the most trust-building artefact the project has,
and currently they are only reachable as JSON in the repo. A read-only
rendering would serve audience 3 well. It also expands the "thin shim"
past what Q1 settled. Left out of the sitemap above; raising it because
the omission is a judgement call, not an oversight.

### 11.6 Timezone handling for visitors outside WITA

§9 fixes "today" to WITA. A reader in another timezone may see a date that
disagrees with their device. Should the page say "22 September 2026
(WITA)" explicitly on every render, or only when the visitor's timezone
differs?

### 11.7 Translation review capacity

Every `ban` string on this site inherits the wiki's
`pending_customary_review` backlog, and `SIGNOFF.md` is empty. If the
apex ships with most Balinese blocks in `[id]` fallback, is that
acceptable as a launch state, or does launch wait on a first sign-off?
This is a governance question, not a design one, but it determines what
the site looks like on day one.

---

## 12. What this brief does not decide

- Any calendar rule, ruleset version, candidate identity, or dispute
  resolution.
- Any Balinese translation, spelling, or ceremonial meaning.
- Whether `1979-03-29 = Saka 1901`, or any other epoch or sasih question.
- Deployment, DNS, Caddy configuration, or release procedure.
- The content of `bci.dewata.org`, `protocol.dewata.org`, or
  `datasets.dewata.org`.
- Whether the strip-corrections branch merges or deploys.

Authority over calendar and customary questions flows through
`phase-1/docs/runbook/SIGNOFF.md` and the two-tier review in
`CONTRIBUTING.md`. This document is a proposal about a web page.
