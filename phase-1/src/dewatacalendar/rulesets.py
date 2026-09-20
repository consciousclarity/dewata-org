"""ruleset version lock + metadata.

The engine ships with ruleset v0.1, frozen. bumps require a new conformance
corpus pass and a new ruleset id.
"""

from __future__ import annotations

RULESET_VERSION = "pawukon-v0.4.1+saka-bali-v0.2.3+wewaran-v0.3.0+rahinan-v0.2.0"

RULESET_METADATA: dict[str, dict[str, object]] = {
    "pawukon": {
        "version": "v0.4.1",
        "epoch": "1981-08-23",
        "epoch_pawukon_day": 1,
        "epoch_wuku_index": 1,  # Sinta on day 1
        "reference": "Dershowitz & Reingold, Calendrical Calculations, ch. 11",
    },
    "saka": {
        "version": "saka-bali-v0.2.3",
        "epoch_gregorian": "1979-03-29",
        "epoch_saka_year": 1901,
        # pangunalatri is NOT implemented. the 63-day cycle and its
        # `is_pangunalatri` flag were removed from saka.py as unvalidated
        # arithmetic: the flag was a plain modulo over days-since-epoch and
        # no eligible source establishes the period. the declared figure is
        # kept here as a record of what v0.2.3 claims -- deliberately not
        # under an active-parameter name -- so `dewatacalendar ruleset`
        # reports the claim and reports that the engine does not honor it.
        "pangunalatri_implemented": False,
        "pangunalatri_days_declared": 63,
        "nampih_threshold_months": (12, 11),
        "nampih_rule": "prevent Tilem Kapitu from falling in gregorian December",
        "reference": "Igarashi bali saka calculation; Cunningham 1994",
    },
    "wewaran": {
        "version": "v0.3.0",
        "urip_5_day": (9, 7, 4, 8, 5),
        "urip_7_day": (5, 4, 3, 7, 8, 6, 9),
        "urip_10_day": (5, 2, 8, 6, 4, 7, 10, 3, 9, 1),
        "reference": "Wikipedia Pawukon, Dershowitz & Reingold",
    },
    "rahinan": {
        "version": "v0.2.0",
        "named_days": 24,
        "purnama_counted": True,
        "tilem_counted": True,
        "reference": "Eiseman 1989, Bali handbook",
    },
}
