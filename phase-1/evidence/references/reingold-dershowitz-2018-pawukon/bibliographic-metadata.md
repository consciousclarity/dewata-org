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

## first-party CALENDRICA 4.0 source — supplementary evidence

In addition to the scholarly chapter metadata, this evidence package archives
**first-party algorithm implementation evidence** retrieved from the authors'
Common Lisp source CALENDRICA 4.0.

| field | value |
|---|---|
| source file | `calendrica-4.0.cl` (Common Lisp, 258050 bytes) |
| source SHA-256 | `5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb` |
| retrieved from | `https://github.com/rengel-de/calixir/blob/master/assets/calendrica-4.0.cl` |
| repo commit SHA | `0f3368339c6318f6751579cf506320b13ce17e2c` |
| repo commit date | 2020-07-18T08:13:30Z |
| retrieval date | 2026-09-15 |
| license | custom personal-use + non-commercial/non-profit reuse (NOT Apache) |
| license SHA-256 | `d34115459b34df91fdd60134384e2f427d29e483a6991b11c2cea42df237412c` |
| license file | `calendrica-source/COPYRIGHT_DERSHOWITZ_RHEINGOLD.txt` |
| redistribution | NOT REDISTRIBUTED — license clause 1 prohibits making the source "accessible, used, or available to others" |
| sample data | `calendrica-source/dates4.csv` (4114 bytes, SHA-256 `49ba8658fe1208e67589a1b4e61b70cddbd42b134c37272bccddd06cc32602ff`) |
| sample data reference | "Sample values for the functions (useful for debugging) are given in Appendix C of the book" — LICENSE file last paragraph |
| runtime verification | SBCL 2.2.9 on Linux 6.8.0-139-generic; CALENDRICA loaded and 10 sample rows verified against dates4.csv |
| authority_basis | `software_reference` |

### license clarification (chat-vs-evidence correction)

The user-supplied instruction stated: "Because the implementation is
Apache-licensed, preserve its license metadata with the evidence package."

**This is incorrect.** The CALENDRICA 4.0 license is **NOT Apache**. It is a
custom license that grants:

- Personal use (copy + backup)
- Non-commercial, non-profit re-use with prominent credit

And **prohibits**: "any other uses, including without limitation, allowing the
code or its output to be accessed, used, or available to others."

The authors' public-service intent is described in the LICENSE file as "more
liberal than suggested by the License below, as are their licensing policies
for otherwise nonallowed uses such as ... commercial, web-site, and
large-scale academic contexts. Please see the web-site
http://www.calendarists.com for all uses not authorized below; in case there
is cause for doubt about whether a use you contemplate is authorized, please
contact the Authors (e-mail: reingold@iit.edu)."

This license does **not** permit redistribution of the full source code to a
public repository, so the source file itself is **NOT committed** to the
Dewata git repository. Instead:

- The source's SHA-256 is recorded
- The retrieval URL is recorded
- The license file IS committed (it is the author's license grant, explicitly
  intended to be redistributed with the code, and is necessary to communicate
  the licensing terms)
- The sample data file (`dates4.csv`) IS committed because the LICENSE itself
  directs users to the sample values in Appendix C of the book — the CSV file
  is the canonical digital form of those Appendix C values

This license clarification is recorded in the dispute ledger under
`DISPUTE-reference-reingold-dershowitz-2018-license-classification` because
the original chat-described license (Apache) is incompatible with the actual
license (custom personal-use + non-commercial/non-profit).
