from datetime import datetime, timedelta, timezone
from enum import Enum
from logging import Logger, getLogger
from typing import Any

import pandas as pd
import requests
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.ENTSOE import ENTSOE_DOMAIN_MAPPINGS
from electricitymap.contrib.parsers.ENTSOE import (
    parse_production as ENTSOE_parse_production,
)
from electricitymap.contrib.parsers.ENTSOE import (
    query_production as ENTSOE_query_production,
)
from electricitymap.contrib.parsers.lib.config import ProductionModes, refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.utils import get_token

URL = "https://api.ned.nl/v1/utilizations"

TYPE_MAPPING = {
    1: ProductionModes.WIND,  # Wind Onshore (Wind)
    2: ProductionModes.SOLAR,  # Solar (Zon)
    18: ProductionModes.GAS,  # Fossil Gas Power (Aardgas)
    19: ProductionModes.COAL,  # Fossil Hard Coal (Steenkool)
    20: ProductionModes.NUCLEAR,  # Nuclear (Kernenergie)
    21: ProductionModes.BIOMASS,  # Waste Power (Aftval)
    25: ProductionModes.BIOMASS,  # Biomass Power (Biomassa)
    26: ProductionModes.UNKNOWN,  # Other Power (Overig)
    35: ProductionModes.GAS,  # CHP (WKK)
    51: ProductionModes.WIND,  # Wind Offshore (ZeeWind)
}


class NedType(Enum):
    WIND = 1
    SOLAR = 2
    FOSSILGASPOWER = 18
    FOSSILHARDCOAL = 19
    NUCLEAR = 20
    WASTEPOWER = 21
    BIOMASSPOWER = 25
    OTHERPOWER = 26
    WKKTOTAL = 35
    WINDOFFSHORE = 51


class NedActivity(Enum):
    PRODUCTION = 1
    CONSUMPTION = 2


class NedGranularity(Enum):
    TEN_MINUTES = 3
    FIFTEEN_MINUTES = 4
    HOURLY = 5
    DAILY = 6
    MONTHLY = 7
    YEARLY = 8


class NedGranularityTimezone(Enum):
    UTC = 0
    LOCAL = 1


class NedClassification(Enum):
    FORECAST = 1
    MEASURED = 2


class NedPoint(Enum):
    NETHERLANDS = 0


# kWh to MW conversion based on granularity with 6 decimal places
def _kwh_to_mw(kwh: float, granularity: int) -> float:
    """
    Convert kWh to MW based on the time granularity.

    Args:
        kwh: Energy in kilowatt-hours
        granularity: NedGranularity value (3=TEN_MINUTES, 4=FIFTEEN_MINUTES, 5=HOURLY)

    Returns:
        Power in megawatts

    Raises:
        ParserException: If granularity is not supported
    """
    # Map granularity to periods per hour
    granularity_multipliers = {
        NedGranularity.TEN_MINUTES.value: 6,  # 6 x 10-minute periods per hour
        NedGranularity.FIFTEEN_MINUTES.value: 4,  # 4 x 15-minute periods per hour
        NedGranularity.HOURLY.value: 1,  # 1 hour per hour
    }

    if granularity not in granularity_multipliers:
        raise ParserException(
            parser="NED.py",
            message=f"Unsupported granularity: {granularity}. Only TEN_MINUTES, FIFTEEN_MINUTES, and HOURLY are supported.",
        )

    multiplier = granularity_multipliers[granularity]
    return round((kwh / 1000) * multiplier, 6)


# It seems the API can take max itemPerPage 200. We fetch x items per page as this is: x = (# types * 4 quaters * n hours) < 200
# If the itemsPerPage is not a multiple of the types the API sometime skips a type, sometimes duplicates a type!
# The API does not include the last page number in the response, so we need to keep querying until we get an empty response
def call_api(target_datetime: datetime, forecast: bool = False):
    is_last_page = False
    pageNum = 1
    results = []

    itemsPerPage = max(
        [(len(NedType) * 4 * n) for n in range(1, 6) if (len(NedType) * 4 * n) < 200]
    )

    while not is_last_page:
        # API fetches full day of data, so we add 1 day to validfrom[before] to get todays data
        params = {
            "page": pageNum,
            "itemsPerPage": itemsPerPage,
            "point": NedPoint.NETHERLANDS.value,
            "type[]": [
                NedType.WIND.value,
                NedType.SOLAR.value,
                NedType.FOSSILGASPOWER.value,
                NedType.FOSSILHARDCOAL.value,
                NedType.NUCLEAR.value,
                NedType.WASTEPOWER.value,
                NedType.BIOMASSPOWER.value,
                NedType.OTHERPOWER.value,
                NedType.WKKTOTAL.value,
                NedType.WINDOFFSHORE.value,
            ],
            "granularity": NedGranularity.FIFTEEN_MINUTES.value,
            "granularitytimezone": NedGranularityTimezone.UTC.value,
            "classification": NedClassification.FORECAST.value
            if forecast
            else NedClassification.MEASURED.value,
            "activity": NedActivity.PRODUCTION.value,
            "validfrom[before]": (
                target_datetime + timedelta(days=2 if forecast else 1)
            )
            .date()
            .isoformat(),
            "validfrom[after]": (target_datetime - timedelta(days=0 if forecast else 1))
            .date()
            .isoformat(),
        }

        headers = {"X-AUTH-TOKEN": get_token("NED_TOKEN"), "accept": "application/json"}
        response = requests.get(URL, params=params, headers=headers)
        if not response.ok:
            raise ParserException(
                parser="NED.py",
                message=f"Failed to fetch NED data: {response.status_code}, err: {response.text}",
            )
        results += response.json()
        pageNum += 1

        if response.json() == [] or pageNum > 30:
            is_last_page = True

    return results


