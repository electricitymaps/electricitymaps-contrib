#!/usr/bin/env python3

"""
Parser for the JAO (Joint Allocation Office) Publication Tool.

Docs: https://www.jao.eu/page-api/market-data
API:  https://publicationtool.jao.eu/core/api

Every JAO Core dataset is served from the same base URL with the same query
params (FromUtc, ToUtc) and the same envelope ({data, rejected, messages}),
so the HTTP layer is reusable. Datasets differ only in row shape:

- Per-border (bidirectional): fields named `border_XX_YY`, one row per hour.
    e.g. shadowAuctionATC, maxExchanges
- Per-zone: one row per hour, fields per country (`maxAT`, `minDE`, ...).
    e.g. maxNetPos, referenceNetPosition
- Per-CNEC: many rows per hour, one per critical network element.
    e.g. shadowPrices, validationReductions

Currently wired:
- fetch_shadow_auction_atc_day_ahead  → shadowAuctionATC (per-border)

To add another per-border dataset, add an entry to `JaoDataset` and a thin
public fetcher that calls `_query_jao` + `_extract_border_capacity`.
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
BASE_URL = "https://publicationtool.jao.eu/core/api"
REQUEST_TIMEOUT_SECONDS = 30


class JaoDataset(str, Enum):
    """Canonical JAO Core Publication Tool dataset slugs."""

    # Per-border, bidirectional (`border_XX_YY` fields)
    SHADOW_AUCTION_ATC = "shadowAuctionATC"
    MAX_EXCHANGES = "maxExchanges"
    # Per-zone
    MAX_NET_POS = "maxNetPos"
    REFERENCE_NET_POSITION = "referenceNetPosition"
    # Per-CNEC (multiple rows per MTU)
    SHADOW_PRICES = "shadowPrices"
    VALIDATION_REDUCTIONS = "validationReductions"

    def __str__(self) -> str:
        return self.value


def _format_utc(dt: datetime) -> str:
    """Format a tz-aware datetime as the ISO-8601 string JAO expects."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _parse_utc(value: str) -> datetime:
    """Parse JAO's `dateTimeUtc` field into a tz-aware datetime."""
    # Python 3.10's fromisoformat doesn't accept a trailing `Z`.
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _target_day_window(
    target_datetime: datetime | None,
) -> tuple[datetime, datetime]:
    """Return the [00:00, 24:00) UTC window containing `target_datetime`."""
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
    elif target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    day_start = datetime.combine(
        target_datetime.astimezone(timezone.utc).date(),
        time.min,
        tzinfo=timezone.utc,
    )
    return day_start, day_start + timedelta(days=1)


def _query_jao(
    session: Session,
    dataset: JaoDataset,
    from_utc: datetime,
    to_utc: datetime,
    logger: Logger,
) -> list[dict]:
    """Call a JAO Core Publication Tool dataset endpoint.

    Shared by every JAO dataset — formats params, unwraps the envelope,
    raises on HTTP error or `rejected=True`.
    """
    url = f"{BASE_URL}/data/{dataset.value}"
    params = {"FromUtc": _format_utc(from_utc), "ToUtc": _format_utc(to_utc)}
    logger.debug(
        "Querying JAO",
        extra={"dataset": dataset.value, "from_utc": params["FromUtc"], "to_utc": params["ToUtc"]},
    )
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    if not response.ok:
        raise ParserException(
            parser="JAO.py",
            message=(
                f"{dataset.value}: HTTP {response.status_code} "
                f"for {params['FromUtc']}..{params['ToUtc']}"
            ),
        )
    payload = response.json()
    if payload.get("rejected"):
        raise ParserException(
            parser="JAO.py",
            message=(
                f"{dataset.value}: request rejected by JAO "
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
    export_field = f"{field_prefix}_{zone_a}_{zone_b}"
    import_field = f"{field_prefix}_{zone_b}_{zone_a}"

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


@refetch_frequency(timedelta(days=2))
def fetch_shadow_auction_atc_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead shadow-auction ATC capacity for a Core border.

    JAO publishes this as a fallback when Core day-ahead market coupling
    can't produce a result; on days where coupling succeeded, the response
    for the requested pair may simply be empty.
    """
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    from_utc, to_utc = _target_day_window(target_datetime)
    rows = _query_jao(
        session or Session(),
        JaoDataset.SHADOW_AUCTION_ATC,
        from_utc,
        to_utc,
        logger,
    )
    return _extract_border_capacity(
        rows, sorted_zone_keys, SOURCE, logger
    ).to_list()


if __name__ == "__main__":
    from pprint import pprint

    pprint(fetch_shadow_auction_atc_day_ahead(ZoneKey("DE"), ZoneKey("FR")))
