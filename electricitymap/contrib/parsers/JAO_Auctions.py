#!/usr/bin/env python3

"""
Parser for the JAO (Joint Allocation Office) Auction API.

Endpoint: https://api.jao.eu/OWSMP/getauctions/
Auth: AUTH_API_KEY header (set via JAO_AUCTION_API_KEY env var)

The Auction API differs from the Publication Tool (JAO.py) in two ways:
1. Each corridor is a *separate* API call — there is no single row with
   multiple border columns.
2. The response envelope is a list; data lives at json()[0]['results'].

For a given EM border, multiple physical corridors (cables/interconnectors)
contribute to the same commercial capacity. Each corridor is fetched
separately and their ATC values are summed per datetime to form
capacityExport and capacityImport.

Corridor naming: {PREFIX}-{TO_ZONE}-{HORIZON_SUFFIX}
  e.g. VKL-GB-D1  →  Viking Link, capacity entering GB (export from DK1)
       VKL-DK1-D1 →  Viking Link, capacity entering DK1 (import from GB)

Currently wired (day-ahead horizon):
- fetch_auction_atc_day_ahead  →  summed ATC across corridors for a border
"""

from datetime import datetime, time, timedelta, timezone
from enum import Enum
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ExchangeAtcList
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.session import mount_retry
from electricitymap.contrib.parsers.lib.utils import get_token
from electricitymap.contrib.types import AtcType

SOURCE = "jao.eu"
REQUEST_TIMEOUT_SECONDS = 30
JAO_MAX_FETCH_DAYS = 2

AUTH_API_KEY = get_token("JAO_AUCTION_API_KEY")

BASE_URL = "https://api.jao.eu/OWSMP"


class JaoHorizon(str, Enum):
    DAY_AHEAD = "Daily"
    INTRADAY = "Intraday"

    def __str__(self) -> str:
        return self.value


# EM exchange zone key → list of corridor prefixes (one prefix per physical cable/link).
# Borders with no prefixes are not included.
EM_ZONE_TO_JAO_PREFIX: dict[str, list[str]] = {
    "DK-DK1->GB": ["VKL-"],
    "FR->GB": ["IF1-", "IF2-", "EL1-"],
    "BE->GB": ["NLL-"],
}

# EM zone key → JAO zone code used in corridor names (only where they differ).
EM_TO_JAO_ZONE: dict[str, str] = {
    "DK-DK1": "D1",
}


def _em_to_jao_zone(em_zone: str) -> str:
    return EM_TO_JAO_ZONE.get(em_zone, em_zone)


def _em_zone_to_jao_prefix(em_exchange_zone: str) -> str:
    return EM_ZONE_TO_JAO_PREFIX.get(em_exchange_zone, [""])


def _format_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d-%H:%M:%S")


def _parse_JAO_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _target_window(
    target_datetime: datetime | None,
    days: int = JAO_MAX_FETCH_DAYS,
) -> tuple[datetime, datetime]:
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
    elif target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    day_start = datetime.combine(
        target_datetime.astimezone(timezone.utc).date(),
        time.min,
        tzinfo=timezone.utc,
    )
    return day_start, day_start + timedelta(days=days)


