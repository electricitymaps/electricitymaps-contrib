#!/usr/bin/env python3

"""Parse Peninsular Malaysian electricity data from the GSO API."""

# The states of Sabah and Sarawak are not included. There is pumped storage on
# the Peninsula but no data is currently available.
# https://www.scribd.com/document/354635277/Doubling-Up-in-Malaysia-International-Water-Power

# Standard library imports
import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

# Third-party library imports
import arrow
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

# Local library imports
from parsers.lib import config, validation

DEFAULT_ZONE_KEY = ZoneKey("MY-WM")
DOMAIN = "www.gso.org.my"
PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = "Asia/Kuala_Lumpur"
CONSUMPTION_URL = f"https://{DOMAIN}/SystemData/SystemDemand.aspx/GetChartDataSource"
EXCHANGE_URL = f"https://{DOMAIN}/SystemData/TieLine.aspx/GetChartDataSource"
PRODUCTION_URL = f"https://{DOMAIN}/SystemData/CurrentGen.aspx/GetChartDataSource"
SOLAR_URL = f"https://{DOMAIN}/SystemData/LargeScaleSolar.aspx/ForecastChart"

PRODUCTION_BREAKDOWN = {
    "Coal": "coal",
    "Gas": "gas",
    "CoGen": "unknown",
    "Oil": "oil",
    "Hydro": "hydro",
    "Solar": "solar",
}


