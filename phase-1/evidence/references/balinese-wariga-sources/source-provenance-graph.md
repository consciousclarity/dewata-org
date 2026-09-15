# Source Provenance Graph — Balinese Wariga Sources

Compiled: 2026-09-15.

This graph shows which Balinese Wariga sources are **independent** and which are **derivative**.

```
                         ┌─────────────────────────────────────────┐
                         │  S1. Pokok-pokok Wariga                 │
                         │  I.B. Suparta Ardhana                   │
                         │  Paramita, Surabaya, 2006               │
                         │  ISBN-10: 979722242X, LCCN: 2007308755  │
                         │  [printed book, not on web]             │
                         └────────────┬────────────────────────────┘
                                      │ (cited as source)
                                      │
                                      ▼
                         ┌─────────────────────────────────────────┐
                         │  S2. Tenung Wariga                      │
                         │  I.B. Putra Manik Aryana                │
                         │  Bali Aga, Denpasar, 2009               │
                         │  [printed book, not on web]             │
                         └────────────┬────────────────────────────┘
                                      │
                                      │ (both cited as reference)
                                      ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  S3. edysantosa/sakacalendar                                 │
        │  Java implementation, Apache 2.0/LGPL-2.1                   │
        │  https://github.com/edysantosa/sakacalendar                  │
        │  ← derivative of S1+S2 (one lineage)                        │
        └─────────────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────────────────┐
        │  S4. Kemendikbud Hindu-BS-KLS-IX (2022)                     │
        │  Indonesian Ministry of Education + Religious Affairs        │
        │  https://static-sc.cloudapp.web.id/content/pdf/bukuteks/...   │
        │  ← independent academic/government lineage                  │
        └─────────────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────────────────┐
        │  S5. babadbali.com                                           │
        │  https://www.babadbali.com                                  │
        │  ← independent cultural reference lineage                   │
        │      │                                                     │
        │      └──▶ peradnya/balinese-date-js-lib (TypeScript)        │
        │           ← derivative of S5 (same lineage)                 │
        └─────────────────────────────────────────────────────────────┘
```

## Independence matrix

| Source pair | Independent? | Note |
|---|---|---|
| S1 ↔ S4 | YES | S1=Paramita printed book; S4=Ministry textbook |
| S1 ↔ S5 | YES | S1=printed book; S5=website |
| S4 ↔ S5 | YES | S4=academic textbook; S5=cultural reference site |
| S3 ↔ any | NO | S3 explicitly cites S1+S2 as its source |
| peradnya ↔ S5 | NO | derivative of S5 |
| kb.org ↔ S4 | YES | L1=practitioner calendar; S4=academic textbook |
| kb.org ↔ CALENDRICA | YES | L1=practitioner site; L4=academic software |
| CALENDRICA ↔ S3 | NO-ish | independent implementation, but S3 cites Pokok-pokok Wariga |

## Per-claim independent lineage count

| Claim | Independent Balinese lineages |
|---|---|
| Wuku/Gregorian phase | 1 (kb.org L1) — INSUFFICIENT |
| Pancawara ordering | 4 (S4, S5, basaibubali, kb.org) |
| Caturwara special-case exists | 3 (S4, S3, L4) |
| Caturwara specific content | 3 disagree (S4=Jaya, S3=Jaya, L4=Sri/Indra/Guru; basaibubali=simple) |
| Astawara special-case exists | 3 (S4, S3, L4) |
| Astawara specific content | 3 disagree (S4=Kala, S3=Kala, L4=Indra/Guru; basaibubali=simple) |
| Sangawara special-case exists | 3 (S4, S3, L4) |
| Sangawara duration (3 vs 4) | S4=4, S3=4, L4=3 (S4+S3 vs L4) |
| Dasawara derivation | 2 (S3, L4) — agree |
| Dwiwara derivation | 2 (S3, L4) — agree |

## Conclusion

**Multiple traditions exist** for:
- Caturwara special-case content (S4/S3=Jaya vs L4=Sri/Indra/Guru vs basaibubali=simple)
- Astawara special-case content (S4/S3=Kala vs L4=Indra/Guru vs basaibubali=simple)
- Sangawara duration (S4/S3=4 days vs L4=3 days vs basaibubali=simple)

**Single tradition** (3-way agreement on urip_sum mod 10) for:
- Dasawara derivation
- Dwiwara derivation (urip_sum parity)

**Insufficient independent evidence** for:
- Wuku/Gregorian phase mapping (only kb.org)

Per user instruction: "If authoritative/reputable Balinese sources themselves disagree, preserve the disagreement."

Per PROTOCOL v1.0: "Multiple legitimate traditions" must be recorded explicitly without forced consensus.

---

## What would resolve disputes

1. **S1 chapter text access** (printed book — would require purchase or institutional library)
2. **S2 chapter text access** (printed book — same)
3. **Independent Wuku/Gregorian examples** from printed Kalender Bali with publication provenance
4. **Customary authority attestation** (per user instruction: "do not implement without customary sign-off")
