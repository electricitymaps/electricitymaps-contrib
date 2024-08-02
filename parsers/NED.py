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

from .ENTSOE import ENTSOE_DOMAIN_MAPPINGS, WindAndSolarProductionForecastTypes
from .ENTSOE import parse_production as ENTSOE_parse_production
from .ENTSOE import query_production as ENTSOE_query_production
from .ENTSOE import (
    query_wind_solar_production_forecast as ENTSOE_query_wind_solar_production_forecast,
)
from .lib.exceptions import ParserException
from .lib.utils import get_token

URL = "https://api.ned.nl/v1/utilizations"

TYPE_MAPPING = {
    2: "solar",
}


class NedType(Enum):
    SOLAR = 2


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


# kWh to MWh with 3 decimal places
def _kwh_to_mw(kwh):
    return round((kwh / 1000) * 4, 3)


# There seems to be a limitation of 144 items we can get in the response in the API at a time
# So we need to query each mode separately and then combine them
def call_api(target_datetime: datetime, forecast: bool = False):
    params = {
        "itemsPerPage": 192,
        "point": NedPoint.NETHERLANDS.value,
        "type[]": NedType.SOLAR.value,
        "granularity": NedGranularity.FIFTEEN_MINUTES.value,
        "granularitytimezone": NedGranularityTimezone.UTC.value,
        "classification": NedClassification.FORECAST.value
        if forecast
        else NedClassification.MEASURED.value,
        "activity": NedActivity.PRODUCTION.value,
        "validfrom[before]": (target_datetime + timedelta(days=2 if forecast else 1))
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
    return response.json()


def format_data(
    json: Any, logger: Logger, forecast: bool = False
) -> ProductionBreakdownList:
    df = pd.DataFrame(json)
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
        data_dict = group_df.to_dict(orient="records")
        mix = ProductionMix()
        for data in data_dict:
            clean_type = int(data["type"].split("/")[-1])
            if clean_type in TYPE_MAPPING:
                mix.add_value(
                    TYPE_MAPPING[clean_type],
                    _kwh_to_mw(data["volume"]),
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


def _get_entsoe_production_data(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime,
    logger: Logger,
) -> ProductionBreakdownList:
    ENTSOE_raw_data = ENTSOE_query_production(
        ENTSOE_DOMAIN_MAPPINGS[zone_key], session, target_datetime=target_datetime
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


def combine_production_data(entsoe_data, ned_data, logger):
    non_matching_indices = set()
    # Reallocate the unknown production from ENTSOE with solar production from NED
    for idx, entsoe_event in enumerate(entsoe_data.events):
        # O(n^2) but n is small. Change to binary search or dict if too slow
        ned_events = [e for e in ned_data.events if e.datetime == entsoe_event.datetime]

        if len(ned_events) == 0:
            non_matching_indices.add(idx)
            continue

        ned_event = ned_events[0]

        unknown_production = entsoe_event.production.unknown or 0
        solar_production = ned_event.production.solar or 0

        # subtract solar production from unknown production
        new_unknown_production = max(unknown_production - solar_production, 0)

        entsoe_event.production.unknown = new_unknown_production
        entsoe_event.production.solar = solar_production

        entsoe_event.source += "," + ned_event.source

    if len(non_matching_indices) > 0:
        logger.info(
            f"Failed to match {len(non_matching_indices)} ENTSOE events with NED events"
        )
        entsoe_data.events = [
            event
            for idx, event in enumerate(entsoe_data.events)
            if idx not in non_matching_indices
        ]

    return entsoe_data


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
    ENTSOE_data = _get_entsoe_production_data(
        zone_key, session, target_datetime, logger
    )

    combined_data = combine_production_data(ENTSOE_data, NED_data, logger)

    return combined_data.to_list()


def _get_entsoe_forecast_data(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime,
    logger: Logger,
) -> ProductionBreakdownList:
    ENTSOE_raw_data_day_ahead = ENTSOE_query_wind_solar_production_forecast(
        ENTSOE_DOMAIN_MAPPINGS[zone_key],
        session,
        data_type=WindAndSolarProductionForecastTypes.DAY_AHEAD,
        target_datetime=target_datetime,
    )
    ENTSOE_raw_data_intraday = ENTSOE_query_wind_solar_production_forecast(
        ENTSOE_DOMAIN_MAPPINGS[zone_key],
        session,
        data_type=WindAndSolarProductionForecastTypes.INTRADAY,
        target_datetime=target_datetime,
    )
    if ENTSOE_raw_data_day_ahead is None or ENTSOE_raw_data_intraday is None:
        raise ParserException(
            parser="NED.py",
            message="Failed to fetch ENTSOE data",
            zone_key=zone_key,
        )
    ENTSOE_parsed_data_day_ahead = ENTSOE_parse_production(
        ENTSOE_raw_data_day_ahead, zoneKey=zone_key, logger=logger, forecasted=True
    )
    ENTSOE_parsed_data_intraday = ENTSOE_parse_production(
        ENTSOE_raw_data_intraday, zoneKey=zone_key, logger=logger, forecasted=True
    )
    ENTSOE_updated_data = ProductionBreakdownList.update_production_breakdowns(
        production_breakdowns=ENTSOE_parsed_data_day_ahead,
        new_production_breakdowns=ENTSOE_parsed_data_intraday,
        logger=logger,
    )
    return ENTSOE_updated_data


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
    ENTSOE_data = _get_entsoe_forecast_data(zone_key, session, target_datetime, logger)

    combined_data = ProductionBreakdownList.update_production_breakdowns(
        production_breakdowns=ENTSOE_data,
        new_production_breakdowns=NED_data,
        logger=logger,
        matching_timestamps_only=True,
    )

    return combined_data.to_list()
