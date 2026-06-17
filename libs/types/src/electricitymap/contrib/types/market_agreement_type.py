"""Market-agreement type vocabulary.

Subset of ENTSOE's `Contract_MarketAgreement.Type` codelist, used as a
discriminator wherever multiple clearing schedules of the same shape
share a single storage table or single domain object. Values are the
DB-friendly names (not the ENTSOE wire codes like "A01"/"A05") so the
enum can serialize directly to Postgres/JSON without a translation step.

Lives in the types lib — not in `electricitymap.contrib.lib.models.events`
— because it's expected to be imported by multiple packages across both
contrib and the monorepo (parsers, storage layer, downstream services).
"""

from enum import Enum


class MarketAgreementType(str, Enum):
    """ENTSOE Contract_MarketAgreement.Type discriminator subset.

    Extend by adding the matching value as new storage requirements emerge.
    The full ENTSOE codelist also includes A02 (week-ahead), A03
    (month-ahead), A04 (year-ahead), A07 (intraday), and others.
    """

    DAY_AHEAD = "DAY_AHEAD"  # A01: cleared day-ahead schedule.
    TOTAL = "TOTAL"  # A05: finalised total schedule (DA + ID + balancing).


__all__ = ["MarketAgreementType"]
