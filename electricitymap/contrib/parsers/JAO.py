#!/usr/bin/env python3

"""
Parser for the JAO (Joint Allocation Office) Publication Tool.

Docs: https://publicationtool.jao.eu/PublicationHandbook/Core_PublicationTool_Handbook_v2.2.pdf
Regions:
    - Core CCR:   https://publicationtool.jao.eu/core/api
    - Nordic CCR: https://publicationtool.jao.eu/nordic/api

Every JAO dataset (Core or Nordic) is served from the same URL template per
region — `/data/<datasetName>` with `FromUtc`/`ToUtc` query params and a
`{data, rejected, messages}` envelope — so the HTTP layer is reusable. Datasets
differ only in row shape:

- Per-border (bidirectional): fields named `border_XX_YY`, one row per hour.
    e.g. shadowAuctionATC, maxExchanges
- Per-zone: one row per hour, fields per country (`maxAT`, `minDE`, ...).
    e.g. maxNetPos, referenceNetPosition
- Per-CNEC: many rows per hour, one per critical network element.
    e.g. shadowPrices, validationReductions

Currently wired:
- fetch_shadow_auction_atc_day_ahead       → Core shadowAuctionATC (per-border)
- fetch_core_external_atc_day_ahead        → Core atc (per-border, 15-min)
- fetch_core_max_exchanges_day_ahead       → Core maxExchanges (per-border, hourly)
- fetch_nordic_max_exchanges_day_ahead     → Nordic maxExchanges (per-border, 15-min)
- fetch_core_scheduled_commercial_day_ahead → Core scheduledExchanges (per-border, 15-min)
- fetch_nordic_max_border_flow_day_ahead   → Nordic maxBorderFlow (per-border, 15-min)
"""

from datetime import datetime, time, timedelta, timezone
from enum import Enum
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeCapacityForecastList,
)
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException

SOURCE = "jao.eu"
REQUEST_TIMEOUT_SECONDS = 30

# JAO Publication Tool API caps all datasets to a 2-day range per call.
JAO_MAX_FETCH_DAYS = 2

class JaoRegion(str, Enum):
    """JAO Publication Tool region — each has its own base URL and dataset catalog."""

    CORE = "core"
    NORDIC = "nordic"

    def __str__(self) -> str:
        return self.value


class JaoDataset(str, Enum):
    """Canonical JAO Publication Tool dataset slugs.

    Each dataset is published by exactly one region's Publication Tool. The
    caller of `_query_jao` must pass the matching `JaoRegion`.
    """

    # Per-border, bidirectional (`border_XX_YY` fields).
    # Slugs are identical between Core and Nordic where both publish the dataset.
    SHADOW_AUCTION_ATC = "shadowAuctionATC"      # Core only
    CORE_EXTERNAL_ATC = "atc"                    # Core only
    MAX_EXCHANGES = "maxExchanges"               # Core + Nordic
    SCHEDULED_EXCHANGES = "scheduledExchanges"   # Core only
    MAX_BORDER_FLOW = "maxBorderFlow"            # Nordic only

    def __str__(self) -> str:
        return self.value


# Mapping from EM zone keys to the zone codes JAO uses in `border_XX_YY`
# fields. Only zones where the two differ need an entry; everything else
# passes through as-is (AT, BE, CZ, DE, FR, etc. all match 1:1).
#
# Notes on the DE-LU joint bidding zone: JAO treats DE-LU as a single zone
# under the code "DE" (no "LU" zone is ever published). Core-external ATC on
# borders involving LU is therefore fully accounted for under the DE-side
# exchange (e.g. BE-LU capacity is rolled into `border_BE_DE`). EM exchanges
# where LU is a party (BE_LU, DE_LU, FR_LU) should NOT be wired to this
# parser to avoid double-counting.
EM_TO_JAO_ZONE: dict[str, str] = {
    # Italy: JAO publishes a single "IT" code for Core-external borders,
    # which physically corresponds to the Italy North bidding zone.
    "IT-NO": "IT",
    "DK-DK1": "DK1",
    "DK-DK2": "DK2",
    "NO-NO1": "NO1",
    "NO-NO2": "NO2",
    "NO-NO3": "NO3",
    "NO-NO4": "NO4",
    "NO-NO5": "NO5",
    "SE-SE1": "SE1",
    "SE-SE2": "SE2",
    "SE-SE3": "SE3",
    "SE-SE4": "SE4",
}

