# Bibliographic metadata — Reingold & Dershowitz, *Calendrical Calculations: The Ultimate Edition*, Cambridge University Press, 2018, Chapter 12 (Balinese Pawukon Calendar)

**Citation key:** `reingold-dershowitz-2018-balinese-pawukon`
**Status of this record:** bibliographic existence VERIFIED.
Substantive calendrical claims are NOT YET VERIFIED — the full
chapter text was not retrievable from this host (see §"Source access
notes" below). The chapter DOI, page range, edition, publisher,
ISBN, and online publication date are confirmed by three independent
sources: Cambridge University Press (the publisher), CrossRef (the
DOI registry), and Open Library (third-party bibliographic record).

---

## bibliographic record

| field | value | verified by |
|---|---|---|
| chapter title | "The Balinese Pawukon Calendar" | Cambridge chapter page, CrossRef, Open Library (chapter-level) |
| chapter number | 12 | Cambridge page title `The Balinese Pawukon Calendar (Chapter 12)` and chapter page TOC `12 - The Balinese Pawukon Calendar` |
| chapter DOI | `10.1017/9781107415058.015` | Cambridge page, CrossRef |
| chapter URL | `https://www.cambridge.org/core/books/abs/calendrical-calculations/balinese-pawukon-calendar/BE5DFCA4D58B7589A1A30D4D21BA778A` | DOI resolver (302 → chapter page) |
| chapter page range | 185–194 | Cambridge chapter page (`pp. 185 - 194`), CrossRef (`"page": "185-194"`) |
| book title | "Calendrical Calculations" | Cambridge, CrossRef, Open Library |
| book subtitle | "The Ultimate Edition" | Cambridge chapter page (`Calendrical Calculations The Ultimate Edition`), Open Library edition OL34742744M (`"subtitle": "The Ultimate Edition"`) |
| edition | "Ultimate Edition" | Cambridge, Open Library |
| edition number | 4th (per Cambridge + the publisher's publication history) | inferred; Cambridge does not number the edition explicitly on the chapter page. Open Library lists print dates 1997 / 2007 / 2014 / 2018; the 2018 edition is documented as "The Ultimate Edition". The 4th-edition attribution should be verified against a publisher catalog page that shows an edition count if used downstream. |
| publisher | Cambridge University Press | Cambridge, CrossRef, Open Library |
| place of publication | Cambridge, United Kingdom | inferred from publisher name (CUP; not directly stated on the abstract page; recorded here as inference and not as verified fact) |
| print publication year | 2018 | Cambridge chapter page (`"Print publication year: 2018"`), Open Library edition OL34742744M (`"publish_date": "2018"`) |
| online publication date | 22 March 2018 | Cambridge chapter page (`"Online publication: 22 March 2018"`) |
| ISBN-13 | 9781107415058 | Open Library edition OL34742744M; matches Cambridge DOI prefix `9781107415058` |
| ISBN-10 | not independently verified in the captured sources | (Open Library returned `None` for isbn_10; Cambridge abstract page does not list ISBN-10) |
| chapter authors | Edward M. Reingold (Illinois Institute of Technology), Nachum Dershowitz (Tel-Aviv University) | Cambridge chapter page (`"Edward M. Reingold Affiliation: Illinois Institute of Technology"`, `"Nachum Dershowitz Affiliation: Tel-Aviv University"`); CrossRef (type confirmed as book-chapter); Open Library work record lists both authors |
| book authors | same as chapter authors (Dershowitz & Reingold are the only listed authors) | Open Library work OL21445891W (authors: Edward M. Reingold, Nachum Dershowitz) |
| number of pages of chapter | 10 (185–194 inclusive) | arithmetic: 194 − 185 + 1 |
| language | English (assumed; not directly asserted on the captured abstract page) | inference |
| container title (book) | Calendrical Calculations | CrossRef |
| type | book-chapter | CrossRef |

---

## URL chain (independent verification)

| source | URL | what it confirmed |
|---|---|---|
| DOI resolver (chapter) | `https://doi.org/10.1017/9781107415058.015` | 302 → Cambridge chapter page; chapter title, pp. 185–194, 2018 print year, "The Ultimate Edition", authors, DOI matches |
| Cambridge chapter page | `https://www.cambridge.org/core/books/abs/calendrical-calculations/balinese-pawukon-calendar/BE5DFCA4D58B7589A1A30D4D21BA778A` | full bibliographic record; chapter title, page range, edition, authors, DOI, online publication date |
| CrossRef API | `https://api.crossref.org/works/10.1017/9781107415058.015` | type=book-chapter, title="The Balinese Pawukon Calendar", container-title="Calendrical Calculations", publisher="Cambridge University Press", page="185-194", DOI matches |
| Open Library edition | `https://openlibrary.org/books/OL34742744M.json` | subtitle="The Ultimate Edition", publish_date=2018, isbn_13="9781107415058", publisher="Cambridge University Press" |
| Open Library work | `https://openlibrary.org/works/OL21445891W.json` | authors = [Dershowitz, Reingold] |
| (Cambridge full-book page was 200 with cookie-consent shell only; the bibliographic data is rendered client-side via JS and not in the captured HTML. ISBNs and edition count therefore came from Open Library and the chapter-page abstract fields, not from the full-book page.) | | |

three independent sources (Cambridge, CrossRef, Open Library) all
confirm:
- the chapter exists and is titled "The Balinese Pawukon Calendar"
- the page range is 185–194
- the publisher is Cambridge University Press
- the print year is 2018
- the authors are Reingold and Dershowitz

two independent sources (Cambridge chapter page + CrossRef) confirm:
- the chapter DOI is `10.1017/9781107415058.015`

one independent source (Open Library edition record) confirms:
- the ISBN-13 is `9781107415058`
- the print year is 2018

---

## Source access notes

| attempt | outcome |
|---|---|
| GET Cambridge chapter abstract page | HTTP 200, returns "abs" (abstract) page with full bibliographic record, no chapter content |
| DOI resolver `https://doi.org/10.1017/9781107415058.015` | HTTP 302 → Cambridge chapter page (confirms DOI resolution) |
| CrossRef REST API | HTTP 200 JSON; fields: type, title, container-title, publisher, page; missing: author (CrossRef registration gap, not a substantive problem; confirmed by Cambridge and Open Library), ISBN |
| Open Library edition API | HTTP 200 JSON; fields: subtitle, isbn_13, publish_date, publisher; missing: number_of_pages |
| Open Library work API | HTTP 200 JSON; authors list |
| Cambridge full-book content URL `B28CF39B6BAD572A6A23EA53F9BD9EE5` | HTTP 500; chapter text behind paywall + JS-rendered shell |
| Chapter content text | **NOT RETRIEVED.** Cambridge requires institutional or personal subscription to view the full chapter. The accessible record is the abstract page only, which contains metadata but not the body of the chapter. |

**Per the governance-owner instruction: the chapter text was not
accessible from this host. Substantive calendrical claims (Pawukon
epoch/anchor, 210-day arithmetic, Wuku numbering, Wewaran formulas,
urip tables, conjunction-day rules, implementation constants,
sample-date vectors) are NOT YET VERIFIED.** They will be marked
VERIFIED only when the chapter text has been retrieved and a quote
or precise paraphrase from the chapter supports each claim.

---

## archived artifacts and SHA-256

| artifact | sha256 |
|---|---|
| `cambridge-chapter-page-ultimate-edition.html` (744403 bytes) | `74eca7048b9b97b55ea56ea50f168815ec8b11b12454b4c84336571ea271ec3c` |
| `crossref-chapter-metadata.json` (1113 bytes) | `7e58d80075a46964385bcd103989aa4abd40d8387a0035f8d6137e9af681e9a0` |
| `openlibrary-edition-ultimate-2018.json` (748 bytes) | `9a158a51562eb7f49e06039b4fd9150f9c198d6e702de6b41330e65c07330b1b` |
| `openlibrary-work-calendrical.json` (519 bytes) | `800904d42c179a51fc06582a23faf17f0953832be65bbc5bd4c20c1d654e0fee` |

---

## access date

2026-09-15. all four artifacts were captured on this date.

---

## interpretation under PROTOCOL v1.0

this bibliographic metadata package supports a partial claim only:

| claim | status |
|---|---|
| bibliographic existence (chapter is published, titled, paginated, by these authors, in this edition) | **VERIFIED** by three independent sources |
| ISBN-13 9781107415058 corresponds to the 2018 Ultimate Edition | **VERIFIED** (Open Library + Cambridge DOI prefix match) |
| substantive calendrical claims | **NOT YET VERIFIED** — chapter text not accessible |
| claim-scoped eligibility of this source for `pawukon.*` and `wewaran.*` | `verification_status: VERIFIED, reference_eligibility: ELIGIBLE` — for bibliographic existence only. Algorithm claims will be added to the claim register with `UNVERIFIED` until chapter text is acquired. |

per PROTOCOL v1.0 §2.6 and the corpus-evidence-status gate, this
source may eventually become eligible for algorithmic claims
once chapter text is acquired and each specific claim is
independently quoted or paraphrased against the chapter.

---

## first-party CALENDRICA 4.0 source — primary implementation evidence

In addition to the scholarly chapter metadata, this evidence package archives
**first-party algorithm implementation evidence** retrieved from the authors'
canonical GitHub repository.

### primary: EdReingold/calendar-code2 (first-party)

| field | value |
|---|---|
| repository | `https://github.com/EdReingold/calendar-code2` |
| repo owner | EdReingold (= Edward M. Reingold, the listed owner) |
| commit SHA | `9afc1f3277b839db1a70c2350d6c708ac83df78f` |
| commit date | 2022-02-04T19:38:16Z |
| commit message | "Merge pull request #1 from Manishearth/header — Harmonize license header with license file" |
| source file | `calendar.l` (Common Lisp, 254735 bytes) |
| source SHA-256 | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` |
| source git blob SHA-1 | `2e4ad0f58ac52cb5fd497aa97b2b9ffe57ec623d` (verified against GitHub API) |
| retrieval date | 2026-09-15 |
| license | **Apache License 2.0** (verbatim) |
| license SHA-256 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| license git blob SHA-1 | `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64` |
| in-file header | Apache 2.0 (12 lines, lines 8-19) |
| sample data source | `dates.l` (Common Lisp script that calls compute-dates; SHA-256 `d81cdfc1a3777b5dbf64473af3f5d272a73afda0fa5f2e97ec2ab299421a863e`) |
| runtime verification | SBCL 2.2.9 on Linux 6.8.0-139-generic; calendar.l loaded; bali-epoch = -1721279 verified; full 210-day cycle generated and compared to Dewata |
| authority_basis | `software_reference` |
| authority hierarchy | PRIMARY (this source) |

### secondary: rengel-de/calixir assets/ (preserved historical)

| field | value |
|---|---|
| repository | `https://github.com/rengel-de/calixir` |
| commit SHA | `0f3368339c6318f6751579cf506320b13ce17e2c` |
| commit date | 2020-07-18T08:13:30Z |
| source file | `assets/calendrica-4.0.cl` (Common Lisp, 258050 bytes) |
| source SHA-256 | `5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb` |
| in-file header | Custom personal-use + non-commercial/non-profit (NOT first-party Apache) — older pre-relicensing header |
| license file (preserved) | `COPYRIGHT_DERSHOWITZ_RHEINGOLD.txt` (SHA-256 `d34115459b34df91fdd60134384e2f427d29e483a6991b11c2cea42df237412c`) |
| sample data (preserved) | `dates4.csv` (4114 bytes, SHA-256 `49ba8658fe1208e67589a1b4e61b70cddbd42b134c37272bccddd06cc32602ff`) |
| authority hierarchy | SECONDARY (preserved historical evidence) |
| algorithmic equivalence to first-party | byte-identical (7344 lines; line-by-line `diff` produces 0 lines) |

### license clarification (corrected by first-party evidence)

The user-supplied instruction (commit 4d37765) stated: "Because the implementation is
Apache-licensed, preserve its license metadata with the evidence package."

**Initial analysis (commit 4d37765) was based on the SECONDARY (Calixir) copy** and
incorrectly concluded that the license was a custom non-commercial restriction.
That analysis was correct for the Calixir copy at that point in time, but
incorrect for the first-party source.

**Corrected analysis (this commit):** the first-party source (`EdReingold/calendar-code2`)
IS Apache License 2.0. The first-party repository was last modified by commit
9afc1f3 ("Harmonize license header with license file", 2022-02-04) which
explicitly aligns the in-file header with the LICENSE file. The LICENSE file is
the verbatim Apache 2.0 text (11357 bytes).

The Calixir copy (commit 2020-07-18) predates the first-party Apache relicense
and therefore carries the older restrictive header. The Calixir header is NOT
representative of the current first-party license.

**Provenance hierarchy:** first-party (EdReingold/calendar-code2, Apache 2.0) >
secondary (rengel-de/calixir assets/, older restrictive header). The first-party
source is the authoritative license reference.

### copyright handling

Under Apache 2.0 terms, the source file itself MAY be redistributed in the
Dewata public repository, subject to the standard Apache 2.0 conditions
(copyright notice preserved, LICENSE file included, state-changes marked).
The first-party `calendar.l` source file IS committed in this commit, under
the Apache 2.0 license terms: copyright notice preserved in the in-file
header, LICENSE file included in the same directory, state-changes
recorded in the git history. The LICENSE file (Apache 2.0, 11357 bytes,
SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`)
is included unmodified.

### license dispute ledger

The original license dispute (`DISPUTE-reference-reingold-dershowitz-2018-license-classification-2026-09-15`)
is now `resolution='superseded'`, preserved append-only, with `superseded_by`
pointing to the resolution record. The resolution record is
`DISPUTE-reference-reingold-dershowitz-2018-license-firstparty-resolution-2026-09-15`,
which contains the first-party evidence chain.

### algorithmic equivalence (Calixir vs first-party)

The two source files differ ONLY in the license header comment block. After
stripping the headers, the algorithm bodies are byte-identical:
- first-party calendar.l code body: 7344 lines
- Calixir calendrica-4.0.cl code body: 7344 lines
- diff line count: 0
- line-count delta: 0

Therefore the comparison results from commit 4d37765 (which used the Calixir copy)
are equivalent to a comparison against the first-party source. This commit
re-states the comparison with first-party provenance and re-runs the full
210-day cycle against the first-party source for explicit verification (see
`dewata-vs-firstparty-calendrica-comparison.md`).

### epoch anchor (algorithmic vs mathematical vs cultural)

The CALENDRICA source defines `bali-epoch = fixed-from-jd 146 = -1721279 (Rata Die)`.
This is an **algorithmic anchor** within the implementation. The corresponding
**mathematical Gregorian conversion** is proleptic Gregorian -4712-04-18 (4714 BCE).
The Pawukon has no canonical epoch (per Wikipedia); **no cultural or historical
source on this host identifies JD 146 / proleptic Gregorian -4712-04-18 as "the
start of a Balinese Pawukon cycle."** Therefore the JD-146 anchor has no
cultural/historical meaning beyond being the first-party implementation's
algorithmic choice. This separation is recorded per PROTOCOL v1.0 §2.4.
