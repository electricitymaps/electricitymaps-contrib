"""ATC type vocabulary.

Discriminates the capacity-calculation methodology that produced an
`ExchangeCapacity` ATC value, since multiple methodologies share the same
storage table. Values follow CACM Regulation 2015/1222 terminology:

- **Coordinated NTC (CNTC)**: bilateral ATC computed directly by the relevant
  Capacity Calculation Region (Core external borders, Nordic CCR, Baltic CCR,
  Italy-North CCR, etc.).
- **Shadow auction**: the FBMC fallback procedure (CACM Art. 51). Used by
  flow-based CCRs (today: Core internal day-ahead). The bilateral ATC value
  is derived from the flow-based domain to support a fallback explicit
  auction when the main implicit clearing can't produce a result.

Lives in the types lib — not in `electricitymap.contrib.lib.models.events`
— because it's expected to be imported by multiple packages across both
contrib and the monorepo (parsers, storage layer, downstream services).
"""

from enum import Enum


class AtcType(str, Enum):
    """ATC capacity-calculation methodology discriminator.

    Extend by adding the matching value as new ATC publication mechanisms
    emerge (e.g. explicit forward-allocation ATC).
    """

    SHADOW_AUCTION = "SHADOW_AUCTION"  # CACM Art. 51 FBMC fallback procedure.
    COORDINATED_NTC = "COORDINATED_NTC"  # CACM Coordinated NTC methodology.


__all__ = ["AtcType"]