@config.refetch_frequency(timedelta(minutes=10))
def fetch_consumption(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the power consumption (in MW) of a given zone."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format("DD/MM/YYYY")
    consumption_data = get_api_data(
        session or Session(),
        CONSUMPTION_URL,
        {
            "Fromdate": date_string,
            "Todate": date_string,
        },
    )
    all_consumption_data = TotalConsumptionList(logger)

    for item in consumption_data:
        all_consumption_data.append(
            zoneKey=zone_key,
            datetime=arrow.get(item["DT"]).to(TIMEZONE).datetime,
            consumption=item["MW"],
            source=DOMAIN,
        )
    return all_consumption_data.to_list()


@config.refetch_frequency(timedelta(minutes=10))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the power exchange (in MW) between two zones."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format("DD/MM/YYYY")

    sorted_zone_keys = "->".join(sorted((zone_key1, zone_key2)))
    all_exchange_data = ExchangeList(logger)
    if sorted_zone_keys == "MY-WM->SG":
        # The Singapore exchange is a PLTG tie.
        exchange_data = get_api_data(
            session,
            EXCHANGE_URL,
            {
                "Fromdate": date_string,
                "Todate": date_string,
                "Line": "PLTG",
            },
        )
        for item in exchange_data:
            all_exchange_data.append(
                datetime=arrow.get(item["Tarikhmasa"], tzinfo=TIMEZONE).datetime,
                netFlow=item["MW"],
                zoneKey=ZoneKey(sorted_zone_keys),
                source=DOMAIN,
            )

    elif sorted_zone_keys == "MY-WM->TH":
        # The Thailand exchange is made up of EGAT and HVDC ties.
        egat_exchanges = get_api_data(
            session,
            EXCHANGE_URL,
            {
                "Fromdate": date_string,
                "Todate": date_string,
                "Line": "EGAT",
            },
        )
        hvdc_exchanges = get_api_data(
            session,
            EXCHANGE_URL,
            {
                "Fromdate": date_string,
                "Todate": date_string,
                "Line": "HVDC",
            },
        )
        for exchange in egat_exchanges + hvdc_exchanges:
            all_exchange_data.append(
                datetime=arrow.get(exchange["Tarikhmasa"], tzinfo=TIMEZONE).datetime,
                netFlow=exchange["MW"],
                zoneKey=sorted_zone_keys,
                source=DOMAIN,
            )
    else:
        raise NotImplementedError("'{sorted_zone_keys}' is not implemented")
    return all_exchange_data.to_list()


@config.refetch_frequency(timedelta(minutes=10))
def fetch_production(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the production mix (in MW) of a given zone."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format("DD/MM/YYYY")
    all_production_data = ProductionBreakdownList(logger)

    production_data = get_api_data(
        session,
        PRODUCTION_URL,
        {
            "Fromdate": date_string,
            "Todate": date_string,
        },
    )
    for item in production_data:
        production_mix = ProductionMix()
        item_datetime = arrow.get(item["DT"], tzinfo=TIMEZONE).datetime
        for mode in [key for key in item if key != "DT"]:
            production_mix.add_value(PRODUCTION_BREAKDOWN[mode], item[mode], True)
        all_production_data.append(
            zoneKey=zone_key,
            production=production_mix,
            source=DOMAIN,
            datetime=item_datetime,
        )
    return all_production_data.to_list()


@config.refetch_frequency(timedelta(minutes=10))
def fetch_wind_solar_forecasts(
    zone_key: str = DEFAULT_ZONE_KEY,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the solar forecast (in MW) of a given zone."""
    date = arrow.get(target_datetime).to(TIMEZONE).floor("day")
    date_string = date.format("DD/MM/YYYY")
    session = session or Session()
    # Like the others, this endpoint presents data as a JSON object containing
    # the lone key 'd' and a string as its value, but the string now represents
    # a '$'-separated list of JSON strings rather than a proper JSON string.
    parsed_api_data = [
        json.loads(table)
        for table in session.post(
            SOLAR_URL,
            json={
                "Fromdate": date_string,
                "Todate": date_string,
            },
        )
        .json()["d"]
        .split("$")
    ]
    result = []
    for index, table in enumerate(parsed_api_data[1:4]):
        forecast_date = date.shift(days=index)
        for point in table:
            hour, minute, second = (int(hms) for hms in point["x"].split(":"))
            result.append(
                {
                    "datetime": forecast_date.replace(
                        hour=hour, minute=minute, second=second
                    ).datetime,
                    "production": {
                        "solar": point["y"],
                        "wind": None,
                    },
                    "source": DOMAIN,
                    "zoneKey": zone_key,
                }
            )
    return result


def get_api_data(session: Session, url, data):
    """Parse JSON data from the API."""
    # The API returns a JSON string containing only one key-value pair whose
    # value is another JSON string. We must therefore parse the response as
    # JSON, access the lone value, and parse it as JSON again!
    return json.loads(session.post(url, json=data).json()["d"])


if __name__ == "__main__":
    # Never used by the electricityMap back-end, but handy for testing.
    DATE = "2020"
    print("fetch_consumption():")
    print(fetch_consumption())
    print(f"fetch_consumption(target_datetime='{DATE}')")
    print(fetch_consumption(target_datetime=DATE))
    print("fetch_production():")
    print(fetch_production())
    print(f"fetch_production(target_datetime='{DATE}')")
    print(fetch_production(target_datetime=DATE))
    print("fetch_exchange('MY-WM', 'SG'):")
    print(fetch_exchange("MY-WM", "SG"))
    print(f"fetch_exchange(MY-WM, SG, target_datetime='{DATE}'):")
    print(fetch_exchange("MY-WM", "SG", target_datetime=DATE))
    print("fetch_exchange('MY-WM', 'TH'):")
    print(fetch_exchange("MY-WM", "TH"))
    print(f"fetch_exchange('MY-WM', 'TH', target_datetime='{DATE}'):")
    print(fetch_exchange("MY-WM", "TH", target_datetime=DATE))
    print(f"fetch_wind_solar_forecasts('MY-WM', target_datetime='{DATE}'):")
    print(fetch_wind_solar_forecasts("MY-WM", target_datetime=DATE))
    print("fetch_wind_solar_forecasts('MY-WM'):")
    print(fetch_wind_solar_forecasts("MY-WM"))
