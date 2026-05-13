"""Market-agreement type vocabulary (subset of ENTSOE's Contract_MarketAgreement.Type codelist).

Values are DB-friendly names so the enum serializes directly to Postgres/JSON
without translating from the ENTSOE wire codes (A01/A05/...).
"""

from enum import Enum


class MarketAgreementType(str, Enum):
    """ENTSOE Contract_MarketAgreement.Type discriminator subset."""

    DAY_AHEAD = "DAY_AHEAD"  # A01: cleared day-ahead schedule.
    TOTAL = "TOTAL"  # A05: finalised total schedule (DA + ID + balancing).


__all__ = ["MarketAgreementType"]
