import logging
from datetime import datetime
from typing import Any

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

logger = logging.getLogger(__name__)

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
            f"Failed to fetch capacity data for IESO from url: {file_url} with date {target_datetime.date()}"
        )


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any]:
    last_full_quarter_month = get_last_month_of_last_full_quarter(target_datetime)
    df = get_data_from_url(session, last_full_quarter_month)

    df = df.rename(
        columns={"Fuel Type": "mode", "Total Installed Capacity\n(MW)": "value"}
    )
    df = df[["mode", "value"]]
    df["mode"] = df["mode"].apply(lambda x: MODE_MAPPING.get(x))
    df = df.dropna(subset=["mode"])  # Drop rows where 'mode' is None
    capacity = {}
    for _idx, data in df.iterrows():
        capacity[data["mode"]] = {
            "datetime": last_full_quarter_month.strftime("%Y-%m-%d"),
            "value": round(data["value"], 0),
            "source": "ieso.ca",
        }
    logger.info(
        f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity}"
    )
    return capacity


def get_last_month_of_last_full_quarter(
    target_datetime: datetime,
) -> datetime:
    # Calculate the last month of the last full quarter
    current_quarter = ((target_datetime.month - 1) // 3) + 1
    last_full_quarter = current_quarter - 1 if current_quarter > 1 else 4
    year = target_datetime.year if current_quarter > 1 else target_datetime.year - 1
    quarter_end_month = last_full_quarter * 3
    last_day_of_month = 31 if quarter_end_month in [3, 12] else 30
    return target_datetime.replace(
        year=year, month=quarter_end_month, day=last_day_of_month
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_production_capacity(ZoneKey("CA_ON"), datetime(2025, 3, 1), Session())
