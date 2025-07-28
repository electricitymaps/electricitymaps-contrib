#!/usr/bin/env python3

"""Parse the Alberta Electric System Operator's (AESO's) Energy Trading System
(ETS) website.
"""

# Standard library imports
import csv
import io
import re
import urllib.parse
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

# Third-party library imports
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey

DEFAULT_ZONE_KEY = ZoneKey("CA-AB")
MINIMUM_PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = ZoneInfo("Canada/Mountain")
URL = urllib.parse.urlsplit("http://ets.aeso.ca/ets_web/ip/Market/Reports")
URL_STRING = urllib.parse.urlunsplit(URL)
SOURCE = URL.netloc

PRODUCTION_MAPPING = {
    "COGENERATION": "gas",
    "COMBINED CYCLE": "gas",
    "GAS FIRED STEAM": "gas",
    "SIMPLE CYCLE": "gas",
    "WIND": "wind",
    "SOLAR": "solar",
    "HYDRO": "hydro",
    "OTHER": "biomass",
}

STORAGE_MAPPING = {"ENERGY STORAGE": "battery"}
SKIP_KEYS = ["TOTAL"]


def fetch_exchange(
    zone_key1: str = DEFAULT_ZONE_KEY,
    zone_key2: str = "CA-BC",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Request the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError("Currently unable to scrape historical data")
    session = session or Session()
    response = session.get(
        f"{URL_STRING}/CSDReportServlet", params={"contentType": "csv"}
    )
    interchange = dict(csv.reader(response.text.split("\r\n\r\n")[4].splitlines()))
    flows = {
        f"{DEFAULT_ZONE_KEY}->CA-BC": interchange["British Columbia"],
        f"{DEFAULT_ZONE_KEY}->CA-SK": interchange["Saskatchewan"],
        f"{DEFAULT_ZONE_KEY}->US-MT": interchange["Montana"],
        f"{DEFAULT_ZONE_KEY}->US-NW-NWMT": interchange["Montana"],
    }
    sorted_zone_keys = ZoneKey("->".join(sorted((zone_key1, zone_key2))))
    if sorted_zone_keys not in flows:
        raise NotImplementedError(f"Pair '{sorted_zone_keys}' not implemented")
    exchanges = ExchangeList(logger)
    exchanges.append(
        zoneKey=sorted_zone_keys,
        datetime=get_csd_report_timestamp(response.text),
        netFlow=float(flows[sorted_zone_keys]),
        source=URL.netloc,
    )
    return exchanges.to_list()


def fetch_price(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Request the last known power price of a given country."""
    if target_datetime:
        raise NotImplementedError("Currently unable to scrape historical data")
    session = session or Session()
    response = session.get(
        f"{URL_STRING}/SMPriceReportServlet", params={"contentType": "csv"}
    )
    prices = PriceList(logger)
    for row in csv.reader(response.text.split("\r\n\r\n")[2].splitlines()[1:]):
        if row[1] != "-":
            date, hour = row[0].split()
            prices.append(
                zoneKey=zone_key,
                datetime=datetime.strptime(
                    f"{date} {int(hour) - 1}", "%m/%d/%Y %H"
                ).replace(tzinfo=TIMEZONE)
                + timedelta(hours=1),
                price=float(row[1]),
                source=URL.netloc,
                currency="CAD",
            )
    return prices.to_list()


def fetch_production(
    zone_key: str = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict[str, Any] | None:
    """Request the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    session = session or Session()
    response = session.get(
        f"{URL_STRING}/CSDReportServlet", params={"contentType": "csv"}
    )
    generation = {
        row[0]: float(row[2])  # total net generation
        for row in csv.reader(response.text.split("\r\n\r\n")[3].splitlines())
    }

    production_breakdowns = ProductionBreakdownList(logger)
    production = ProductionMix()
    storage = StorageMix()

    for key in generation:
        if key in PRODUCTION_MAPPING:
            production.add_value(
                PRODUCTION_MAPPING[key],
                generation.get(key),
                correct_negative_with_zero=True,
            )
        elif key in STORAGE_MAPPING:
            storage.add_value(STORAGE_MAPPING[key], generation.get(key))

        elif key not in SKIP_KEYS:
            logger.warning(f"Unrecognized key: {key} in data skipped")

    date = get_csd_report_timestamp(response.text)

    production_breakdowns.append(
        zoneKey=zone_key,
        datetime=date,
        production=production,
        storage=storage,
        source=SOURCE,
    )

    return production_breakdowns.to_list()


def get_csd_report_timestamp(report):
    """Get the timestamp from a current supply/demand (CSD) report."""
    return datetime.strptime(
        re.search(r'"Last Update : (.*)"', report).group(1), "%b %d, %Y %H:%M"
    ).replace(tzinfo=TIMEZONE)


def _get_wind_solar_data(session: Session, url: str) -> pd.DataFrame:
    response = session.get(url)
    csv = pd.read_csv(io.StringIO(response.text))
    return csv


def fetch_wind_solar_forecasts(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests wind and solar production forecasts in hourly data (in MW) for 7 days ahead."""
    session = session or Session()

    # Requests
    # Wind 7 days
    url_wind = "http://ets.aeso.ca/Market/Reports/Manual/Operations/prodweb_reports/wind_solar_forecast/wind_rpt_longterm.csv"
    csv_wind = _get_wind_solar_data(session, url_wind)

    # Solar 7 days
    url_solar = "http://ets.aeso.ca/Market/Reports/Manual/Operations/prodweb_reports/wind_solar_forecast/solar_rpt_longterm.csv"
    csv_solar = _get_wind_solar_data(session, url_solar)

    all_production_events = csv_wind.merge(
        csv_solar, on="Forecast Transaction Date", suffixes=("_wind", "_solar")
    )

    production_list = ProductionBreakdownList(logger)
    for _, event in all_production_events.iterrows():
        event_datetime = event["Forecast Transaction Date"]
        event_datetime = datetime.fromisoformat(event_datetime).replace(tzinfo=TIMEZONE)
        production_mix = ProductionMix()
        production_mix.add_value(
            "solar", event["Most Likely_solar"], correct_negative_with_zero=True
        )
        production_mix.add_value(
            "wind", event["Most Likely_wind"], correct_negative_with_zero=True
        )

        production_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            production=production_mix,
            source=URL.netloc,
            sourceType=EventSourceType.forecasted,
        )
    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""
    """
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, CA-BC) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "CA-BC"))
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, CA-SK) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "CA-SK"))
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, US-MT) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "US-MT"))
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, US-NW-NWMT) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "US-NW-NWMT"))"
    """
