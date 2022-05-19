#!/usr/bin/env python3

"""Parse Peninsular Malaysian electricity data from the GSO API."""

# The states of Sabah and Sarawak are not included. There is pumped storage on
# the Peninsula but no data is currently available.
# https://www.scribd.com/document/354635277/Doubling-Up-in-Malaysia-International-Water-Power

# Standard library imports
import collections
import datetime
import json
import logging

# Third-party library imports
import arrow
import requests

# Local library imports
from parsers.lib import config, validation

DEFAULT_ZONE_KEY = "MY-WM"
DOMAIN = "www.gso.org.my"
PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = "Asia/Kuala_Lumpur"
CONSUMPTION_URL = f"https://{DOMAIN}/SystemData/SystemDemand.aspx/GetChartDataSource"
EXCHANGE_URL = f"https://{DOMAIN}/SystemData/TieLine.aspx/GetChartDataSource"
PRODUCTION_URL = f"https://{DOMAIN}/SystemData/CurrentGen.aspx/GetChartDataSource"
SOLAR_URL = f"https://{DOMAIN}/SystemData/LargeScaleSolar.aspx/ForecastChart"


@config.refetch_frequency(datetime.timedelta(minutes=10))
def fetch_consumption(
    zone_key=DEFAULT_ZONE_KEY, session=None, target_datetime=None, logger=None
) -> list:
    """Request the power consumption (in MW) of a given zone."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format("DD/MM/YYYY")
    return [
        {
            "datetime": arrow.get(breakdown["DT"], tzinfo=TIMEZONE).datetime,
            "consumption": breakdown["MW"],
            "source": DOMAIN,
            "zoneKey": zone_key,
        }
        for breakdown in get_api_data(
            session or requests.Session(),
            CONSUMPTION_URL,
            {
                "Fromdate": date_string,
                "Todate": date_string,
            },
        )
    ]


@config.refetch_frequency(datetime.timedelta(minutes=10))
def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> list:
    """Request the power exchange (in MW) between two zones."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format("DD/MM/YYYY")
    session = session or requests.Session()
    sorted_zone_keys = "->".join(sorted((zone_key1, zone_key2)))
    if sorted_zone_keys == "MY-WM->SG":
        # The Singapore exchange is a PLTG tie.
        return [
            {
                "datetime": arrow.get(exchange["Tarikhmasa"], tzinfo=TIMEZONE).datetime,
                "netFlow": exchange["MW"],
                "sortedZoneKeys": sorted_zone_keys,
                "source": DOMAIN,
            }
            for exchange in get_api_data(
                session,
                EXCHANGE_URL,
                {
                    "Fromdate": date_string,
                    "Todate": date_string,
                    "Line": "PLTG",
                },
            )
        ]
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
        exchanges = collections.defaultdict(float)
        for exchange in egat_exchanges + hvdc_exchanges:
            exchanges[exchange["Tarikhmasa"]] += exchange["MW"]
        return [
            {
                "datetime": arrow.get(timestamp, tzinfo=TIMEZONE).datetime,
                "netFlow": power,
                "sortedZoneKeys": sorted_zone_keys,
                "source": DOMAIN,
            }
            for timestamp, power in exchanges.items()
        ]
    else:
        raise NotImplementedError("'{sorted_zone_keys}' is not implemented")


@config.refetch_frequency(datetime.timedelta(minutes=10))
def fetch_production(
    zone_key=DEFAULT_ZONE_KEY,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Request the production mix (in MW) of a given zone."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format("DD/MM/YYYY")
    return [
        validation.validate(
            {
                "datetime": arrow.get(breakdown["DT"], tzinfo=TIMEZONE).datetime,
                "production": {
                    "coal": breakdown["Coal"],
                    "gas": breakdown["Gas"],
                    "hydro": breakdown["Hydro"],
                    "oil": breakdown["Oil"],
                    "solar": breakdown["Solar"],
                    "unknown": breakdown["CoGen"],
                },
                "source": DOMAIN,
                "zoneKey": zone_key,
            },
            logger,
            floor=PRODUCTION_THRESHOLD,
            remove_negative=True,
        )
        for breakdown in get_api_data(
            session or requests.Session(),
            PRODUCTION_URL,
            {
                "Fromdate": date_string,
                "Todate": date_string,
            },
        )
    ]


@config.refetch_frequency(datetime.timedelta(minutes=10))
def fetch_wind_solar_forecasts(
    zone_key=DEFAULT_ZONE_KEY, session=None, target_datetime=None, logger=None
) -> list:
    """Request the solar forecast (in MW) of a given zone."""
    date = arrow.get(target_datetime).to(TIMEZONE).floor("day")
    date_string = date.format("DD/MM/YYYY")
    session = session or requests.Session()
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


def get_api_data(session, url, data):
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
