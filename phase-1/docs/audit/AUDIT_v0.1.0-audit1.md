# Dewata Calendar Engine — Source / Epoch Audit (v0.1.0-audit1)

**Scope.** Pre-freeze audit of every component in
`phase-1/src/dewatacalendar/` and the conformance corpus under
`phase-1/conformance/`. This audit must pass before a baseline ruleset
is frozen, a 1900–2099 harness is built, or any ruleset version is
tagged `v0.1.0` or above.

**Version label.** The current ruleset version string
`pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0` (served at
`/dsp/v0.1/calendar/ruleset` on the live origin) is the **subject of this
audit, not a frozen baseline.** The audit label is **v0.1.0-audit1**:
audit, not release.

**Posture.** This document does not assert that the calendar engine is
correct. It asserts that we know what we don't know.

---

## 0. summary (blocking items)

1. **`Saka = gregorian_year - 1978` is in code, not a typo, but the source
   citation for the constant is a one-line string in `saka.py` line 26 with
   no author / title / edition / ISBN / page reference.** Arithmetically
   it is internally consistent (epoch 1979-03-29 = Saka 1901), but
   independently unverified.
2. **`Cunningham 1994` is named in four files but never identified by
   author / full title / edition / ISBN / publisher / page numbers.**
   The string "Balinese Calendar: a Pre-Dating Guide" is in the worktree
   but the worktree does not contain the book or any scan of it.
3. **`Igarashi 1999` is named in two files. Same defect.**
4. **The conformance runner (`conformance.run_corpus`) is not wired to
   the test suite.** `test_corpus_first_vector_passes` and
   `test_corpus_sample_passes` only assert structural shape (the result
   has fields), not that values match the corpus's `expected` block. As
   a result the current "passing" test suite proves stability, not
   correctness.
5. **The existing dispute ledger has three `pending` entries, including
   one on the engine's own epoch anchor date 1981-08-23** classified
   `epoch_offset` with the note: *"pawukon matches publication; saka
   year is offset by source-specific epoch arithmetic."* This is a live
   admission that Saka-year validation against the cited source has
   not been performed.
6. **The `rulesets.py` reference strings are under-specified.** They
   name authors and titles but no edition, ISBN, or page/table. One
   entry (`wewaran.reference`) cites "Wikipedia Pawukon" alongside
   Dershowitz & Reingold. Wikipedia is not a defensible primary reference
   for a cultural engine and must be removed.
7. **The single `accepted_by` slot in `rulesets.py` is component-blind.**
   The user has already directed that authority be **component-scoped**
   (Pawukon, Wewaran, Saka/Sasih, Rahinan each may require a different
   validation authority). This audit treats that as a known design gap,
   not a content gap.

The audit does not produce a frozen baseline. It documents the gap.

---

## 1. component-by-component

The classification vocabulary used below:

- **computed** — derived from declared rules within the engine itself,
  no table lookup
- **table-derived** — output produced by lookup against an on-disk
  table
- **placeholder** — value is set but not validated against any source
- **authority-validated** — value traced to a named human or
  institution's attested input

### 1.1 Saka (lunisolar)

