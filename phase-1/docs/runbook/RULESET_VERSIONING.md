# Ruleset Versioning Runbook — culture-first considerations

> this runbook governs how `dewatacalendar.rulesets.RULESET_VERSION` is bumped.

## Why a runbook, not a script

a Balinese calendrical ruleset carries *cultural* authority, not just engineering. when we change a rule, the meaning of a date could shift for every banjar using it. a runbook ensures human review and provenance, not a blind CI step.

## The seven invariants (must hold for any ruleset to ship)

### 1. Cultural sovereignty

A ruleset bump does not silently change the meaning of any piodalan, odalan, or rahinan that any banjar has already published against an earlier ruleset. **every prior version remains queryable as a frozen archive.**

If a banjar published a piodalan under `pawukon-v0.4.1+saka-bali-v0.2.3` for "23 September 2026, Buda Kliwon", then `pawukon-v0.4.2+saka-bali-v0.2.4` must agree with that historical record. If the new ruleset disagrees, the banjar's published record is preserved **as-published** (immutable).

### 2. Authority ordering

The ruleset metadata records which authorities were consulted for the new ruleset:

  - **academic / scholarly**: e.g. Cunningham 1994, Igarashi 1999
  - **customary authority**: e.g. bendesa adat, pemangku Keramas of a major pura
  - **observer / international**: e.g. akademisi Undwi

A ruleset must list at least one customary authority.

### 3. Cross-validation

A new ruleset must run against **every** published-source corpus in `conformance/published/`. Disagreements must be classified (`epoch_offset` / `rule_drift` / `calendar_variant`) and either resolved or accepted as documented variants.

Disagreements are recorded in `docs/runbook/disputes.json` with full provenance.

### 4. Conformance corpus rebaseline

A ruleset bump regenerates the self-consistent corpus (`conformance/pawukon.json`, `pawukon_extended.json`, etc.). The corpus name remains stable — the version is recorded inside each vector.

### 5. Append-only history

Every published ruleset remains in `git history` forever. **no `git rebase` on ruleset files.** This is enforced by `RULESET_VERSION` being a string constant in source, and any change to it produces a new commit, not a re-write.

### 6. Mirror-redundancy at release time

A ruleset release is announced to every banjar mirror at least **14 days** before public deployment. Banjars that fail to respond are recorded as `silent` but the deployment proceeds.

### 7. Indikator perubahan terlihat

A ruleset bump changes nothing about a date's *meaning* unless explicitly called out:

  - if you change the wuku/Sasih mapping, the runbook must say "wuku interpretation changes for dates after X"
  - if you change the wuku-Sasih conversion rule, the runbook must say "Sasih mapping for Y changes"
  - if the ruleset is *only* an arithmetic correction, the runbook must say "no observable change"

## The bump procedure

```
1. verify need                         # has a dispute been classified as `rule_drift`?
2. draft change in source                # pawukon.py / saka.py / wewaran.py
3. update rulesets.py                    # bump RULESET_VERSION
4. update docs/runbook/CHANGELOG.md      # note the change in indonesian
5. run cross-validation                  # `python -m dewatacalendar validate`
6. classify every new dispute             # auto-classified, manual review
7. regenerate self-consistent corpus     # `python tests/gen_corpus.py --all`
8. add a propagation window entry         # docs/runbook/rollout.md
9. commit with `ruleset: <new-id>` prefix # never rebase
10. announce to banjar mirrors            # 14-day notice
11. tag the release                       # git tag v0.x.y
12. archive the prior ruleset             # docs/runbook/archive/
```

## the format for ruleset version strings

```
pawukon-v{MAJOR.MINOR.PATCH}+saka-bali-v{MAJOR.MINOR.PATCH}+wewaran-v{MAJOR.MINOR.PATCH}+rahinan-v{MAJOR.MINOR.PATCH}
```

each component is independent. a `saka-bali` bump does not require a `pawukon` bump.

current ruleset (v0.1):

```
pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
```

## what changes look like in source

```
# pawukon.py — when bumping:
-from .rulesets import RULESET_VERSION  # 0.4.1
+from .rulesets import RULESET_VERSION  # 0.4.2

# rulesets.py:
-    "version": "v0.4.1",
+    "version": "v0.4.2",
+    "changed_in_v0.4.2": "<change description>",
```

every change entry must be in indonesian, suitable for direct paste to banjar operators.

## The Sign-off Rule

A ruleset bump is published only after **at least one customary authority** confirms it. The confirmation is recorded in `docs/runbook/SIGNOFF.md` with:

- customary authority identity
- date of sign-off
- their signature's verification against the mirror-chain
- any territory specific caveats

A ruleset bump without customary sign-off is *not* a release; it's a draft, and the draft is invisible to mirror-partners.

## Why this is bigger than typical software versioning

A Balinese calendrical ruleset carries *civic weight*. A buggy release could re-date piodalans, miscalculate sasih boundaries, and undermine the trust that banjars place in the platform. Versioning-as-process rather than versioning-as-tag protects the trust relationship.

A bad `npm version` causes a small outage. A bad `pawukon-v0.4.x` causes a cultural-records outage for every banjar that depended on the platform for the period the bad version was active. **The cost of being wrong is asymmetric.** Hence the runbook.
