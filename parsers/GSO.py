#!/usr/bin/env python3

"""Parse Peninsular Malaysian electricity data from the GSO API."""

# The states of Sabah and Sarawak are not included. There is pumped storage on
# the Peninsula but no data is currently available.
# https://www.scribd.com/document/354635277/Doubling-Up-in-Malaysia-International-Water-Power

# Standard library imports
import json
from datetime import datetime, timedelta
from logging import Logger, getLogger

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
from parsers.lib.config import refetch_frequency

DEFAULT_ZONE_KEY = ZoneKey("MY-WM")
DOMAIN = "www.gso.org.my"
PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = "Asia/Kuala_Lumpur"
CONSUMPTION_URL = f"https://{DOMAIN}/SystemData/SystemDemand.aspx/GetChartDataSource"
EXCHANGE_URL = f"https://{DOMAIN}/SystemData/TieLine.aspx/GetChartDataSource"
PRODUCTION_URL = f"https://{DOMAIN}/SystemData/CurrentGen.aspx/GetChartDataSource"

PRODUCTION_BREAKDOWN = {
    "Coal": "coal",
    "Gas": "gas",
    "CoGen": "unknown",
    "Oil": "oil",
    "Hydro": "hydro",
    "Solar": "solar",
}


def get_api_data(session: Session, url, data):
    """Parse JSON data from the API."""
    # The API returns a JSON string containing only one key-value pair whose
    # value is another JSON string. We must therefore parse the response as
    # JSON, access the lone value, and parse it as JSON again!
    return json.loads(session.post(url, json=data).json()["d"])


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session = Session(),
    target_datetime: datetime | None = None,
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
            datetime=arrow.get(item["DT"], tzinfo=TIMEZONE).to("utc").datetime,
            consumption=item["MW"],
            source=DOMAIN,
        )
    return all_consumption_data.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the power exchange (in MW) between two zones."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format("DD/MM/YYYY")

    sorted_zone_keys = ZoneKey("->".join(sorted((zone_key1, zone_key2))))
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
                datetime=arrow.get(item["Tarikhmasa"], tzinfo=TIMEZONE)
                .to("utc")
                .datetime,
                netFlow=item["MW"],
                zoneKey=sorted_zone_keys,
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
                datetime=arrow.get(exchange["Tarikhmasa"], tzinfo=TIMEZONE)
                .to("utc")
                .datetime,
                netFlow=exchange["MW"],
                zoneKey=sorted_zone_keys,
                source=DOMAIN,
            )
    else:
        raise NotImplementedError("'{sorted_zone_keys}' is not implemented")
    return all_exchange_data.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session = Session(),
    target_datetime: datetime | None = None,
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
        item_datetime = arrow.get(item["DT"], tzinfo=TIMEZONE).to("utc").datetime
        for mode in [key for key in item if key != "DT"]:
            production_mix.add_value(PRODUCTION_BREAKDOWN[mode], item[mode], True)
        all_production_data.append(
            zoneKey=zone_key,
            production=production_mix,
            source=DOMAIN,
            datetime=item_datetime,
        )
    return all_production_data.to_list()


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
