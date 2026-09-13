# README (English)

> English version. primary languages are Balinese (`README_BAL.md`)
> and Indonesian (`README_ID.md`). English is academic-only and does
> not appear in any user-facing UI.

## What is dewata?

**dewata** (ᬤᭂᬯᬢ, "the gods" — plural of *dewa*) is a computer
protocol for **recording, certifying, and preserving** Balinese customary
ceremony.

the project is built for **banjar, pura, and desa adat** — not for
tourists. we record *nyepi* and *odalan*, not "what's closed for
traffic".

## scope

**in scope** (cultural record):
- piodalan (210-day temple anniversary)
- odalan (utama, madya)
- melasti (water procession)
- ngaben and pelebon (cremation)
- paruman (customary assembly)
- ngayah (communal labour)
- kerama

**out of scope** (will not be implemented):
- tourism map / "what's open" feature for visitors
- routing engines (osrm / valhalla / graphhopper)
- hotel concierge integrations
- location-aware advertising
- card-matching / way-finding UX
- any payment-for-adat-reciprocation services

## installation

```bash
pip install -e phase-1/
python -m dewatacalendar ruleset
python -m dewatacalendar date 2026-09-13
```

## conformance corpus

`phase-1/conformance/` — 75k+ generated vectors plus published-source
cross-validation (Cunningham 1994, Igarashi 1999). every vector
carries provenance.

## disagreements with published sources

if you have a different saka-year for a date than the engine produces,
this is almost always because:

  - the source uses a different epoch convention
  - the source encodes a regional variant (lombok / java / bali)
  - the engine has a bug

all disagreements are recorded in `docs/runbook/disputes.json`. none
are silently rejected.

## authorship & contributions

see `CONTRIBUTING.md` (English) or `CONTRIBUTING_ID.md` (Indonesian)
for how to file a dispute, contribute a corrected date, or write code
that observes the cultural-integrity invariants.

## how to reach us

see `bci.dewata.org/connect` after public deployment. wa, ussd, and
email are all available to banjar / pura / individuals seeking to
record their ceremonies.

## license & citation

MIT, with a **cultural-sovereignty notice**. for academic citation
see `CITATION.cff`.

---

this is the english README. the project's primary voice is Indonesian
and Balinese. english is here for academic and technical audience.
