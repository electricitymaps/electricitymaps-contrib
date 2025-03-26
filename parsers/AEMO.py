import io
import re
import zipfile
from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import TotalConsumptionList
from electricitymap.contrib.lib.models.events import EventSourceType

TIMEZONE = ZoneInfo("?")  # TODO change this
# See at:
"""
from zoneinfo import available_timezones
all_timezones = sorted(available_timezones())
all_timezones[350]
"""

# TODO, what about the other zone in Australia?

ZONE_KEY_TO_REGION = {
    "AU-NSW": "NSW1",
    "AU-QLD": "QLD1",
    "AU-SA": "SA1",
    "AU-TAS": "TAS1",
    "AU-VIC": "VIC1",
    "AU-WA": "WEM",
}


def find_document(session, target_datetime):
    # Fetch the directory listing
    base_url = "http://nemweb.com.au/Reports/CURRENT/Operational_Demand/FORECAST_HH/"
    response = session.get(base_url)

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # String datetime
    target_date_str = target_datetime.strftime("%Y%m%d")

    # Find matching links
    matching_links = soup.find_all(
        "a",
        href=re.compile(
            rf"PUBLIC_FORECAST_OPERATIONAL_DEMAND_HH_{target_date_str}\d+_{target_date_str}\d+\.zip"
        ),
    )

    if matching_links:
        target_link = matching_links[-1]  # Get the last (most recent) link
        full_url = urljoin(base_url, target_link["href"])  # Construct full URL

        file_response = session.get(full_url)

        with zipfile.ZipFile(io.BytesIO(file_response.content)) as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as f:
                df = pd.read_csv(f)
                return df
    else:
        print("No matching files found")


def fetch_consumption_forecast(
    zone_key: str,  # "AU-NSW", "AU-QLD", "AU-SA", "AU-TAS", "AU-VIC", "AU-WA"
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Only for NSW1, QND1, SA1, TAS1, VIC1 zones"""
    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now()  # tz=timezone.utc

    df = find_document(session, target_datetime)

    # Transform dataframe
    df.columns = df.iloc[0]
    df = df.iloc[1:-1].reset_index(drop=True)

    #
    region = ZONE_KEY_TO_REGION.get(zone_key)
    all_consumption_events = df[
        df["REGIONID"] == region
    ]  # all events with a datetime and a consumption value
    consumption_list = TotalConsumptionList(logger)
    for _, event in all_consumption_events.iterrows():
        datetime_object = datetime.strptime(
            event["INTERVAL_DATETIME"], "%Y/%m/%d %H:%M:%S"
        )  # .replace(tzinfo=TX_TZ)
        print(datetime_object)

        consumption_list.append(
            zoneKey=zone_key,
            datetime=datetime_object,
            consumption=float(
                event["OPERATIONAL_DEMAND_POE50"]
            ),  # TODO transform to float
            source="mysource.com",  # TODO change this
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""

    print(fetch_consumption_forecast("AU-VIC"))
