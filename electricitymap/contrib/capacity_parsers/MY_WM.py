import json
from datetime import datetime
from logging import INFO, basicConfig, getLogger
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

logger = getLogger(__name__)
basicConfig(level=INFO)

"""Disclaimer: only valid for real-time data, historical capacity is not available"""

MODE_MAPPING = {"Gas": "gas", "Water": "hydro", "Coal": "coal", "Solar": "solar"}
GSO_URL = "https://www.gso.org.my/SystemData/PowerStation.aspx/GetDataSource"

GSO_REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://www.gso.org.my",
    "Referer": "https://www.gso.org.my/SystemData/PowerStation.aspx",
}


def get_capacity_datetime(session: Session) -> datetime:
    r: Response = session.get(GSO_URL)
    soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
    date_str = soup.find_all("b")[0].string
    capacity_datetime = parser.parse(date_str, fuzzy=True)
    return capacity_datetime.replace(day=1)


def fetch_production_capacity(
    zone_key: ZoneKey, session: Session, target_datetime: datetime | None = None
) -> dict[str, Any]:
    if target_datetime is not None:
        raise ValueError("MY-WM capacity parser not enabled for past dates")
    target_datetime = datetime.now()
    capacity_datetime = get_capacity_datetime(session)

    r: Response = session.post(GSO_URL, headers=GSO_REQUEST_HEADERS)
    if not r.ok:
        raise ValueError(
            f"Failed to fetch capacity data for GSO at {target_datetime.strftime('%Y-%m')}"
        )
    else:
        data = pd.DataFrame(json.loads(r.json()["d"]))
        data = data[["Fuel", "Capacity (MW)"]]
        data = data.rename(
            columns={
                "Fuel": "mode",
                "Capacity (MW)": "value",
            }
        )
        data["mode"] = data["mode"].apply(lambda x: x.strip())
        data["mode"] = data["mode"].apply(lambda x: MODE_MAPPING[x])

        filtered_data = data.groupby(["mode"])[["value"]].sum().reset_index()

        capacity_dict = {}
        for idx, data in filtered_data.iterrows():
            capacity_dict[data["mode"]] = {
                "value": round(float(data["value"]), 0),
                "source": "gso.org.my",
                "datetime": capacity_datetime.strftime("%Y-%m-%d"),
            }
        logger.info(
            f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity_dict}"
        )
        return capacity_dict


if __name__ == "__main__":
    fetch_production_capacity(ZoneKey("MY-WM"), Session())