def _em_to_jao_zone(em_zone: str) -> str:
    """Translate an EM zone key to the zone code JAO uses in its border field names."""
    return EM_TO_JAO_ZONE.get(em_zone, em_zone)


def _format_utc(dt: datetime) -> str:
    """Format a tz-aware datetime as the ISO-8601 string JAO expects."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _parse_utc(value: str) -> datetime:
    """Parse JAO's `dateTimeUtc` field into a tz-aware datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))



def _target_window(
    target_datetime: datetime | None,
    days: int = JAO_MAX_FETCH_DAYS,
) -> tuple[datetime, datetime]:
    """Return a [day_start, day_start + `days`) UTC window starting at the
    UTC day containing `target_datetime`. Matches the `@refetch_frequency`
    the public fetcher is decorated with so refetches are gapless.
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
    return day_start, day_start + timedelta(days=days)


BASE_URL_BY_REGION: dict[JaoRegion, str] = {
    JaoRegion.CORE: "https://publicationtool.jao.eu/core/api",
    JaoRegion.NORDIC: "https://publicationtool.jao.eu/nordic/api",
}

def _query_jao(
    session: Session,
    region: JaoRegion,
    dataset: JaoDataset,
    from_utc: datetime,
    to_utc: datetime,
    logger: Logger,
) -> list[dict]:
    """Call a JAO Publication Tool dataset endpoint in the given region.

    Shared by every JAO dataset (Core and Nordic alike) — formats params,
    unwraps the envelope, raises on HTTP error or `rejected=True`.
    """
    base_url = BASE_URL_BY_REGION[region]
    url = f"{base_url}/data/{dataset.value}"
    params = {"FromUtc": _format_utc(from_utc), "ToUtc": _format_utc(to_utc)}
    logger.debug(
        "Querying JAO",
        extra={
            "region": region.value,
            "dataset": dataset.value,
            "from_utc": params["FromUtc"],
            "to_utc": params["ToUtc"],
        },
    )
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    if not response.ok:
        raise ParserException(
            parser="JAO.py",
            message=(
                f"{region.value}/{dataset.value}: HTTP {response.status_code} "
                f"for {params['FromUtc']}..{params['ToUtc']}"
            ),
        )
    payload = response.json()
    if payload.get("rejected"):
        raise ParserException(
            parser="JAO.py",
            message=(
                f"{region.value}/{dataset.value}: request rejected by JAO "
                f"(messages={payload.get('messages')!r})"
            ),
        )
    return payload.get("data") or []


def _extract_border_capacity(
    rows: list[dict],
    sorted_zone_keys: ZoneKey,
    source: str,
    logger: Logger,
    field_prefix: str = "border",
) -> ExchangeCapacityForecastList:
    """Turn per-border rows into an ExchangeCapacityForecastList.

    For a sorted zone key `"A->B"`, reads `f'{prefix}_A_B'` as capacityExport
    (A→B) and `f'{prefix}_B_A'` as capacityImport (B→A). Works for any JAO
    dataset that uses the `border_XX_YY` shape (shadowAuctionATC,
    maxExchanges).
    """
    zone_a, zone_b = sorted_zone_keys.split("->")
    jao_a = _em_to_jao_zone(zone_a)
    jao_b = _em_to_jao_zone(zone_b)
    export_field = f"{field_prefix}_{jao_a}_{jao_b}"
    import_field = f"{field_prefix}_{jao_b}_{jao_a}"

    capacities = ExchangeCapacityForecastList(logger)
    for row in rows:
        export_value = row.get(export_field)
        import_value = row.get(import_field)
        if export_value is None and import_value is None:
            continue
        capacities.append(
            zoneKey=sorted_zone_keys,
            datetime=_parse_utc(row["dateTimeUtc"]),
            source=source,
            capacityExport=export_value,
            capacityImport=import_value,
        )
    return capacities


@refetch_frequency(timedelta(days=JAO_MAX_FETCH_DAYS))
def fetch_shadow_auction_atc_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead shadow-auction ATC capacity for a Core internal border.

    JAO publishes this as a fallback when Core day-ahead market coupling
    can't produce a result; on days where coupling succeeded, the response
    for the requested pair may be empty. Hourly granularity.
    """
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    from_utc, to_utc = _target_window(target_datetime)
    rows = _query_jao(
        session or Session(),
        JaoRegion.CORE,
        JaoDataset.SHADOW_AUCTION_ATC,
        from_utc,
        to_utc,
        logger,
    )
    return _extract_border_capacity(
        rows, sorted_zone_keys, SOURCE, logger
    ).to_list()


