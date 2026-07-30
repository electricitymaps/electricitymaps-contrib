#!/usr/bin/env python3

"""
Parser for the JAO (Joint Allocation Office) Auction API.

Endpoint: https://api.jao.eu/OWSMP/getauctions
Docs: https://www.jao.eu/sites/default/files/2021-11/API_User_Guide_v1.0.pdf
Auth: AUTH_API_KEY header (set via JAO_AUCTION_API_KEY env var)

This is a different API from the JAO Publication Tool (JAO.py), and shares little
with it beyond the vendor name:

1. Explicit auctions are per *corridor*, not per border, and several physical
   corridors can make up one EM border — each needs its own call, and their ATC
   values are summed per datetime.
2. `getauctions` answers HTTP 400 `{"status":400,"message":"No Data found"}` rather
   than an empty 200 when a corridor has nothing in the window.
3. Timestamps are not UTC. `marketPeriodStart` is the start of the *local* (CET/CEST)
   market day, and `productHour` is a local wall-clock label — see
   `_auction_hourly_atc` for why that matters.
4. A window may span 31 days (the Publication Tool caps at 2).

Corridor naming is `{PREFIX}{FROM}-{TO}`, where `PREFIX` identifies the physical
interconnector and is only present where several cables share a border:
  IF1-FR-GB   IFA1, capacity FR→GB          CH-DE   Swiss borders carry no prefix
  VKL-D1-GB   Viking Link, capacity DK1→GB  DE-CH
The full list is available from `GET /OWSMP/getcorridors`.

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

# The Auction API rejects windows longer than 31 days (user guide §5.1), and
# `_target_window` spends one of them reaching back for the target day's own auction,
# leaving 30 days of forward coverage per call.
JAO_AUCTION_MAX_WINDOW_DAYS = 31
JAO_AUCTION_MAX_FETCH_DAYS = JAO_AUCTION_MAX_WINDOW_DAYS - 1

# Returned as the body of an HTTP 400 when a corridor has no auction in the window.
NO_DATA_MESSAGE = "no data found"

BASE_URL = "https://api.jao.eu/OWSMP"


class JaoHorizon(str, Enum):
    """Auction horizons served by the API (`GET /OWSMP/gethorizons`)."""

    DAY_AHEAD = "Daily"
    INTRADAY = "Intraday"

    def __str__(self) -> str:
        return self.value


# EM exchange zone key → the corridor prefixes making up that border. A single
# empty prefix means the border is served by one unprefixed corridor per direction.
# Borders absent from this mapping are not available on the Auction API.
#
# This is every border where JAO runs a *daily* explicit auction, i.e. where day-ahead
# capacity is not implicitly allocated by market coupling: GB (post-Brexit), CH (never
# coupled), and the non-SDAC Balkan and Ukrainian borders. Borders inside SDAC have
# corridors registered here too, but only for long-term products — their day-ahead ATC
# comes from the Publication Tool (JAO.py) instead, so the two parsers never overlap.
# `GET /OWSMP/getcorridors` lists all corridors; probe `horizon=Daily` to see which
# actually carry day-ahead auctions.
EM_ZONE_TO_JAO_PREFIX: dict[str, list[str]] = {
    # GB borders are the only ones where several cables share a border, so each
    # physical interconnector has its own prefixed corridor.
    "BE->GB": ["NLL-"],  # Nemo Link
    "DK-DK1->GB": ["VKL-"],  # Viking Link
    "FR->GB": ["IF1-", "IF2-", "EL1-"],  # IFA1, IFA2, ElecLink
    # Everything else is a single unprefixed corridor per direction.
    "AT->CH": [""],
    "BG->MK": [""],
    "BG->RS": [""],
    "CH->DE": [""],
    "CH->FR": [""],
    "CH->IT-NO": [""],
    "HR->RS": [""],
    "HU->RS": [""],
    "HU->UA": [""],
    "IT-CSO->ME": [""],
    "ME->RS": [""],
    "MK->RS": [""],
    "PL->UA": [""],
    "SK->UA": [""],
}

# EM zone key → JAO zone code used in corridor names (only where they differ).
# NOTE: the Auction API and the Publication Tool use *different* codes for the same
# zone — DK-DK1 is "D1" here but "DK1" in JAO.py. Both are correct for their API;
# don't "fix" the discrepancy.
EM_TO_JAO_ZONE: dict[str, str] = {
    "DK-DK1": "D1",
    # JAO uses a single "IT" code for every Italian border and lets the counterparty
    # disambiguate which bidding zone is meant: the Swiss interconnector lands in Italy
    # North, the Montenegrin one (MONITA) in Italy Centre-South. The EM→JAO direction is
    # many-to-one so a flat mapping is fine, but it cannot be inverted.
    "IT-NO": "IT",
    "IT-CSO": "IT",
}


def _em_to_jao_zone(em_zone: str) -> str:
    return EM_TO_JAO_ZONE.get(em_zone, em_zone)


def _em_zone_to_jao_prefix(em_exchange_zone: str) -> list[str]:
    """Corridor prefixes for a border, or raise if the border isn't on this API.

    Failing loudly matters: falling back to an empty prefix would silently request a
    corridor code that doesn't exist (e.g. "DE-DK") and report no data rather than a
    configuration mistake.
    """
    if em_exchange_zone not in EM_ZONE_TO_JAO_PREFIX:
        raise ParserException(
            parser="JAO_Auctions.py",
            message=f"No JAO auction corridors configured for {em_exchange_zone}",
        )
    return EM_ZONE_TO_JAO_PREFIX[em_exchange_zone]


def _format_utc(dt: datetime) -> str:
    """Format a tz-aware datetime as the `yyyy-MM-dd-HH:mm:ss` string JAO expects."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d-%H:%M:%S")