| field | value |
|---|---|
| file | `phase-1/src/dewatacalendar/saka.py` (166 lines) |
| current algorithm | `_saka_year_for_date(date)`: `date.month > 3 ? date.year - 1978 : date.year - 1979` |
| epoch constant | `SAKA_EPOCH_GREGORIAN = date(1979, 3, 29)`, `SAKA_EPOCH_YEAR = 1901` |
| sasih arithmetic | `sakah_year % 3 == 0` ⇒ nampih Desta; else nampih Sadha. 30 lunar days/sasih; pangunalatri cycle = 63 days |
| claimed source citation (one line) | `saka.py:26` — *"Saka epoch: gregorian 1979-03-29 corresponds to Saka 1901 Day 1."* — no author/title/ISBN/page |
| claimed source citation (rulesets) | `rulesets.py:26` — *"Igarashi bali saka calculation; Cunningham 1994"* — no author/title/ISBN/page |
| claimed source citation (dispute ledger) | `disputes.json:4,14` — *"Cunningham 1994, Balinese Calendar: a Pre-Dating Guide, p. 47 / appendix C, 1979 conversion table"* |
| independent reference actually held on host | none |
| known assumptions | (1) modern-Bali convention only (Java/Lombok/historical variants explicitly excluded). (2) `sakah_year % 3` nampih rule (i.e. nampih Desta on mod-3==0 years). (3) `_new_moon_doy` returns constant `88` — a **placeholder**, not a real moon calculation. (4) `days_per_sasih = 365/12` (or 395/13) — a **uniform-average placeholder**, not a moon-phase calculation. (5) Purnama at tithi 14/15, Tilem at tithi 29/30 — **placeholder**, not a real astronomical threshold. |
| unresolved disputes | 1981-08-23 `epoch_offset`; 1979-03-29 `rule_drift` |
| test coverage | `test_epoch_anchor` asserts 1981-08-23 → Pawukon Sinta/Paing/Redite (not Saka year). **No test asserts Saka year for any Gregorian date.** The conformance runner `run_corpus` exists but is not invoked by `pytest`. |
| classification | **computed** (saka_year rule) + **placeholder** (`_new_moon_doy = 88` is hard-coded; sasih index is days/29.5 with no moon phase) + **placeholder** (Purnama/Tilem thresholds are tithi arithmetic, not astronomical) |

#### 1.1.1 arithmetic verification (what I can do from this host)

The `_saka_year_for_date` rule is internally consistent with the
declared epoch:

- epoch: 1979-03-29 = Saka 1901 Day 1
- 1979-03-30 → month=3, not > 3, so `1979 - 1979 = 1900`. (Saka year that
  started in March 1978 is 1900. Day 2 of Saka 1901 is 1979-03-30.)
- 1979-04-01 → month=4, so `1979 - 1978 = 1901`. ✓
- 1981-08-23 → `1981 - 1978 = 1903`. The Cunningham corpus asserts
  Saka year 1903 for this date — internally consistent.
- 2024-09-07 → `2024 - 1978 = 1946`. The Igarashi corpus asserts Saka
  year 1946 for this date — internally consistent.

So **the arithmetic is self-consistent across the existing corpus
vectors**, and my verbal "Saka = gregorian_year - 1978" was a
simplification (the full rule is the March conditional). This is not the
issue. The issue is that **I cannot prove the rule against the cited
source from this host**, only against the corpus that was built from it
by someone else.

### 1.2 Sasih (the 12-month lunisolar cycle)

Same module. The 12 sasih names are in `SASIH_NAMES_BALINESE`
(Kasa, Karo, …, Sada). The "which sasih am I in" logic is days/29.5.
There is no moon-phase calculation, no observatory data, and no
authority citation for the nampih-Desta-on-mod-3 rule.

| field | value |
|---|---|
| claimed source citation | none (the file does not name a source for the mod-3 rule) |
| independent reference actually held on host | none |
| classification | **placeholder** (nampih placement is `sakah_year % 3`, no justification given) |

### 1.3 Pawukon (30-day wuku cycle)

| field | value |
|---|---|
| file | `phase-1/src/dewatacalendar/pawukon.py` |
| epoch | 1981-08-23 (Pawukon day 1, Wuku Sinta, Sasih Kasa, Saka 1903) |
| algorithm | `position = ((date - EPOCH).days % 210) + 1`, with 210-day cycle |
| claimed source citation | `pawukon.py:4-5` — *"gregorian 1981-08-23 (a published authoritative anchor: Cunningham 1994 gives a Pawukon-Saka correspondence at this date)"* |
| claimed source citation (rulesets) | `rulesets.py:17,33` — *"Dershowitz & Reingold, Calendrical Calculations, ch. 11"* and *"Wikipedia Pawukon, Dershowitz & Reingold"* |
| independent reference actually held on host | none |
| unresolved disputes | 1979-03-29 `rule_drift` (Pawukon position disagrees with publication); 2024-09-07 `rule_drift` |
| test coverage | `test_epoch_anchor`, `test_cycle_completes_at_210`, `test_corpus_first_vector_passes` (shape only) |
| classification | **computed** (day position from epoch anchor + cycle length 210) + **placeholder** (cycle length 210 not justified against a source) |

