# SIGNOFF.md — customary sign-off log

> this file records which customary authorities have signed off on a ruleset.
> a ruleset is "released" only when at least one customary sign-off is here.

## Definitions

  - **customary authority**: a person or institution whose customary
    standing gives them weight to attest a calendrical decision. examples:
    bendesa adat, pemangku Keramas of a major pura, Klian Adat of a known
    banjar.

  - **sign-off**: a dated entry below. the entry carries the customary
    authority's name, role, jurisdiction, and a note describing what they
    confirmed.

  - **mirror verification**: the signatory's published-key signature
    confirms their entry as a signed record. mirror partners see this in
    `disputes.json` resolution history.

## Sign-offs

(none recorded for v0.1)

---

### how to record a sign-off

```
YYYY-MM-DD  name              role            jurisdiction  confirmed_for
            (e.g. I Wayan Sudirta, pemangku Keramas, pura saraswati ubud)
            ruleset        : pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0
            notes          : <what they confirmed>
            signature_fingerprint: <their-key-hash>
            mirror_seen_at: YYYY-MM-DD  (when mirror partner recorded this)
            ...
```

human reviewers fill these in. do not auto-populate.
