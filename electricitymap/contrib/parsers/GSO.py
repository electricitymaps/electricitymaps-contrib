#!/usr/bin/env python3

"""Parse Peninsular Malaysian electricity data from the GSO API."""

# The states of Sabah and Sarawak are not included. There is pumped storage on
# the Peninsula but no data is currently available.
# https://www.scribd.com/document/354635277/Doubling-Up-in-Malaysia-International-Water-Power

# Standard library imports
import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

# Third-party library imports
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

# Local library imports
from electricitymap.contrib.parsers.lib.config import refetch_frequency, use_proxy

DEFAULT_ZONE_KEY = ZoneKey("MY-WM")
DOMAIN = "www.gso.org.my"
PRODUCTION_THRESHOLD = 10  # MW
ZONE_INFO = ZoneInfo("Asia/Kuala_Lumpur")
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
@use_proxy(country_code="MY")
def fetch_consumption(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the power consumption (in MW) of a given zone."""
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    date_string = target_datetime.strftime("%d/%m/%Y")
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
            datetime=datetime.fromisoformat(item["DT"]).replace(tzinfo=ZONE_INFO),
            consumption=item["MW"],
            source=DOMAIN,
        )
    return all_consumption_data.to_list()


@refetch_frequency(timedelta(days=1))
@use_proxy(country_code="MY")
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the power exchange (in MW) between two zones."""
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    date_string = target_datetime.strftime("%d/%m/%Y")

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
                datetime=datetime.fromisoformat(item["Tarikhmasa"]).replace(
                    tzinfo=ZONE_INFO
                ),
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
                datetime=datetime.fromisoformat(exchange["Tarikhmasa"]).replace(
                    tzinfo=ZONE_INFO
                ),
                netFlow=exchange["MW"],
                zoneKey=sorted_zone_keys,
                source=DOMAIN,
            )
    else:
        raise NotImplementedError("'{sorted_zone_keys}' is not implemented")
    return all_exchange_data.to_list()


@refetch_frequency(timedelta(days=1))
@use_proxy(country_code="MY")
def fetch_production(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Request the production mix (in MW) of a given zone."""
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    date_string = target_datetime.strftime("%d/%m/%Y")
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
        item_datetime = datetime.fromisoformat(item["DT"]).replace(tzinfo=ZONE_INFO)
        for mode in [key for key in item if key != "DT"]:
            production_mix.add_value(PRODUCTION_BREAKDOWN[mode], item[mode], True)
        all_production_data.append(
            zoneKey=zone_key,
            production=production_mix,
            source=DOMAIN,
            datetime=item_datetime,
        )
    return all_production_data.to_list()