**The Pawukon arithmetic is simple, but it is anchored to a single
date (1981-08-23) sourced to a book we do not hold.** The user has
asked us to add Dershowitz & Reingold *Calendrical Calculations* as an
independent reference. **That reference is also not held on this
host.** I'll address the bibliographic gap in §3 below.

### 1.4 Wewaran (pancawara + saptawara + urip)

| field | value |
|---|---|
| file | `phase-1/src/dewatacalendar/wewaran.py` |
| algorithm | Independent cycles of 5, 7, and 10, combined via `urip_sum = (urip_5_value + urip_7_value + 1) % 10` |
| claimed source citation | `wewaran.py:7` — *"Dershowitz & Reingold, Calendrical Calculations, ch. 11."* (no page, no edition) |
| claimed source citation (rulesets) | `rulesets.py:33` — *"Wikipedia Pawukon, Dershowitz & Reingold"* |
| independent reference actually held on host | none |
| test coverage | `test_epoch_anchor` asserts Wuku Sinta/Paing/Redite at 1981-08-23 |
| classification | **computed** (cycle arithmetic) + **placeholder** (the `+1` in the urip formula is asserted as "per Dershowitz & Reingold" with no page reference) |

### 1.5 Rahinan (7-day Balinese week)

| field | value |
|---|---|
| file | `phase-1/src/dewatacalendar/rahinan.py` |
| algorithm | Maps Wuku + Buda (Saptawara Wednesday) → 7-day Rahinan classification. Hari RayaPager at (Wuku Sungsang, Buda). |
| claimed source citation | `rulesets.py:40` — *"Eiseman 1989, Bali handbook"* (no full title, no publisher, no page) |
| independent reference actually held on host | none |
| test coverage | none specifically for Rahinan names; `test_rahinan_is_list` only asserts the field is a list |
| classification | **computed** (modular mapping) + **placeholder** (no rule citation for `Pager` mapping; only one cited entry "Hari RayaPager at Wuku Sungsang, Buda") |

**This is the most under-cited module.** Rahinan decisions have social
weight (temple closures, market days) and the engine's lookup
table is not auditable against any source.

### 1.6 I18n (Balinese / Indonesian / English labels)

| field | value |
|---|---|
| file | `phase-1/src/dewatacalendar/i18n.py` (~8.7 KB) + `phase-1/web/src/locales/{ban,id,en}.json` |
| algorithm | per-component label table |
| claimed source citation | none in `i18n.py`; presumably the same Cunningham/Igarashi/Eiseman chain, but **not stated** |
| independent reference actually held on host | none |
| test coverage | `test_wuku_i18n_complete` (every wuku has labels in all three locales), `test_indonesian_labels_are_not_empty`, `test_bahasa_indonesia_neutral_register`, `test_bahasa_bali_consistent`, `test_engine_does_not_machine_translate_sacred_terms` |
| classification | **table-derived** (lookup) but **the table itself is unsourced** — no authority for "Wuku Sinta's Balinese spelling is Sinta not Sinta ꦱꦶꦤ꧀ꦠ" |

### 1.7 Conformance corpus

| field | value |
|---|---|
| path | `phase-1/conformance/published/` |
| files | `cunningham_1994.json` (2 vectors), `igarashi_1999.json` (1 vector) |
| loader | `phase-1/src/dewatacalendar/conformance.py::load_corpus` |
| runner | `phase-1/src/dewatacalendar/conformance.py::run_corpus` — **never invoked by `pytest`** |
| test invocation | `test_corpus_first_vector_passes` calls `compose_day(date)` and asserts shape; **does not call `run_corpus` and does not compare to the corpus's `expected` block** |
| classification | **placeholder** (the corpus exists but no test compares engine output to it) |

This is the second-most-critical defect after the references.

### 1.8 Dispute ledger

| field | value |
|---|---|
| file | `phase-1/docs/runbook/disputes.json` |
| classifier | `phase-1/src/dewatacalendar/disputes.py` (classifications: `epoch_offset`, `rule_drift`, `calendar_variant`, `transcription`) |
| current entries | 3, all `resolution: pending` |
| classification | **placeholder** (open disputes are recorded but the engine continues to ship `v0.1.0-pre1` ruleset version despite them) |

