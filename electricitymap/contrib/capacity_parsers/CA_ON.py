from datetime import datetime
from logging import getLogger
from typing import Dict, Union

import pandas as pd
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

logger = getLogger(__name__)
MODE_MAPPING = {
    "Nuclear": "nuclear",
    "Hydroelectric": "hydro",
    "Gas/Oil": "gas",
    "Wind": "wind",
    "Biofuel": "biomass",
    "Solar": "solar",
}

BASE_URL = "https://www.ieso.ca"


"""Disclaimer: only valid for real-time data, historical capacity is not available"""

def get_data_from_url(session: Session) -> tuple:
    main_url = f"{BASE_URL}/en/Sector-Participants/Planning-and-Forecasting/Reliability-Outlook"
    url_response: Response = session.get(main_url)

    soup = BeautifulSoup(url_response.text, "html.parser")
    file_name = soup.find_all("a", string="Reliability Outlook - Tables")[0].get("href")
    file_url = f"{BASE_URL}{file_name}"
    file_response: Response = session.get(file_url)
    file_date = file_name.split(".")[0][-7:]
    target_datetime = datetime.strptime(file_date, "%Y%b")
    if file_response.status_code == 200:
        df = pd.read_excel(file_response.url, sheet_name="Table 4.1", header=4, skipfooter=3)
        return df, target_datetime
    else:
        raise ValueError(
            f"Failed to fetch capacity data for IESO from url: {file_url}"
        )


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> Dict:
    df, target_datetime = get_data_from_url(session)
    logger.info(f"Latest capacity data available for IESO: {target_datetime.date()}")
    df = df.rename(
        columns={"Fuel Type": "mode", "Total Installed Capacity\n(MW)": "value"}
    )
    df = df[["mode", "value"]]
    df["mode"] = df["mode"].apply(lambda x: MODE_MAPPING[x])
    capacity = {}
    for idx, data in df.iterrows():
        capacity[data["mode"]] = {
            "datetime": target_datetime.strftime("%Y-%m-%d"),
            "value": round(data["value"], 2),
            "source": "ieso.ca",
        }
    logger.info(
        f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity}"
    )
    return capacity



if __name__ == "__main__":
    fetch_production_capacity("CA_ON", datetime(2023, 1, 1), Session())