def _query_jao_auction(
    session: Session,
    from_utc: datetime,
    to_utc: datetime,
    horizon: JaoHorizon,
    corridor: str,
    logger: Logger,
) -> list[dict]:
    """Fetch one corridor from the JAO Auction API.

    Returns the rows from json()[0]['results'], or [] when the response is
    empty (corridor has no auction data for the requested window).
    """
    url = f"{BASE_URL}/getauctions"
    params = {
        "fromdate": _format_utc(from_utc),
        "todate": _format_utc(to_utc),
        "shadow": 0,
        "horizon": horizon.value,
        "corridor": corridor,
    }
    logger.debug(
        "Querying JAO Auction",
        extra={
            "corridor": corridor,
            "from_utc": params["fromdate"],
            "to_utc": params["todate"],
        },
    )
    mount_retry(session)
    response = session.get(
        url,
        headers={"AUTH_API_KEY": AUTH_API_KEY},
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if not response.ok:
        raise ParserException(
            parser="JAO_Auctions.py",
            message=f"corridor={corridor}: HTTP {response.status_code}",
        )
    payload = response.json()
    if not payload:
        return []
    return payload or []


def _extract_auction(
    payload: list,
) -> list[(datetime, list)]:
    """Extract all individual auctions from the JAO auction API response"""
    auction_list = []
    for auction in payload:
        dt = _parse_JAO_datetime(auction.get("marketPeriodStart"))
        rows = auction.get("results")
        auction_list.append([dt, rows])
    return auction_list


def _extract_hour_from_product_hour(
    productHour: str,
) -> int:
    """Extract the hour from the productHour"""
    return int(productHour[:2])


def _extract_atc(
    sorted_zone_keys: ZoneKey,
    from_utc: datetime,
    to_utc: datetime,
    horizon: JaoHorizon,
    session: Session,
    source: str,
    logger: Logger,
    atc_type: AtcType,
) -> ExchangeAtcList:
    """Fetch ATC for every corridor of a border and sum per datetime.

    For sorted_zone_keys "A->B":
      - Export (A→B): corridor {prefix}-{jao_a}-{jao_b}  (capacity entering B)
      - Import (B→A): corridor {prefix}-{jao_b}-{jao_a}  (capacity entering A)

    Values from all prefixes are accumulated into capacityExport / capacityImport.
    """
    zone_a, zone_b = sorted_zone_keys.split("->")
    prefixes = _em_zone_to_jao_prefix(sorted_zone_keys)
    jao_a = _em_to_jao_zone(zone_a)
    jao_b = _em_to_jao_zone(zone_b)

    export_by_dt: dict[datetime, float] = {}
    import_by_dt: dict[datetime, float] = {}

    for prefix in prefixes:
        export_corridor = f"{prefix}{jao_a}-{jao_b}"
        export_auctions = _query_jao_auction(
            session, from_utc, to_utc, horizon, export_corridor, logger
        )

        for auction in _extract_auction(export_auctions):
            auction_start, rows = auction
            for row in rows:
                hour = _extract_hour_from_product_hour(row.get("productHour"))
                dt = auction_start + timedelta(hours=hour)
                atc = row.get("offeredCapacity")
                export_by_dt[dt] = export_by_dt.get(dt, 0) + atc

        import_corridor = f"{prefix}{jao_b}-{jao_a}"
        import_auctions = _query_jao_auction(
            session, from_utc, to_utc, horizon, import_corridor, logger
        )

        for auction in _extract_auction(import_auctions):
            auction_start, rows = auction
            for row in rows:
                hour = _extract_hour_from_product_hour(row.get("productHour"))
                dt = auction_start + timedelta(hours=hour)
                atc = row.get("offeredCapacity")
                import_by_dt[dt] = import_by_dt.get(dt, 0) + atc

    capacities = ExchangeAtcList(logger)
    for dt in sorted(set(export_by_dt) | set(import_by_dt)):
        export_val = export_by_dt.get(dt)
        import_val = import_by_dt.get(dt)
        if export_val is None and import_val is None:
            continue
        capacities.append(
            zoneKey=sorted_zone_keys,
            datetime=dt,
            source=source,
            capacityExport=export_val,
            capacityImport=import_val,
            atcType=atc_type,
        )
    return capacities


@refetch_frequency(timedelta(days=JAO_MAX_FETCH_DAYS))
def fetch_auction_atc_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead ATC capacity from the JAO Auction API.

    Sums ATC across all configured corridors for the given border and returns
    an ExchangeAtcList-shaped list with capacityExport and capacityImport.
    """
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    from_utc, to_utc = _target_window(target_datetime)
    return _extract_atc(
        sorted_zone_keys,
        from_utc,
        to_utc,
        JaoHorizon.DAY_AHEAD,
        session or Session(),
        SOURCE,
        logger,
        AtcType.COORDINATED_NTC,
    ).to_list()


if __name__ == "__main__":
    from pprint import pprint

    pprint(fetch_auction_atc_day_ahead(ZoneKey("FR"), ZoneKey("GB")))