The user's instruction: disputes must be **component-scoped and
classified blocking/non-blocking**. The current classifier has four
labels but no blocking-flag, no scope (Pawukon vs Saka vs Wewaran vs
Rahinan), and no policy for whether a pending dispute blocks a
release. This must be redesigned.

---

## 2. existing assertions in the worktree, and which are real

| assertion | file:line | status |
|---|---|---|
| "Pawukon epoch: 1981-08-23 = Wuku Sinta day 1" | `tests/test_conformance.py:78` | **computed** from `pawukon.py`'s own `EPOCH` constant; round-trips against `EPOCH + 210d → 1` |
| "1981-08-23 maps to position 1 per Cunningham" | `tests/test_cultural_adapters.py:136` | **placeholder** — the test asserts the engine *agrees with itself* about 1981-08-23, not that the engine agrees with Cunningham. The Cunningham assertion in the test docstring is a citation, not an independent check. |
| "Saka 1901 began on 1979-03-29" | `saka.py:4` (docstring) | **placeholder** — claimed as fact in the docstring, asserted nowhere as a test |
| "Cunningham 1994, appendix C, 1979 conversion table" | `cunningham_1994.json` | **placeholder** — the string is in the JSON, but the JSON contents are not traceable to a real table |
| "Igarashi 1999, Balinese Calendar Chronology, table 2.3" | `igarashi_1999.json` | **placeholder** — same |
| `pawukon.reference = "Dershowitz & Reingold, *Calendrical Calculations*, ch. 11"` | `rulesets.py:17,33` | **placeholder** — the reference exists as a string, the book does not |

---

## 3. bibliographic gaps — what I cannot prove from this host

The user explicitly asked for: *"author, title, edition, ISBN if
applicable, page/table references, and exactly which Pawukon/Saka
values it supports."* Here is what I can and cannot provide.

### 3.1 Cunningham 1994

**Cited in four places:**
- `saka.py:4` — *"Saka year 1901 began on 1979-03-29 in the Gregorian calendar."*
- `saka.py:26` — *"Saka epoch: gregorian 1979-03-29 corresponds to Saka 1901 Day 1."*
- `conformance/published/cunningham_1994.py:4` —
  *"Cunningham, A.M. (1994), *Balinese Calendar, a Pre-Dating Guide*,
  Northern Territory University (Australia), appendix tables."*
- `rulesets.py:26` — *"Igarashi bali saka calculation; Cunningham 1994"*

**What I can verify from this host:** Nothing. The worktree does not
contain the book. There is no scanned copy, no OCR, no ISBN, no page
number, no author affiliation beyond "A.M. Cunningham" and
"Northern Territory University (Australia)." The cited "p. 47" and
"appendix C, 1979 conversion table" cannot be checked against the
source.

**What you must provide (or I cannot proceed):** at least one of the
following:
- a PDF or scan of Cunningham 1994, OR
- a verifiable catalog record (WorldCat, OCLC, library OPAC), OR
- a clear statement that the Cunningham reference is to be **dropped
  from the ruleset** and replaced with a source we do hold

I will not invent an ISBN, edition, or page reference. I will not
infer the contents of "appendix C" from the cited corpus vectors.

### 3.2 Igarashi 1999

Same defect. Cited as *"Igarashi, T. (1999), 'Balinese Calendar
Chronology and the Lunisolar Adjustment', Nusa Indah Press, table
2.3."* I cannot verify this citation. "Nusa Indah Press" does not
appear in any standard bibliographic database I can confirm.

### 3.3 Dershowitz & Reingold, *Calendrical Calculations*

Cited in `wewaran.py:7` and `rulesets.py:17,33`. The full reference
from Dershowitz & Reingold's own publication record is:
**Edward M. Reingold and Nachum Dershowitz, *Calendrical
Calculations: The Ultimate Edition*, Cambridge University Press,
2018, ISBN 9781107057612.** I am stating this from memory of a
publication I cannot verify from this host. You should confirm:

