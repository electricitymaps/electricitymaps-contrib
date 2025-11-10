# Archived reason: Switched to ENTSOE parser for production data as it has higer resolution.

"""Fetch the status of the Georgian electricity grid."""

import urllib.parse
from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import numpy as np
import pandas
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.ENTSOE import (
    fetch_exchange as ENTSOE_fetch_exchange,
)
from electricitymap.contrib.parsers.lib import config
from electricitymap.contrib.parsers.lib.exceptions import ParserException

PARSER = "GE.py"
TIMEZONE = ZoneInfo("Asia/Tbilisi")
ZONE_KEY = ZoneKey("GE")

MINIMUM_PRODUCTION_THRESHOLD = 10  # MW
URL = urllib.parse.urlsplit("https://gse.com.ge/apps/gsebackend/rest")
URL_STRING = URL.geturl()
SOURCE = URL.netloc


@config.refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Request the last known production mix (in MW) of a given country."""
    session = session or Session()

    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    # Get the production mix for every hour on the (UTC) day of interest.
    day = datetime.combine(target_datetime, time(), tzinfo=timezone.utc)
    timestamp_from, timestamp_to = (
        day,
        day + timedelta(days=1) - timedelta(seconds=1),
    )

    # TODO: remove `verify=False` ASAP.
    response = session.get(
        f"{URL_STRING}/diagramDownload",
        params={
            "fromDate": timestamp_from.astimezone(TIMEZONE).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "lang": "EN",
            "toDate": timestamp_to.astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
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

    tables = pandas.read_excel(
        response.content,
        header=None,
        # labels column + the 24 columns of hourly data
        usecols=[1] + list(range(3, 27)),
        # drop every 11th row (separation between tables)
        skiprows=lambda x: x % 11 == 0,
    )

    production_breakdown_list = ProductionBreakdownList(logger)
    for _i, daily_table in reversed(
        tuple(tables.groupby(np.arange(len(tables)) // 10))
    ):
        day = daily_table.iloc[1][1]
        timestamps = pandas.date_range(start=day, freq="1H", periods=24)

        # zoom in on fields of interest
        itemised_production_data = daily_table.iloc[4:8].set_index(1)
        itemised_production_data.columns = timestamps

        for timestamp, production in itemised_production_data.dropna(
            axis="columns", how="all"
        ).items():
            dt = timestamp.to_pydatetime().replace(tzinfo=TIMEZONE)

            production_mix = ProductionMix()
            production_mix.add_value("gas", production["Thermal Power Plants"])
            production_mix.add_value("hydro", production["Hydro Power Plants"])
            production_mix.add_value("solar", production["Solar Power Plants"])
            production_mix.add_value("wind", production["Wind Power Plants"])

            production_breakdown_list.append(
                zoneKey=zone_key,
                datetime=dt.astimezone(timezone.utc),
                source=SOURCE,
                production=production_mix,
            )
    return production_breakdown_list.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Request the last known power exchange (in MW) between two countries."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if ZONE_KEY not in {zone_key1, zone_key2}:
        raise ParserException(
            PARSER,
            f"This parser can only parse exchanges to / from {ZONE_KEY}.",
            sorted_zone_keys,
        )

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
            f"Exception when fetching exchange error code: {response.status_code}: {response.text}",
            sorted_zone_keys,
        )

    net_flows = response.json()["areaSum"]

    neighbour = zone_key2 if zone_key1 == ZONE_KEY else zone_key1
    direction = -1 if sorted_zone_keys.startswith(ZONE_KEY) else 1
    if neighbour == ZoneKey("AM"):
        net_flow = net_flows["armeniaSum"]
    elif neighbour == ZoneKey("AZ"):
        net_flow = net_flows["azerbaijanSum"]
    elif neighbour == ZoneKey("RU-1"):
        # GE->RU might be falsely reported, exchanges/*.yaml has a definition to
        # use the Russian TSO for this flow.
        net_flow = (
            net_flows["russiaSum"]
            + net_flows["russiaJavaSum"]
            + net_flows["russiaSalkhinoSum"]
        )
    elif neighbour == ZoneKey("TR"):
        net_flow = net_flows["turkeySum"]
    else:
        raise NotImplementedError(f"{sorted_zone_keys} pair is not implemented")

    exchange_list = ExchangeList(logger)
    exchange_list.append(
        zoneKey=sorted_zone_keys,
        datetime=now.replace(second=0, microsecond=0),
        netFlow=direction * net_flow,
        source=SOURCE,
    )
    return exchange_list.to_list()


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.

    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_production(target_datetime=datetime.datetime(2020, 1, 1)) ->")
    print(fetch_production(target_datetime=datetime(2020, 1, 1, tzinfo=timezone.utc)))

    for neighbour in ["AM", "AZ", "RU-1", "TR"]:
        print(f"fetch_exchange('GE', {neighbour}) ->")
        print(fetch_exchange(ZONE_KEY, ZoneKey(neighbour)))
