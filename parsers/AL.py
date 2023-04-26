from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import pandas as pd
from requests import Session, Response
from pytz import utc


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
        raise Exception("Invalid response")
    data = pd.read_excel(response.content, sheet_name="Publikime EN")
    return data


def fetch_production(
    zone_key: str = "AL",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    data = fetch_data(getURL(None), None)
    production_data = data.iloc[381:406].reset_index(drop=True)
    production_data = production_data.rename(
        columns=production_data.iloc[0].to_dict()
    ).drop(production_data.index[0])
    # Sum the production of all plants in a row excluding the value for hour to get the total production and add it to a total column
    production_data["Total"] = production_data.sum(axis=1) - production_data["Hour"]

    date: datetime = data["Albania Transmission System Operator"][0]

    production = []

    for row in production_data.iterrows():
        production.append(
            {
                "zoneKey": "AL",
                "datetime": date.replace(hour=row[1]["Hour"] - 1, tzinfo=utc),
                "production": {
                    "hydro": row[1]["Total"],
                },
                "source": "ost.al",
            }
        )
    return production

def fetch_consumption(
    zone_key: str = "AL",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    data = fetch_data(getURL(None), None)
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


fetch_production()