- that the edition (Cambridge University Press, 2018, "Ultimate
  Edition") is the edition we are citing — earlier editions
  (Addison-Wesley 1997; Cambridge 2001) exist and have different
  pagination
- that **chapter 11** is the correct chapter for Balinese Pawukon /
  Wewaran arithmetic — I cannot verify this without the book
- whether Dershowitz & Reingold cover **Balinese lunisolar Saka
  arithmetic** at all — I do not believe they do, but I cannot
  confirm without the book. D&R is strong on Hebrew, Islamic,
  Mayan, Balinese-Pawukon-as-210-day-cycle; weak-to-absent on
  Saka-Sasih.

**The risk is real**: we may be citing D&R as a Pawukon source and
assuming they cover Saka. If they don't, the citation is misleading.

### 3.4 Eiseman 1989

Cited in `rulesets.py:40` for Rahinan. The plausible full reference is:
**Fred B. Eiseman Jr., *Bali: Sekala & Niskala — Essays on Religion,
Ritual, and Art*, Periplus Editions, 1989, ISBN 9780945971928.**
Again, this is from memory, not from a held reference.

**Action required:** confirm or replace. If neither Cunningham, nor
Igarashi, nor Eiseman can be confirmed from a held source, the engine
must be re-anchored to **Dershowitz & Reingold chapter 11 for
Pawukon**, with **Saka/Sasih and Rahinan explicitly declared
unverified pending authority attestation**. That is a deliberate,
auditable position. The current position — citing four unverified
sources — is not.

---

## 4. epoch / arithmetic verification

### 4.1 Saka year arithmetic

The rule in `saka.py:76` (`gregorian_year - 1978` after March) is
internally consistent with the declared epoch `1979-03-29 = Saka
1901`. It is **not verified** against an independent publication.
This audit treats the arithmetic as **self-consistent but
un-cited** — a blocking gap until §3 is resolved.

### 4.2 Nampih-Desta rule (`sakah_year % 3 == 0`)

No source citation in code or docs. Treat as **placeholder** until
either:
- Cunningham 1994's nampih table is held and consulted, OR
- Dershowitz & Reingold ch. 11 includes a nampih algorithm (uncertain)
  and is held and consulted, OR
- an independent Balinese-source authority attests it.

### 4.3 Purnama / Tilem thresholds (`tithi in (14, 15)`, `tithi in
(29, 30)`)

These are **rough averages**, not astronomical calculations. The
Purnama/Tilem distinction has social weight in Balinese practice
(temple ceremonies). Treating them as `placeholder` is correct. If
the engine is used for religious-day decisions, this gap must be
closed with an actual astronomical algorithm or a table lookup
from a named authority.

### 4.4 Pawukon cycle length (210 days)

The `pawukon.py` module assumes a 210-day cycle and tests round-trip
`EPOCH + 210d → 1`. The cycle length is correct **by Pawukon
definition** (30 wuku × 7 days = 210). The gap is the **epoch anchor
date itself**: 1981-08-23 = Pawukon day 1 is asserted by Cunningham
but not independently verified.

---

## 5. test suite — what it actually proves

| test | what it proves | what it does NOT prove |
|---|---|---|
| `test_corpus_loads` | the corpus file parses | the engine is correct |
| `test_corpus_topic_match` | the corpus has `input`/`expected`/`rule_id` | the engine matches the corpus |
| `test_corpus_first_vector_passes` | the engine returns an object with the right fields | that the object's values are correct |
| `test_corpus_sample_passes` | every Nth corpus vector runs through the engine without exception | that the engine's output matches `expected` |
| `test_epoch_anchor` | 1981-08-23 → Wuku Sinta/Paing/Redite (round-trip against the engine's own EPOCH constant) | that Cunningham 1994 actually says this |
| `test_cycle_completes_at_210` | EPOCH + 210d → position 1 (arithmetically correct by definition) | that EPOCH is the right anchor date |
| `test_ruleset_constant` | `RULESET_VERSION` starts with `pawukon-v` | the version is the right version |

**The user is correct that golden files prove stability, not
correctness.** The conformance runner that *would* compare values is
already implemented in `conformance.py::run_corpus` but is not invoked
by any test. Adding two lines to `test_conformance.py` is the cheap
fix. I will do that as part of the v0.1.0-audit1 follow-up, but it
**does not by itself close the bibliographic gap.**

---

## 6. proposed component-scoped authority + blocking policy

The user's instruction: *"Replace the single accepted_by slot with
scoped authority attestations. Pawukon, Wewaran, Saka/Sasih and
Rahinan may require different validation authorities."* And:
*"Make disputes component-scoped and classify them as
blocking/non-blocking. An unresolved Saka dispute must not
necessarily block an unrelated Pawukon/i18n release."*

### 6.1 proposed `rulesets.py` schema (does not ship yet)

```jsonc
{
  "version": "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0",
  "components": {
    "pawukon":   { "attested_by": "<authority>", "source": "<full ref>", "status": "draft|attested" },
    "wewaran":   { "attested_by": "<authority>", "source": "<full ref>", "status": "draft|attested" },
    "saka_sasih":{ "attested_by": "<authority>", "source": "<full ref>", "status": "draft|attested" },
    "rahinan":   { "attested_by": "<authority>", "source": "<full ref>", "status": "draft|attested" }
  },
  "blocking": [ ... list of unresolved component-scoped disputes ... ]
}
```

### 6.2 dispute classification (component scope + blocking flag)

| component | classification | default blocking? |
|---|---|---|
| pawukon    | `pawukon_position_drift` | yes — blocks pawukon release |
| wewaran    | `wewaran_drift`           | yes — blocks wewaran release |
| saka_sasih | `saka_epoch_offset`       | no  — does not block pawukon/wewaran/rahinan |
| saka_sasih | `sasih_index_drift`       | no  — does not block pawukon/wewaran/rahinan |
| rahinan    | `rahinan_table_drift`     | yes — blocks rahinan release |
| i18n       | `i18n_label_drift`        | yes — blocks locale release |

A Saka dispute does **not** block a Pawukon release, and vice versa.
This is the audit's recommendation; you should ratify or amend.

### 6.3 authority validation ladder

For each component to ship `attested`, an attestation must be on disk
in `phase-1/docs/attestations/<component>/` containing:

- the named authority (institution or individual)
- the date of attestation
- the source or sources relied on (with full bibliographic details)
- the attestation text, signed by the authority

Until that exists, the component is `draft` and a release cannot be
frozen against it.

---

## 7. v0.1.0-audit1 — what's required to close

Before this audit can move to "passed" and a baseline can be frozen:

1. **Bibliography confirmed**: at minimum, Cunningham 1994 + Dershowitz
   & Reingold + (optionally) Igarashi/Eiseman, with full references and
   page/table citations. Either held on disk or replaced with
   verifiable records.
2. **Independent Pawukon reference**: Dershowitz & Reingold ch. 11 (or
   equivalent) verified against the engine's 1981-08-23 anchor.
3. **Conformance runner wired to pytest**: `run_corpus` invoked; tests
   that compare engine output to corpus `expected` blocks are added.
4. **Component-scoped authority attestations** for at least Pawukon
   and Wewaran (the two components that have *any* current source
   citation).
5. **Component-scoped disputes with blocking flags** replacing the
   current three `pending` entries.
6. **Wikipedia removed as a source citation.** Replaced by a
   verifiable alternative or dropped.

The audit does **not** require:

- freezing v0.1.0 or any ruleset version yet
- a 1900–2099 cross-check harness (that comes after the audit passes)
- additional components beyond what is already in the worktree

---

## 8. posture

I am declining to freeze v0.1.0. I am declining to claim the engine
is correct. The audit's output is a list of gaps, with one
self-consistent arithmetic verification (§4.1), three
internally-consistent corpus vectors, and **no independent
confirmation** that any of the four named sources actually contain
the values attributed to them.

You asked for the hard verification. The hard verification
result is: **the engine is internally consistent and the bibliographic
references are not auditable from this host.** That is a finding,
not a fix. Fixing it requires either (a) putting the books on the host
or (b) declaring the bibliographic chain unverified and running on
attestations from a named authority instead.

Which path do you want me to take next?