def _parse_JAO_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _target_window(
    target_datetime: datetime | None,
    days: int = JAO_AUCTION_MAX_FETCH_DAYS,
) -> tuple[datetime, datetime]:
    """Return the UTC window to request for `target_datetime`.

    The API filters on `marketPeriodStart`, which is the start of the *local* market
    day and therefore falls at 22:00/23:00 UTC on the preceding calendar day. A lower
    bound of UTC midnight would exclude the target day's own auction, so the window
    starts a day early. The extra day overlaps harmlessly on refetch, and keeps the
    total span within the API's 31-day limit.
    """
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
    elif target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    day_start = datetime.combine(
        target_datetime.astimezone(timezone.utc).date(),
        time.min,
        tzinfo=timezone.utc,
    )
    return day_start - timedelta(days=1), day_start + timedelta(days=days)


def _query_jao_auction(
    session: Session,
    from_utc: datetime,
    to_utc: datetime,
    horizon: JaoHorizon,
    corridor: str,
    logger: Logger,
) -> list[dict]:
    """Fetch every auction of one corridor in the window.

    Returns the raw auction objects, one per market day. An empty list is returned
    when the corridor has no auction in the window — the API signals that with an
    HTTP 400 rather than an empty 200, and it is routine (cable outage, or a corridor
    that only trades long-term products), so it must not fail the whole border.
    """
    url = f"{BASE_URL}/getauctions"
    params = {
        "fromdate": _format_utc(from_utc),
        "todate": _format_utc(to_utc),
        "shadow": 0,  # Explicit (non-shadow) auctions only.
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
    response = session.get(
        url,
        headers={"AUTH_API_KEY": get_token("JAO_AUCTION_API_KEY")},
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 400 and NO_DATA_MESSAGE in response.text.lower():
        logger.debug("No JAO auction data for corridor", extra={"corridor": corridor})
        return []
    if not response.ok:
        raise ParserException(
            parser="JAO_Auctions.py",
            message=f"corridor={corridor}: HTTP {response.status_code}",
        )
    return response.json() or []


def _product_hour_sort_key(product_hour: str) -> tuple[str, bool]:
    """Chronological sort key for the hourly product labels of one market day.

    Labels are zero-padded local wall-clock ranges ("00:00-01:00"), so plain string
    ordering is chronological. On the long DST day the repeated hour is suffixed with
    "*" and must sort immediately after its unsuffixed twin, being the second
    (post-transition) occurrence.
    """
    return (product_hour.rstrip("*"), product_hour.endswith("*"))


def _auction_hourly_atc(auction: dict, logger: Logger) -> dict[datetime, float]:
    """Map each hourly product of one auction to its UTC start and ATC value.

    `marketPeriodStart` is the start of the local market day expressed in UTC, and the
    products tile it one hour at a time, so the Nth product in chronological order
    starts N hours after it.

    We deliberately do not derive the offset from the `productHour` label. Labels are
    local wall-clock times, which breaks on both DST transitions: on the short day they
    skip an hour ("00", "01", "03", ...) so every later hour would land an hour late and
    the last would spill into the next market day, and on the long day "02:00-03:00" and
    "02:00-03:00*" would collapse onto a single timestamp and have their capacities
    summed. Products also arrive unsorted, so raw list position is not usable either.

    `offeredCapacity` is the ATC; JAO exposes the identical value as `products[].atc`.
    """
    start = _parse_JAO_datetime(auction["marketPeriodStart"])
    stop = _parse_JAO_datetime(auction["marketPeriodStop"])
    rows = sorted(
        auction.get("results") or [],
        key=lambda row: _product_hour_sort_key(row["productHour"]),
    )

    # Auctions are announced well before they are held, and the window reaches ~30 days
    # forward, so most of it is upcoming auctions with no results yet. Routine, not an
    # anomaly.
    if not rows:
        return {}

    # Position-based offsets are only sound if the products exactly tile the market
    # period. Bail out rather than emit rows on guessed timestamps.
    expected_hours = round((stop - start) / timedelta(hours=1))
    if len(rows) != expected_hours:
        logger.error(
            f"JAO auction {auction.get('identification')} has {len(rows)} hourly "
            f"products but spans {expected_hours} hours; skipping it"
        )
        return {}

    atc_by_datetime: dict[datetime, float] = {}
    for offset, row in enumerate(rows):
        capacity = row.get("offeredCapacity")
        if capacity is None:
            continue
        atc_by_datetime[start + timedelta(hours=offset)] = capacity
    return atc_by_datetime


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
      - Export (A→B): corridor {prefix}{jao_a}-{jao_b}  (capacity entering B)
      - Import (B→A): corridor {prefix}{jao_b}-{jao_a}  (capacity entering A)

    Values from all prefixes are accumulated into capacityExport / capacityImport.
    """
    zone_a, zone_b = sorted_zone_keys.split("->")
    prefixes = _em_zone_to_jao_prefix(sorted_zone_keys)
    jao_a = _em_to_jao_zone(zone_a)
    jao_b = _em_to_jao_zone(zone_b)

    export_by_dt: dict[datetime, float] = {}
    import_by_dt: dict[datetime, float] = {}

    for prefix in prefixes:
        for corridor, accumulator in (
            (f"{prefix}{jao_a}-{jao_b}", export_by_dt),
            (f"{prefix}{jao_b}-{jao_a}", import_by_dt),
        ):
            auctions = _query_jao_auction(
                session, from_utc, to_utc, horizon, corridor, logger
            )
            for auction in auctions:
                for dt, capacity in _auction_hourly_atc(auction, logger).items():
                    accumulator[dt] = accumulator.get(dt, 0.0) + capacity

    capacities = ExchangeAtcList(logger)
    for dt in sorted(set(export_by_dt) | set(import_by_dt)):
        export_val = export_by_dt.get(dt)
        import_val = import_by_dt.get(dt)
        if export_val is None and import_val is None:
            continue
        capacities.append(
            zoneKey=sorted_zone_keys,
            datetime=dt,
            end_datetime=dt + timedelta(hours=1),
            source=source,
            capacityExport=export_val,
            capacityImport=import_val,
            atcType=atc_type,
        )
    return capacities


@refetch_frequency(timedelta(days=JAO_AUCTION_MAX_FETCH_DAYS))
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

    Tagged AtcType.COORDINATED_NTC: these borders are NTC-based and their capacity is
    coordinated bilaterally by the two TSOs. The explicit auction is how that capacity
    is *allocated*, which is a separate axis from how it was *calculated*.
    """
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    from_utc, to_utc = _target_window(target_datetime)
    session = session or Session()
    mount_retry(session)
    return _extract_atc(
        sorted_zone_keys,
        from_utc,
        to_utc,
        JaoHorizon.DAY_AHEAD,
        session,
        SOURCE,
        logger,
        AtcType.COORDINATED_NTC,
    ).to_list()


if __name__ == "__main__":
    from pprint import pprint

    pprint(fetch_auction_atc_day_ahead(ZoneKey("FR"), ZoneKey("GB")))
