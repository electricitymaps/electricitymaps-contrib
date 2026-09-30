"""ATC type vocabulary.

Discriminates how an ATC value was allocated, since several mechanisms share the
same storage table and **must not be interpreted the same way**. Every value is
"remaining directional capacity after prior allocations" — they differ in whether
that number constrains physical flow, which is what consumers care about:

- **Coordinated NTC (CNTC)**: bilateral ATC computed by the relevant Capacity
  Calculation Region and allocated *implicitly* by market coupling (Core external
  borders, Nordic CCR, Baltic CCR, Italy-North CCR). Coupling clears one net flow
  per border, bounded directly by these values, so each direction *is* a bound on
  physical flow. Use as published.
- **Explicit auction**: capacity sold as directional rights (PTR) that buyers then
  nominate, so physical flow is the *net* of nominations in both directions. Under
  cross-netting (JAO `xnRule=1/1`) each published value is
  `capability -/+ the net position already committed the other way`, so a single
  direction is **not** a bound — the reverse direction is inflated by whatever the
  forward direction has committed. The bound is `(export + import) / 2`.
  Borders outside SDAC: GB, CH, the Balkans, Ukraine.
- **Shadow auction**: the FBMC fallback procedure (CACM Art. 51). Used by
  flow-based CCRs (today: Core internal day-ahead). The bilateral ATC value is
  derived from the flow-based domain to support a fallback explicit auction when
  the main implicit clearing can't produce a result. On days where clearing
  succeeds — nearly all of them — the binding constraint is the flow-based domain
  across the whole region, not this per-border number, so it is a counterfactual
  and **not a bound in either form**.

Measured evidence for the three readings, and the feature recipe that follows
from them, are in DAT-477.

Lives in the types lib — not in `electricitymap.contrib.lib.models.events`
— because it's expected to be imported by multiple packages across both
contrib and the monorepo (parsers, storage layer, downstream services).
"""

from enum import Enum


class AtcType(str, Enum):
    """How an ATC value was allocated, and therefore how it may be interpreted.

    Consumers deriving a flow envelope must branch on this: CNTC is directional,
    explicit auction needs the half-sum, shadow auction is not an envelope at all.
    Extend by adding a value whenever a new allocation mechanism appears — never
    reuse an existing one for a mechanism that needs different handling.
    """

    SHADOW_AUCTION = "SHADOW_AUCTION"  # CACM Art. 51 FBMC fallback procedure.
    COORDINATED_NTC = "COORDINATED_NTC"  # CACM Coordinated NTC, implicitly allocated.
    EXPLICIT_AUCTION = "EXPLICIT_AUCTION"  # Directional rights, netted per xnRule.


__all__ = ["AtcType"]
