"""Balinese calendrical engine — deterministic, versioned.

The engine converts a Gregorian date to the full set of Balinese calendrical
components and back. It is deterministic for an input and a ruleset version:

    for fixed input + ruleset, the output is bit-for-bit reproducible

## Two parallel cycles

* **Pawukon** — 210-day repeating cycle. No leap day, no astronomy.
* **Saka** — lunisolar. Adjusts with **nampih sasih** (intercalary month).

## Wewaran

Ten concurrent weeks of length 1..10 days running through every 210-day cycle.
Some weeks require padding (the 4-day, 8-day, and 9-day weeks) because 210 is
not divisible by those lengths.

## Module order

    pawukon.py        — 210-day cycle, position lookup
    wewaran.py        — 10 concurrent cycles, derived from pawukon position
    saka.py           — saka year + sasih indexing (lunisolar unvalidated)
    rahinan.py        — named ceremony days derived from above
    rulesets.py       — frozen rule versions
    conformance.py    — vector harness
"""

__version__ = "0.1.0"
