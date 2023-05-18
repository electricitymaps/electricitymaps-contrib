from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import pandas as pd
from pytz import utc
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException


def getURL(target_datetime: Optional[datetime]) -> str:
    if target_datetime is None:
        target_datetime = datetime.now() - timedelta(days=40)
    day = target_datetime.strftime("%d")
    month = target_datetime.strftime("%m")
    year = target_datetime.strftime("%Y")

    # https://ost.al/wp-content/uploads/2023/03/Publikimi-te-dhenave-16.03.2023.xlsx
    URL = f"https://ost.al/wp-content/uploads/{year}/{month}/Publikimi-te-dhenave-{day}.{month}.{year}.xlsx"
    return URL


def fetch_data(URL, session):
    session = session or Session()
    response: Response = session.get(URL)
    if not response.ok:
        raise ParserException("AL.py", "Got a non okay response from the server.")
    data = pd.read_excel(response.content, sheet_name="Publikime EN")
    return data


@refetch_frequency(timedelta(hours=24))
def fetch_consumption(
    zone_key: str = "AL",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    data = fetch_data(getURL(target_datetime), session)
    consumption_data = data.iloc[381:406].reset_index(drop=True)
    consumption_data = consumption_data.rename(
        columns=consumption_data.iloc[0].to_dict()
    ).drop(consumption_data.index[0])
    # Sum the consumption of all plants in a row excluding the value for hour to get the total consumption and add it to a total column
    consumption_data["Total"] = consumption_data.sum(axis=1) - consumption_data["Hour"]

    date: datetime = data["Albania Transmission System Operator"][0]

    consumption = []

    for row in consumption_data.iterrows():
        consumption.append(
            {
                "zoneKey": "AL",
                "datetime": date.replace(hour=row[1]["Hour"] - 1, tzinfo=utc),
                "consumption": row[1]["Total"],
                "source": "ost.al",
            }
        )
    return consumption


@refetch_frequency(timedelta(hours=24))
def fetch_production_per_unit(
    zone_key: str = "AL",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    data = fetch_data(getURL(target_datetime), session)
    production_data = data.iloc[381:406].reset_index(drop=True)
    production_data = production_data.rename(
        columns=production_data.iloc[0].to_dict()
    ).drop(production_data.index[0])

    date: datetime = data["Albania Transmission System Operator"][0]

    production_per_unit = []

    for column in production_data:
        if column != "Hour":
            plant_data = production_data[["Hour", column]]
            for row in plant_data.iterrows():
                production_per_unit.append(
                    {
                        "datetime": date.replace(hour=row[1]["Hour"] - 1, tzinfo=utc),
                        "production": row[1][str(column)],
                        "productionType": "hydro",
                        "source": "ost.al",
                        # "unitKey": column, # The data is not specific enough to identify the unit by its key.
                        "unitName": column,
                        "zoneKey": "AL",
                    }
                )
    return production_per_unit


if __name__ == "__main__":
    fetch_production_per_unit("AL")
