from datetime import datetime
from logging import INFO, basicConfig, getLogger
from typing import Any

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

logger = getLogger(__name__)
basicConfig(level=INFO)

MODE_MAPPING = {
    "Nuclear": "nuclear",
    "Hydroelectric": "hydro",
    "Gas/Oil": "gas",
    "Wind": "wind",
    "Biofuel": "biomass",
    "Solar": "solar",
}


"""Disclaimer: only valid for real-time data, historical capacity is not available"""
OUTLOOK_URL = "https://www.ieso.ca/-/media/Files/IESO/Document-Library/planning-forecasts/reliability-outlook/ReliabilityOutlookTables_{date}.ashx"


def get_data_from_url(session: Session, target_datetime: datetime) -> pd.DataFrame:
    file_url = OUTLOOK_URL.format(date=target_datetime.strftime("%Y%b"))
    file_response: Response = session.get(file_url)
    if "Error-404" not in file_response.url and file_response.ok:
        df = pd.read_excel(
            file_response.url, sheet_name="Table 4.1", header=4, skipfooter=3
        )
        return df
    else:
        raise ValueError(
            f"Failed to fetch capacity data for IESO from url: {target_datetime.date()}"
        )


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any]:
    df = get_data_from_url(session, target_datetime)

    df = df.rename(
        columns={"Fuel Type": "mode", "Total Installed Capacity\n(MW)": "value"}
    )
    df = df[["mode", "value"]]
    df["mode"] = df["mode"].apply(lambda x: MODE_MAPPING[x])
    capacity = {}
    for idx, data in df.iterrows():
        capacity[data["mode"]] = {
            "datetime": target_datetime.strftime("%Y-%m-%d"),
            "value": round(data["value"], 0),
            "source": "ieso.ca",
        }
    logger.info(
        f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity}"
    )
    return capacity


if __name__ == "__main__":
    fetch_production_capacity(ZoneKey("CA_ON"), datetime(2023, 3, 1), Session())
