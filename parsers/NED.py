from datetime import datetime, timedelta, timezone
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

from .ENTSOE import ENTSOE_DOMAIN_MAPPINGS
from .ENTSOE import parse_production as ENTSOE_parse_production
from .ENTSOE import query_production as ENTSOE_query_production
from .lib.exceptions import ParserException
from .lib.utils import get_token

URL = "https://api.ned.nl/v1/utilizations"

TYPE_MAPPING = {
    2: "solar",
}


# kWh to MWh with 3 decimal places
def kwh_to_mw(kwh):
    return round((kwh / 1000) * 4, 3)


# There seems to be a limitation of 144 items we can get in the response in the API at a time
# So we need to query each mode separately and then combine them
def call_api(target_datetime: datetime, forecast: bool = False):
    params = {
        "point": "0",
        "type[]": "2",
        "granularity": "4",
        "granularitytimezone": "0",
        "classification": "1" if forecast else "2",
        "activity": "1",
        "validfrom[before]": (target_datetime + timedelta(days=1)).date().isoformat(),
        "validfrom[after]": (target_datetime - timedelta(days=1)).date().isoformat(),
    }
    headers = {"X-AUTH-TOKEN": get_token("NED_KEY"), "accept": "application/json"}
    response = requests.get(URL, params=params, headers=headers)
    if not response.ok:
        raise ParserException(
            parser="NED.py",
            message=f"Failed to fetch NED data: {response.status_code}, err: {response.text}",
        )
    return response.json()


def format_data(json: Any, logger: Logger, forecast: bool = False):
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
                    kwh_to_mw(data["volume"]),
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

    combined_data = ProductionBreakdownList.update_production_breakdowns(
        production_breakdowns=ENTSOE_parsed_data,
        new_production_breakdowns=NED_data,
        logger=logger,
        matching_timestamps_only=True,
    )

    return combined_data.to_list()
