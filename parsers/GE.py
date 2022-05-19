"""Fetch the status of the Georgian electricity grid."""

# Standard library imports
import datetime
import logging
import urllib.parse

# Third-party library imports
import arrow
import pandas
import requests

# Local library imports
from parsers.lib import config, validation

from .ENTSOE import fetch_exchange as ENTSOE_fetch_exchange

MINIMUM_PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = "Asia/Tbilisi"
URL = urllib.parse.urlsplit("https://gse.com.ge/apps/gsebackend/rest")
URL_STRING = URL.geturl()


@config.refetch_frequency(datetime.timedelta(hours=1))
def fetch_production(
    zone_key="GE",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Request the last known production mix (in MW) of a given country."""
    session = session or requests.session()
    if target_datetime is None:  # Get the current production mix.
        # TODO: remove `verify=False` ASAP.
        production_mix = session.get(f"{URL_STRING}/map", verify=False).json()[
            "typeSum"
        ]
        return validation.validate(
            {
                "datetime": arrow.now(TIMEZONE).floor("minute").datetime,
                "production": {
                    "gas": production_mix["thermalData"],
                    "hydro": production_mix["hydroData"],
                    "solar": production_mix["solarData"],
                    "wind": production_mix["windPowerData"],
                },
                "source": URL.netloc,
                "zoneKey": "GE",
            },
            logger,
            remove_negative=True,
            floor=MINIMUM_PRODUCTION_THRESHOLD,
        )
    else:
        # Get the production mix for every hour on the day of interest.
        timestamp_from, timestamp_to = (
            arrow.get(target_datetime, TIMEZONE)
            .replace(hour=0)
            .floor("hour")
            .span("day")
        )
        response = session.get(
            f"{URL_STRING}/diagramDownload",
            params={
                "fromDate": timestamp_from.format("YYYY-MM-DDTHH:mm:ss"),
                "lang": "EN",
                "toDate": timestamp_to.format("YYYY-MM-DDTHH:mm:ss"),
                "type": "FACT",
            },
            verify=False,
        )  # TODO: remove `verify=False` ASAP.
        table = (
            pandas.read_excel(response.content, header=2, index_col=1)
            .iloc[2:6, 2:]
            .dropna(axis="columns", how="all")
        )
        table.index = "gas", "hydro", "wind", "solar"
        table.columns = pandas.date_range(
            start=timestamp_from.datetime, freq="1H", periods=table.shape[1]
        )

        # Collect the data into a list of dictionaries, then validate and
        # return it.
        production_mixes = (
            {
                "datetime": arrow.get(timestamp, TIMEZONE).datetime,
                "production": {
                    "gas": production_mix["gas"],
                    "hydro": production_mix["hydro"],
                    "wind": production_mix["wind"],
                    "solar": production_mix["solar"],
                },
                "source": URL.netloc,
                "zoneKey": zone_key,
            }
            for timestamp, production_mix in table.items()
        )
        return [
            validation.validate(
                production_mix,
                logger,
                remove_negative=True,
                floor=MINIMUM_PRODUCTION_THRESHOLD,
            )
            for production_mix in production_mixes
        ]


def fetch_exchange(
    zone_key1="GE",
    zone_key2="TR",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Request the last known power exchange (in MW) between two countries."""
    if target_datetime:
        return ENTSOE_fetch_exchange(
            zone_key1, zone_key2, session, target_datetime, logger
        )

    session = session or requests.session()
    # The API uses the convention of positive net flow into GE.
    net_flows = session.get(f"{URL_STRING}/map", verify=False).json()[
        "areaSum"
    ]  # TODO: remove `verify=False` ASAP.

    # Positive net flow should be in the same direction as the arrow in
    # `exchange`. This is not necessarily the same as positive flow into GE.
    exchange = "->".join(sorted((zone_key1, zone_key2)))
    if exchange == "AM->GE":
        net_flow = net_flows["armeniaSum"]
    elif exchange == "AZ->GE":
        net_flow = net_flows["azerbaijanSum"]
    elif exchange == "GE->RU":
        # GE->RU might be falsely reported, exchanges.json has a definition to
        # use the Russian TSO for this flow.
        net_flow = -(
            net_flows["russiaSum"]
            + net_flows["russiaJavaSum"]
            + net_flows["russiaSalkhinoSum"]
        )
    elif exchange == "GE->TR":
        net_flow = -net_flows["turkeySum"]
    else:
        raise NotImplementedError(f"{exchange} pair is not implemented")

    return {
        "datetime": arrow.now(TIMEZONE).floor("minute").datetime,
        "netFlow": net_flow,
        "sortedZoneKeys": exchange,
        "source": URL.netloc,
    }


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_production(target_datetime=datetime.datetime(2020, 1, 1)) ->")
    print(fetch_production(target_datetime=datetime.datetime(2020, 1, 1)))
    print("fetch_exchange('GE', 'AM') ->")
    print(fetch_exchange("GE", "AM"))
    print("fetch_exchange('GE', 'AZ') ->")
    print(fetch_exchange("GE", "AZ"))
    print("fetch_exchange('GE', 'RU') ->")
    print(fetch_exchange("GE", "RU"))
    print("fetch_exchange('GE', 'TR') ->")
    print(fetch_exchange("GE", "TR"))
    print("fetch_exchange('AB', 'YZ') ->")
    print(fetch_exchange("AB", "YZ"))
