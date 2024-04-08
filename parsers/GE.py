"""Fetch the status of the Georgian electricity grid."""

import urllib.parse
from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.ENTSOE import fetch_exchange as ENTSOE_fetch_exchange
from parsers.lib import config
from parsers.lib.exceptions import ParserException

PARSER = "GE.py"
TIMEZONE = ZoneInfo("Asia/Tbilisi")
ZONE_KEY = ZoneKey("GE")

MINIMUM_PRODUCTION_THRESHOLD = 10  # MW
URL = urllib.parse.urlsplit("https://gse.com.ge/apps/gsebackend/rest")
URL_STRING = URL.geturl()
SOURCE = URL.netloc


def _floor(breakdowns: ProductionBreakdownList, floor: float | int):
    """Filters production breakdown events whose production sum is lower than a given floor."""
    filtered_breakdowns = ProductionBreakdownList(breakdowns.logger)
    for event in breakdowns.events:
        if event.production is None:
            continue

        total = sum(v for _mode, v in event.production if v is not None)

        if event.storage is not None:
            total_storage = sum(v for _mode, v in event.storage if v is not None)
            total -= total_storage

        if total < floor:
            filtered_breakdowns.logger.warning(
                f"Discarded production event for {event.zoneKey} at {event.datetime} due to reported total of {total} MW does not meet {floor} MW floor value."
            )
            continue

        filtered_breakdowns.append(
            zoneKey=event.zoneKey,
            datetime=event.datetime,
            production=event.production,
            storage=event.storage,
            source=event.source,
            sourceType=event.sourceType,
        )
    return filtered_breakdowns


@config.refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("GE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Request the last known production mix (in MW) of a given country."""
    session = session or Session()

    # Get the current production mix
    if target_datetime is None:
        # TODO: remove `verify=False` ASAP.
        response = session.get(f"{URL_STRING}/map", verify=False)
        if not response.ok:
            raise ParserException(
                PARSER,
                f"Exception when fetching production error code: {response.status_code}: {response.text}",
                zone_key,
            )
        response_payload = response.json()["typeSum"]

        production_mix = ProductionMix()
        production_mix.add_value("gas", response_payload["thermalData"])
        production_mix.add_value("hydro", response_payload["hydroData"])
        production_mix.add_value("solar", response_payload["solarData"])
        production_mix.add_value("wind", response_payload["windPowerData"])

        production_breakdown_list = ProductionBreakdownList(logger)
        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=datetime.now(tz=TIMEZONE).replace(second=0, microsecond=0),
            source=SOURCE,
            production=production_mix,
        )
        return _floor(
            production_breakdown_list, floor=MINIMUM_PRODUCTION_THRESHOLD
        ).to_list()

    # Get the production mix for every hour on the day of interest.
    day = datetime.combine(target_datetime.astimezone(TIMEZONE), time())
    timestamp_from, timestamp_to = (
        day,
        day + timedelta(days=1) - timedelta(seconds=1),
    )
    # TODO: remove `verify=False` ASAP.
    response = session.get(
        f"{URL_STRING}/diagramDownload",
        params={
            "fromDate": timestamp_from.strftime("%Y-%m-%dT%H:%M:%S"),
            "lang": "EN",
            "toDate": timestamp_to.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "FACT",
        },
        verify=False,
    )
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    table = (
        pandas.read_excel(response.content, header=2, index_col=1)
        .iloc[2:6, 2:]
        .dropna(axis="columns", how="all")
    )
    table.index = "gas", "hydro", "wind", "solar"
    table.columns = pandas.date_range(
        start=timestamp_from, freq="1H", periods=table.shape[1]
    )

    production_breakdown_list = ProductionBreakdownList(logger)
    for timestamp, production in table.items():
        production_mix = ProductionMix()
        production_mix.add_value("gas", production["gas"])
        production_mix.add_value("hydro", production["hydro"])
        production_mix.add_value("solar", production["wind"])
        production_mix.add_value("wind", production["solar"])

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=timestamp.to_pydatetime().replace(tzinfo=TIMEZONE),
            source=SOURCE,
            production=production_mix,
        )
    return _floor(
        production_breakdown_list, floor=MINIMUM_PRODUCTION_THRESHOLD
    ).to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Request the last known power exchange (in MW) between two countries."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    session = session or Session()
    if target_datetime is not None:
        return ENTSOE_fetch_exchange(
            zone_key1, zone_key2, session, target_datetime, logger
        )

    now = datetime.now(timezone.utc)
    # The API uses the convention of positive net flow into GE.
    # TODO: remove `verify=False` ASAP.
    response = session.get(f"{URL_STRING}/map", verify=False)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            sorted_zone_keys,
        )

    net_flows = response.json()["areaSum"]

    # Positive net flow should be in the same direction as the arrow in
    # `exchange`. This is not necessarily the same as positive flow into GE.
    if sorted_zone_keys == ZoneKey("AM->GE"):
        net_flow = net_flows["armeniaSum"]
    elif sorted_zone_keys == ZoneKey("AZ->GE"):
        net_flow = net_flows["azerbaijanSum"]
    elif sorted_zone_keys == ZoneKey("GE->RU"):
        # GE->RU might be falsely reported, exchanges/*.yaml has a definition to
        # use the Russian TSO for this flow.
        net_flow = -(
            net_flows["russiaSum"]
            + net_flows["russiaJavaSum"]
            + net_flows["russiaSalkhinoSum"]
        )
    elif sorted_zone_keys == ZoneKey("GE->TR"):
        net_flow = -net_flows["turkeySum"]
    else:
        raise NotImplementedError(f"{sorted_zone_keys} pair is not implemented")

    exchange_list = ExchangeList(logger)
    exchange_list.append(
        zoneKey=sorted_zone_keys,
        datetime=now.replace(second=0, microsecond=0),
        netFlow=net_flow,
        source=SOURCE,
    )
    return exchange_list.to_list()


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.

    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_production(target_datetime=datetime.datetime(2020, 1, 1)) ->")
    print(fetch_production(target_datetime=datetime(2020, 1, 1, tzinfo=timezone.utc)))

    for neighbour in ["AM", "AZ", "RU", "TR"]:
        print(f"fetch_exchange('GE', {neighbour}) ->")
        print(fetch_exchange(ZONE_KEY, ZoneKey(neighbour)))