def _get_entsoe_production_data(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime,
    logger: Logger,
) -> ProductionBreakdownList:
    # Add 2 days as ENTSOE fetches data from three days before target_datetime, where NED.nl fetches for target_datetime and day before
    ENTSOE_raw_data = ENTSOE_query_production(
        ENTSOE_DOMAIN_MAPPINGS[zone_key],
        session,
        target_datetime=(target_datetime + timedelta(days=2)),
    )
    if ENTSOE_raw_data is None:
        raise ParserException(
            parser="NED.py",
            message="Failed to fetch ENTSOE data",
            zone_key=zone_key,
        )
    ENTSOE_parsed_data = ENTSOE_parse_production(
        ENTSOE_raw_data, zoneKey=zone_key, logger=logger
    )

    return ENTSOE_parsed_data


def format_data(
    json: Any, logger: Logger, forecast: bool = False
) -> ProductionBreakdownList:
    df = pd.DataFrame(json)

    # Capture and parse granularity before dropping it (format: "/v1/granularities/4")
    if "granularity" in df.columns and not df.empty:
        granularity_raw = df["granularity"].iloc[0]
        granularity = int(granularity_raw.split("/")[-1])
    else:
        raise ParserException(
            parser="NED.py",
            message="Granularity not found in API response",
        )

    df.drop(
        columns=[
            "id",
            "point",
            "classification",
            "activity",
            "granularity",
            "granularitytimezone",
            "emission",
            "emissionfactor",
            "capacity",
            "validto",
            "lastupdate",
        ],
        inplace=True,
    )

    df = df.groupby(by="validfrom")

    formatted_production_data = ProductionBreakdownList(logger)
    for _group_key, group_df in df:
        # Add lag to avoid using data that is not yet complete and remove "future" data
        if (
            datetime.fromisoformat(group_df["validfrom"].iloc[0])
            > (datetime.now(timezone.utc) - timedelta(hours=0.5))
            and not forecast
        ):
            continue
        data_dict = group_df.to_dict(orient="records")
        mix = ProductionMix()
        for data in data_dict:
            clean_type = int(data["type"].split("/")[-1])
            if clean_type in TYPE_MAPPING:
                mix.add_value(
                    TYPE_MAPPING[clean_type], _kwh_to_mw(data["volume"], granularity)
                )

            else:
                logger.warning(f"Unknown type: {clean_type}")

        formatted_production_data.append(
            zoneKey=ZoneKey("NL"),
            datetime=group_df["validfrom"].iloc[0],
            production=mix,
            source="ned.nl",
            sourceType=EventSourceType.forecasted
            if forecast
            else EventSourceType.measured,
        )

    return formatted_production_data


@refetch_frequency(timedelta(hours=24))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("NL"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()
    target_datetime = target_datetime or datetime.now(timezone.utc)

    json_data = call_api(target_datetime)
    NED_data = format_data(json_data, logger)

    all_dates = [item.get("datetime") for item in NED_data.to_list()]

    if all(
        date >= datetime(2021, 1, 1, tzinfo=timezone.utc)
        for date in all_dates
        if date is not None
    ):
        return NED_data.to_list()

    else:
        ENTSOE_data = _get_entsoe_production_data(
            zone_key, session, target_datetime, logger
        )
        combined_data = ProductionBreakdownList.update_production_breakdowns(
            ENTSOE_data, NED_data, logger, matching_timestamps_only=True
        )
        return combined_data.to_list()


def fetch_production_forecast(
    zone_key: ZoneKey = ZoneKey("NL"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()
    target_datetime = target_datetime or datetime.now(timezone.utc)
    json_data = call_api(target_datetime, forecast=True)
    NED_data = format_data(json_data, logger, forecast=True)

    return NED_data.to_list()