@refetch_frequency(timedelta(days=JAO_MAX_FETCH_DAYS))
def fetch_core_external_atc_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead ATC capacity on Core's external borders (non-flow-based
    neighbors: IT, DK1, ES, BG, ...). 15-minute granularity.
    """
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    from_utc, to_utc = _target_window(target_datetime)
    rows = _query_jao(
        session or Session(),
        JaoRegion.CORE,
        JaoDataset.CORE_EXTERNAL_ATC,
        from_utc,
        to_utc,
        logger,
    )
    return _extract_border_capacity(
        rows, sorted_zone_keys, SOURCE, logger
    ).to_list()


def _fetch_per_border_dataset(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    region: JaoRegion,
    dataset: JaoDataset,
    session: Session | None,
    target_datetime: datetime | None,
    logger: Logger,
) -> list[dict]:
    """Shared body for every per-border JAO fetcher: sort zone keys, build the
    window, query, extract, return. Each public fetcher is then a one-line
    wrapper that pins its region + dataset."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    from_utc, to_utc = _target_window(target_datetime)
    rows = _query_jao(
        session or Session(), region, dataset, from_utc, to_utc, logger
    )
    return _extract_border_capacity(
        rows, sorted_zone_keys, SOURCE, logger
    ).to_list()


@refetch_frequency(timedelta(days=JAO_MAX_FETCH_DAYS))
def fetch_core_max_exchanges_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead max bilateral exchange capacity (MaxBex) for a Core border.

    Published hourly; computed by Core TSOs as the max NTC that could be
    commercially exchanged per direction given grid constraints.
    """
    return _fetch_per_border_dataset(
        zone_key1, zone_key2,
        JaoRegion.CORE, JaoDataset.MAX_EXCHANGES,
        session, target_datetime, logger,
    )


@refetch_frequency(timedelta(days=JAO_MAX_FETCH_DAYS))
def fetch_nordic_max_exchanges_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead max bilateral exchange capacity (MaxBex) for a Nordic border.

    15-minute granularity. Uses Nordic bidding-zone codes (NO1..NO5, SE1..SE4,
    DK1/DK2, FI) — `EM_TO_JAO_ZONE` handles the EM→JAO translation.
    """
    return _fetch_per_border_dataset(
        zone_key1, zone_key2,
        JaoRegion.NORDIC, JaoDataset.MAX_EXCHANGES,
        session, target_datetime, logger,
    )


@refetch_frequency(timedelta(days=JAO_MAX_FETCH_DAYS))
def fetch_core_scheduled_commercial_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead scheduled commercial exchanges for a Core border.

    The cleared net commercial flow from Core day-ahead market coupling, per
    MTU (15 min). Covers Core internal borders and Core-external ones (e.g.
    FR↔ES, DK1↔DE).
    """
    return _fetch_per_border_dataset(
        zone_key1, zone_key2,
        JaoRegion.CORE, JaoDataset.SCHEDULED_EXCHANGES,
        session, target_datetime, logger,
    )


@refetch_frequency(timedelta(days=JAO_MAX_FETCH_DAYS))
def fetch_nordic_max_border_flow_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead max border flow (MaxBflow) for a Nordic border.

    15-minute granularity. Complementary to maxExchanges — maxBorderFlow is
    the raw physical capability ceiling on the border; maxExchanges is what
    was offered to the market after security constraints.
    """
    return _fetch_per_border_dataset(
        zone_key1, zone_key2,
        JaoRegion.NORDIC, JaoDataset.MAX_BORDER_FLOW,
        session, target_datetime, logger,
    )


if __name__ == "__main__":
    from pprint import pprint

    pprint(fetch_shadow_auction_atc_day_ahead(ZoneKey("DE"), ZoneKey("FR")))
    pprint(fetch_core_external_atc_day_ahead(ZoneKey("DE"), ZoneKey("DK-DK1")))
    pprint(fetch_core_max_exchanges_day_ahead(ZoneKey("DE"), ZoneKey("FR")))
    pprint(fetch_nordic_max_exchanges_day_ahead(ZoneKey("NO-NO2"), ZoneKey("SE-SE3")))
    pprint(fetch_core_scheduled_commercial_day_ahead(ZoneKey("DE"), ZoneKey("FR")))
    pprint(fetch_nordic_max_border_flow_day_ahead(ZoneKey("NO-NO2"), ZoneKey("SE-SE3")))
