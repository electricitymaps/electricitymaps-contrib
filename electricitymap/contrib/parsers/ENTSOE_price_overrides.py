from datetime import datetime
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.parsers import ENTSOE
from electricitymap.contrib.types import ZoneKey

from .lib.exceptions import ParserException

# Zones that do not have their own ENTSOE bidding zone domain for
# day-ahead prices, mapped to the domain they share instead.
PRICE_DOMAIN_OVERRIDES: dict[str, str] = {
    "AX": ENTSOE.ENTSOE_DOMAIN_MAPPINGS["SE-SE3"],
    "LU": ENTSOE.ENTSOE_DOMAIN_MAPPINGS["DE-LU"],
}


@ENTSOE.refetch_frequency(ENTSOE.DEFAULT_LOOKBACK_HOURS_REALTIME)
def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Gets day-ahead price for a zone via the ENTSOE domain it shares with another zone."""
    if not session:
        session = Session()

    domain = PRICE_DOMAIN_OVERRIDES[zone_key]
    try:
        raw_price_data = ENTSOE.query_price(
            domain, session, target_datetime=target_datetime
        )
    except Exception as e:
        raise ParserException(
            "ENTSOE_price_overrides.py",
            f"Failed to fetch price for {zone_key}",
            zone_key,
        ) from e
    if raw_price_data is None:
        raise ParserException(
            "ENTSOE_price_overrides.py",
            f"No price data found for {zone_key}",
            zone_key,
        )
    return ENTSOE.parse_prices(raw_price_data, zone_key, logger).to_list()
