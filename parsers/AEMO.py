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
from electricitymap.contrib.lib.types import ZoneKey

SOURCE = "aemo.com.au"

ZONE_KEY_TO_REGION = {
    "AU-NSW": "NSW1",
    "AU-QLD": "QLD1",
    "AU-SA": "SA1",
    "AU-TAS": "TAS1",
    "AU-VIC": "VIC1",
    "AU-WA": "WEM",  # This zone is not implemented yet
}

ZONE_KEY_TO_TIMEZONE = {
    "AU-NSW": ZoneInfo("Australia/Sydney"),
    "AU-QLD": ZoneInfo("Australia/Brisbane"),
    "AU-SA": ZoneInfo("Australia/Adelaide"),
    "AU-TAS": ZoneInfo("Australia/Hobart"),
    "AU-VIC": ZoneInfo("Australia/Melbourne"),
    "AU-WA": ZoneInfo("Australia/Perth"),  # This zone is not implemented yet
}

# TODO, what about the other zone in Australia (AU-WA)? Check remaining zone


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
    zone_key: ZoneKey,  # "AU-NSW", "AU-QLD", "AU-SA", "AU-TAS", "AU-VIC", "AU-WA"
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Consumption forecast in MW every half an hour for 10 days ahead.
    Only for NSW1, QND1, SA1, TAS1, VIC1 zones."""
    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(tz=ZONE_KEY_TO_TIMEZONE[zone_key])

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
        ).replace(tzinfo=ZONE_KEY_TO_TIMEZONE[zone_key])

        consumption_list.append(
            zoneKey=zone_key,
            datetime=datetime_object,
            consumption=float(
                event["OPERATIONAL_DEMAND_POE50"]
            ),  # 50% probability of exceedance operational demand forecast value
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""

    print(fetch_consumption_forecast("AU-NSW"))
    print(fetch_consumption_forecast("AU-QLD"))
    print(fetch_consumption_forecast("AU-SA"))
    print(fetch_consumption_forecast("AU-TAS"))
    print(fetch_consumption_forecast("AU-VIC"))
    print(
        fetch_consumption_forecast("AU-WA")
    )  # Not implemented yet. It returns an empty list
