"""Day-ahead auction vocabulary.

Several auctions can clear the same zone for the same delivery period (N2EX vs EPEX
in GB), and their prices differ, so the auction is part of a day-ahead price's
identity. Values mirror the `day_ahead_auction` Postgres enum backing
`parser_data_price_day_ahead` and must match its labels exactly.

Lives in the types lib so the parsers and the storage layer share one definition.
"""

from enum import Enum


class DayAheadAuction(str, Enum):
    """The auction that cleared a day-ahead price.

    Postgres enum values can be appended but never renamed or removed, so extend
    by adding a value — never repurpose an existing one.
    """

    SDAC = "SDAC"  # Single Day-Ahead Coupling (EU + NO).
    EPEX_GB_DA = "EPEX_GB_DA"
    EPEX_GB_HH = "EPEX_GB_HH"
    NORDPOOL_N2EX_DA = "NORDPOOL_N2EX_DA"
    NORDPOOL_GB_HH = "NORDPOOL_GB_HH"
    EPEX_CH_DA = "EPEX_CH_DA"
    SEMOPX_DA = "SEMOPX_DA"  # IE, GB-NIR.
    SEEPEX_DA = "SEEPEX_DA"  # RS.
    ALPEX_DA = "ALPEX_DA"  # AL, XK.
    BELEN_DA = "BELEN_DA"  # ME.
    MEMO_DA = "MEMO_DA"  # MK.
    UA_MO_DA = "UA_MO_DA"  # UA.
    JEPX_DA = "JEPX_DA"  # JP-*.
    EPIAS_DA = "EPIAS_DA"  # TR.


__all__ = ["DayAheadAuction"]
