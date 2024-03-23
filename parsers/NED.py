from datetime import datetime
from logging import Logger, getLogger

import pandas as pd
import requests
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionBreakdown, ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

from .lib.utils import get_token

# URL = (
# ) = "https://api.ned.nl/v1/utilizations?point=0&type=2&granularity=3&granularitytimezone=1&classification=2&activity=10&validfrom[strictly_before]=2020-11-17&validfrom[after]=2020-11-16"

#URL = "https://api.ned.nl/v1/utilizations?point=0&type=&type[]=1&type[]=2&type[]=8&type[]=10&type[]=11&type[]=12&type[]=13&type[]=14&type[]=17&type[]=18&type[]=19&type[]=20&type[]=21&type[]=25&type[]=26&granularity=4&granularitytimezone=0&classification=2&activity[]=1&validfrom[before]=2024-03-23&validfrom[after]=2024-03-20"

URL = "https://api.ned.nl/v1/utilizations?point=0&type=&type[]=2&granularity=4&granularitytimezone=0&classification=2&activity[]=1&validfrom[before]=2024-03-23&validfrom[after]=2024-03-22"

TYPE_MAPPING = {
    #1: "wind",
    2: "solar",
    #8: "unknown",
    #17: "wind",
    #22: "wind",
    #20: "nuclear",
    #21: "unknown",
    #25: "biomass",
    #26: "unknown"
}


# kWh to MWh with 3 decimal places
def kwh_to_mw(kwh):
    return round((kwh / 1000) * 4, 3)


# There seems to be a limitation of 144 items we can get in the response in the API at a time
# So we need to query each mode separately and then combine them
def call_api():
    headers = {"X-AUTH-TOKEN": get_token("NED_KEY"), "accept": "application/json"}
    response = requests.get(URL, headers=headers)
    return response.json()


def format_data(logger: Logger):
    df = pd.DataFrame(call_api())
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

        )
    return formatted_production_data


def fetch_production(
    zone_key: ZoneKey = ZoneKey("NED"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    return format_data(logger).to_list()
