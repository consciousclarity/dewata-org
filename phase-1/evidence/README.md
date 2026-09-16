# phase-1/evidence/ — Canonical Evidence Archive

This directory is the canonical evidence archive per Hermes Operating
Protocol v1.0 §2.7. Any evidence cited by an audit, release, dispute,
or other permanent artifact must live here (with SHA-256 hashes where
the file is binary or large), not in `/tmp`.

**Status as of 2026-09-15:** empty. Per the gap analysis
(`phase-1/docs/audit/GAP_ANALYSIS_v1.0_2026-09-15.md`, Findings 6
and 8), the following evidence was originally captured during
retrieval as transient working copies and should be promoted here when
remediation is approved:

- `/tmp/cross-2026-09.jsonl` — 30-day × 4-impl cross-validation output
- `/tmp/kb-2026-09.json` — kalenderbali.info parsed day cells (15 vectors)
- `/tmp/kb-org-2026-09.json` — kalenderbali.org parsed day cells (30 vectors)
- `/tmp/refs/*.html` (transient retrieval copies — not durable evidence storage)
- `/tmp/repos/*` (transient cloned reference implementations)

NOTE: per the v3.0-post-stabilization `/tmp/refs/` policy
(2026-09-16), `/tmp/` is scratch space only and `/tmp/refs/` is not
durable evidence storage. The files at `/tmp/refs/` (when present)
are transient retrieval copies used during verification. The
canonical evidence record is the committed URL + SHA-256 + access
date + minimum quotation/metadata as listed in each evidence
package's manifest. This README is being updated to reflect that
policy.

Per PROTOCOL §2.7, citation keys for these references follow the
`AuthorYearShortTitle` pattern (lowercase, hyphen-separated):

- `KalenderBali-Org-2026-09`
- `KalenderBali-Info-2026-09`
- `Peradnya-Balinese-Date-JS-Lib-0.4.3`
- `Edysantosa-Saka-Calendar-2.0`
- `SHA888-Balinese-Calendar-0.3.0`
- `Wikipedia-Balinese-Pawukon-Calendar`
- `Wikipedia-Balinese-Saka-Calendar`
- `Babadbali-Pewarigaan-Pawukon`
- `Babadbali-Pewarigaan-Saptawara`
- `Babadbali-Pewarigaan-Pancawara`
- `Cambridge-Dershowitz-Reingold-Pawukon-Ch-11` (abstract only, paywall)
- `PPID-Karangasem-Aneka-Tarikh`

No files have been moved here yet. The directory exists per PROTOCOL
§2.7 but contents are pending governance-owner approval of the gap
analysis remediation order.
