# Source-dependency graph

Independent attestation lineages:

| lineage | sources |
|---|---|
| L1: kb.org practitioner + media derivatives | kb.org, liputan6.com, detik.com, pelajahin.com, kalenderbali.online |
| L2: Wikipedia encyclopedia + derivatives | wikipedia:Pawukon_calendar, lydiaa.bnb.dweb3.wtf, grokipedia.com |
| L3: BASAbali community wiki | basaibubali.org |
| L4: First-party software | EdReingold/calendar-code2 |
| L5: Academic publication | I.B. Suparta Ardhana, Pokok-Pokok Wariga (2006) |

Edges (dependency relationships):
  lydiaa.bnb.dweb3.wtf -> wikipedia:Pawukon_calendar
  grokipedia.com -> wikipedia:Pawukon_calendar
  liputan6.com -> kb.org
  detik.com -> kb.org
  pelajahin.com -> kb.org
  kalenderbali.online -> kb.org

Provenance lineage for each of the 7 reference dates in this analysis:

| date | primary source | lineage | cross-confirmations (same lineage) |
|---|---|---|---|
| 2026-09-01 | kb.org page title | L1 | none |
| 2026-09-05 | liputan6 + kb.org | L1 | liputan6 article text; kb.org page title |
| 2026-09-09 | kb.org + 4 sources | L1 | liputan6, detik, pelajahin |
| 2026-09-15 | kb.org + liputan6 | L1 | liputan6 article text |
| 2026-09-17 | kb.org page title | L1 | none |
| 2026-09-26 | kb.org + liputan6 | L1 | liputan6 article text |
| 2026-09-30 | kb.org + detik | L1 | detik article text |

Independent lineage attestations for the 7 reference dates: 1 (L1 only).

Independent lineage attestations for the Pancawara convention (1=Umanis):
  - L1 (kb.org): all 7 dates confirm Umanis-Paing-Pon-Wage-Kliwon order
  - L5 (Suparta Ardhana, Pokok-Pokok Wariga, 2006, page 12): lists 'Anggara Wage' for Pahang (matches convention)
  - L3 (BASAbali): formula (uku*7+saptawara)/5 → 1=Umanis, 2=Pahing, ...
  - 3 independent lineages confirm the cultural convention

Independent lineage attestations for the irregular Caturwara/Astawara/Sangawara special-case structure:
  - L4 (CALENDRICA): implements special case in source code
  - Dewata: implements simple day-72/73 special case
  - L2 (Wikipedia mirror): describes special case in prose
  - L3 (BASAbali): uses simple modular arithmetic WITHOUT special case
  - No independent academic (L5) attestation retrievable from this host

Recommendation per user instruction: obtain independent Wuku evidence from sources with independent provenance (L2 or L5).
