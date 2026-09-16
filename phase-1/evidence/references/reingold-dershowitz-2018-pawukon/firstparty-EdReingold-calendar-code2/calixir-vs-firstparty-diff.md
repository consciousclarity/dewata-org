# Calixir vs first-party CALENDRICA — comparative analysis

**Date:** 2026-09-15
**Purpose:** determine whether the Calixir copy (`assets/calendrica-4.0.cl`) of CALENDRICA 4.0 is algorithmically identical to the first-party copy (`EdReingold/calendar-code2/calendar.l`) at the authors' canonical GitHub repository.

## sources

| artifact | source | sha-256 | git blob sha-1 | license header |
|---|---|---|---|---|
| `firstparty-EdReingold-calendar-code2/calendar.l` | EdReingold/calendar-code2 commit `9afc1f3277b839db1a70c2350d6c708ac83df78f` (main, 2022-02-04) | `642ad18fef302f401f9f8d19d9ecac3d0eff800acfdd57e19835e59470e23484` | `2e4ad0f58ac52cb5fd497aa97b2b9ffe57ec623d` | Apache 2.0 (12 lines) |
| `calendrica-source/calendrica-4.0.cl` | rengel-de/calixir assets/ commit `0f3368339c6318f6751579cf506320b13ce17e2c` (master, 2020-07-18) | `5206959bd22c1542cd438ab89876cc98c9a542d56e0da829d259d6f6ef2a24cb` | (not extracted) | Custom personal-use + non-commercial/non-profit reuse (75 lines) |
| license file (first-party) | `LICENSE` (Apache 2.0) | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` | `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64` | n/a |

## whole-file comparison

| metric | value |
|---|---|
| first-party `calendar.l` size | 254735 bytes |
| Calixir `calendrica-4.0.cl` size | 258050 bytes |
| byte delta | 3315 bytes (Calixir larger) |
| diff hunk count | 1 |
| diff line count | 81 |
| changed code-body lines | 0 |

## diff detail

The single hunk spans lines 8-22 of first-party (12 lines removed) and lines 8-82 of Calixir (75 lines added). The differences are **entirely in the license header comment block** — no code lines differ.

First-party (Apache 2.0 header, 12 lines, lines 8-19):
```
;;;; limitations listed therein.  These Functions are explained in the Authors'
;;;; book, "Calendrical Calculations", 4th ed. (Cambridge University
;;;; Press, 2016), and are subject to an international copyright.
;;;;
;;;; Licensed under the Apache License, Version 2.0 <LICENSE or
;;;; https://www.apache.org/licenses/LICENSE-2.0>.
```

Calixir (custom-restrictive header, 75 lines, lines 8-82):
```
;;;; limitations below.  These Functions are explained in the Authors'
;;;; book, "Calendrical Calculations", 4th ed. (Cambridge University
;;;; Press, 2016), and are subject to an international copyright.
;;;;
;;;; The Authors' public service intent is more liberal than suggested
;;;; by the License below, as are their licensing policies for otherwise
;;;; nonallowed uses such as--without limitation--those in commercial,
;;;; web-site, and large-scale academic contexts.  Please see the
;;;; web-site
;;;;
;;;;     http://www.calendarists.com
;;;;
;;;; for all uses not authorized below; ...
;;;; 1. LICENSE.  ...
;;;; 2. WARRANTY.  ...
;;;; ...
;;;; Last modified 20 December 2016.
```

(The "Last modified 20 December 2016." line is at line 20 in first-party, line 83 in Calixir — both files agree on the date.)

## algorithmic-body comparison

Extracted each file's code-body by stripping the license header (everything up to but not including the first non-comment, non-blank line). For first-party, code starts at line 22 (`(in-package "CC4")`). For Calixir, code starts at line 85 (`(in-package "CC4")`). The bodies are **byte-identical**:

| metric | value |
|---|---|
| first-party code body length | 7344 lines |
| Calixir code body length | 7344 lines |
| diff line count | 0 |
| line-count delta | 0 |

**Conclusion:** The Calixir copy is algorithmically identical to the first-party source. The only difference is the license header — the Calixir copy was distributed with an older, more restrictive non-Apache license header that has since been superseded by the first-party Apache 2.0 header.

## license re-evaluation

| source | license header | license file in repo | license URL |
|---|---|---|---|
| first-party (EdReingold/calendar-code2) | Apache License, Version 2.0 (12 lines) | `LICENSE` file (11357 bytes, SHA-256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`) | https://www.apache.org/licenses/LICENSE-2.0 |
| Calixir (rengel-de/calixir) | Custom personal-use + non-commercial/non-profit reuse (75 lines) | none | n/a |

The first-party repository contains both an in-file Apache 2.0 header AND a separate `LICENSE` file that is the verbatim Apache 2.0 text. **The current first-party CALENDRICA 4.0 distribution is Apache License 2.0.**

The Calixir copy was made from a version of the source that predates the Apache relicensing. The commit message on the first-party repo ("Merge pull request #1 from Manishearth/header — Harmonize license header with license file", 2022-02-04) confirms that the license change is a deliberate, intentional act of the authors, not an accident.

## sample-data comparison

| source | file | size | sha-256 | git blob sha-1 |
|---|---|---|---|---|
| first-party | `dates.l` (Common Lisp script) | 12578 bytes | `d81cdfc1a3777b5dbf64473af3f5d272a73afda0fa5f2e97ec2ab299421a863e` | `e73a43b863178fbad14fd14210d7b10bd8920225` |
| Calixir | `dates4.csv` (already-computed sample data) | 4114 bytes | `49ba8658fe1208e67589a1b4e61b70cddbd42b134c37272bccddd06cc32602ff` | n/a (not in a git tree) |

The first-party `dates.l` is a Common Lisp script that calls `compute-dates` to generate the .tex files. The Calixir `dates4.csv` is a pre-computed CSV representation of the corresponding .tex output (specifically the Pawukon columns). Since the algorithm bodies are byte-identical, the sample data is reproducible from first-party by running `dates.l` against `calendar.l`.

## conclusion

The Calixir copy and the first-party copy are **algorithmically identical**. The earlier comparison results (commit 4d37765, using the Calixir copy) remain valid — they describe the same algorithm as the first-party source. However:

1. **License clarification:** the first-party source is Apache 2.0, NOT the restrictive license in the Calixir copy. The earlier license dispute (`DISPUTE-reference-reingold-dershowitz-2018-license-classification-2026-09-15`) is **superseded** by this stronger first-party evidence.

2. **Authority hierarchy:** all authoritative Pawukon claims now point to the first-party source. The Calixir copy remains as secondary/preserved historical evidence.

3. **All comparison counts are unchanged** because the algorithm bodies are byte-identical.
